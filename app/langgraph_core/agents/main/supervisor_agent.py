# app/langgraph_core/agents/main/supervisor_agent.py

import json
import logging
from typing import Dict, Any, List, Optional
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

from app.langgraph_core.state.graph_state import AgentState, Plan, SubTask
from app.llms.reasoning_models import supervisor_llm
from app.langgraph_core.prompts.utils import load_prompt_template
from app.langgraph_core.agents.config_loader import WORKERS_CONFIG

# --- 加载所有需要的 Supervisor Prompts ---
plan_evaluation_prompt = load_prompt_template("supervisor/plan_evaluation.md")
result_evaluation_prompt = load_prompt_template("supervisor/result_evaluation.md")
final_summary_prompt = load_prompt_template("supervisor/final_summary.md")

# --- 在文件顶部定义最大重试次数配置 ---
MAX_PLAN_REVISIONS = 2
MAX_TASK_REVISIONS = 1

logger = logging.getLogger(__name__)


def _find_subtask_by_id(plan: Dict[str, Any], task_id: str) -> Optional[Dict[str, Any]]:
    """Helper function to find a subtask dictionary by its ID in the plan."""
    for task in plan.get("steps", []):
        if task.get("id") == task_id:
            return task
    return None

def _validate_and_correct_plan(plan: Plan) -> (Plan, bool):
    """
    校验并修正计划的合法性。
    1. 检查每个步骤是否有 'assigned_to' 字段，如果没有则分配给兜底工人。
    2. 检查 'assigned_to' 的值是否是已知的工人，如果不是则分配给兜底工人。
    返回修正后的计划和一个布尔值，表示计划是否被修正过。
    """
    was_corrected = False
    available_worker_names = {worker['name'] for worker in WORKERS_CONFIG.get('workers', [])}
    if not available_worker_names:
        logger.error("致命错误：系统中没有配置任何工人 (Workers)。")
        return plan, True # 返回未修改的计划，并标记为已"修正"以阻止流程

    steps = plan.get("steps", [])
    if not steps:
        # 这是一个无效计划，但我们让上游的 LLM 评估来处理它
        return plan, False

    for i, task in enumerate(steps):
        assignee = task.get("assigned_to")
        if not assignee:
            logger.warning(f"计划修正：第 {i+1} 步任务 '{task.get('description')}' 没有指定执行人。自动分配给 other_worker。")
            task["assigned_to"] = "other_worker"
            was_corrected = True
        elif assignee not in available_worker_names:
            logger.warning(f"计划修正：第 {i+1} 步任务指定了不存在的工人 '{assignee}'。自动重新分配给 other_worker。")
            task["assigned_to"] = "other_worker"
            was_corrected = True
    
    return plan, was_corrected

def supervisor_agent(state: AgentState) -> dict:
    logger.info("--- Agent: Supervisor ---")
    
    current_request = state.get("current_request")
    overall_plan = state.get("overall_plan")
    last_agent_role = state.get("last_agent_role")

    logger.info(f"Supervisor state: last_role='{last_agent_role}', plan_exists={bool(overall_plan and overall_plan.get('steps'))}, active_task_id='{state.get('active_subtask_id')}'")

    # 场景1: 首次请求，路由给 Planner
    if not current_request:
        logger.info("Scenario 1: Initial request. Routing to Planner.")
        return {
            "current_request": state["messages"][-1].content,
            "current_agent_role": "planner",
            "last_agent_role": "supervisor"
        }

    # 场景2: 从 Planner 处收到计划，进行评估
    if last_agent_role == "planner":
        logger.info("Scenario 2: Received plan from Planner. Evaluating...")

        # --- 修改：进行结构合法性校验和自动修正 ---
        corrected_plan, was_corrected = _validate_and_correct_plan(overall_plan)
        if was_corrected:
            logger.info("Plan has been auto-corrected by the supervisor.")
            # 更新状态中的计划
            state["overall_plan"] = corrected_plan
        
        # 即使修正了，也继续进行 LLM 评估，因为计划的逻辑可能仍然有问题
        prompt = plan_evaluation_prompt.format(
            user_request=current_request,
            plan=json.dumps(corrected_plan, indent=2, ensure_ascii=False) # 使用修正后的计划进行评估
        )
        llm_response = supervisor_llm.invoke(prompt, response_format={"type": "json_object"})
        
        try:
            raw_content = llm_response.content
            json_start_index = raw_content.find('{')
            json_end_index = raw_content.rfind('}') + 1
            json_str = raw_content[json_start_index:json_end_index]
            evaluation = json.loads(json_str)
            logger.info(f"Plan evaluation result: {evaluation}")

            if not evaluation.get("is_approved", False):
                # --- 新增：计划重试计数和检查 ---
                current_revisions = state.get("plan_revision_count", 0) + 1
                logger.warning(f"Plan rejected. Revision count: {current_revisions}/{MAX_PLAN_REVISIONS}.")

                if current_revisions > MAX_PLAN_REVISIONS:
                    logger.error("Maximum plan revisions reached. Forcibly approving the last plan to proceed.")
                    # 强制接受，让流程继续，而不是终止
                    state["plan_revision_count"] = 0 # 重置计数器
                    # 此处不返回，让代码继续向下执行到任务分配逻辑
                else:
                    return {
                        "messages": [AIMessage(content=evaluation.get("feedback", "No feedback provided."))],
                        "plan_revision_count": current_revisions, # 更新计数
                        "current_agent_role": "planner",
                        "last_agent_role": "supervisor"
                    }
            
            logger.info("Plan approved. Resetting plan revision count and proceeding to execution.")
            state["plan_revision_count"] = 0
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse plan evaluation: {e}. Raw content: '{llm_response.content}'")
            return {"current_agent_role": "end_process", "last_agent_role": "supervisor"}

    # 场景3: 从 Worker 处收到结果，或从 Planner 处收到批准的计划后，决定下一步
    if last_agent_role == "other_worker":
        logger.info(f"Scenario 3: Received result from Worker for task '{state.get('active_subtask_id')}'. Evaluating result...")
        active_task = _find_subtask_by_id(overall_plan, state.get('active_subtask_id'))
        if not active_task:
             logger.error(f"Logic error: Could not find active task with ID '{state.get('active_subtask_id')}'")
             return {"current_agent_role": "end_process"}

        prompt = result_evaluation_prompt.format(
            user_request=current_request,
            subtask_description=active_task["description"],
            worker_result=state.get("last_worker_result", "")
        )
        llm_response = supervisor_llm.invoke(prompt, response_format={"type": "json_object"})
        
        try:
            raw_content = llm_response.content
            json_start_index = raw_content.find('{')
            json_end_index = raw_content.rfind('}') + 1
            json_str = raw_content[json_start_index:json_end_index]
            evaluation = json.loads(json_str)
            logger.info(f"Result evaluation: {evaluation}")

            if not evaluation.get("is_satisfactory", False):
                current_revisions = state.get("task_revision_count", 0) + 1
                logger.warning(f"Result for task '{active_task['id']}' not satisfactory. Revision count: {current_revisions}/{MAX_TASK_REVISIONS}.")

                if current_revisions > MAX_TASK_REVISIONS:
                    logger.error(f"Maximum revisions for task '{active_task['id']}' reached. Forcibly accepting the last result.")
                    # 强制接受，标记任务为完成，然后继续
                    state["task_revision_count"] = 0 # 重置计数器
                    active_task["status"] = "completed"
                    active_task["result"] = state.get("last_worker_result", "Result forcibly accepted after max revisions.")
                    # 此处不返回，让代码继续向下执行到下一个任务分配逻辑
                else:
                    return {
                        "messages": [AIMessage(content=evaluation.get("feedback", "Result was not satisfactory."))],
                        "task_revision_count": current_revisions, # 更新计数
                        "current_agent_role": "other_worker",
                        "last_agent_role": "supervisor"
                    }

            logger.info(f"Result for task '{active_task['id']}' is satisfactory. Resetting task revision count and marking as completed.")
            state["task_revision_count"] = 0
            active_task["status"] = "completed"
            active_task["result"] = state.get("last_worker_result")

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse result evaluation: {e}. Raw content: '{llm_response.content}'")
            return {"current_agent_role": "end_process", "last_agent_role": "supervisor"}

    # --- 任务分配逻辑 (场景2批准后和场景3完成后都会进入这里) ---
    logger.info("Entering task assignment logic...")
    next_pending_task = None
    for task in overall_plan.get("steps", []):
        if task.get("status") is None or task.get("status") == "pending":
            next_pending_task = task
            break

    if next_pending_task:
        assignee = next_pending_task.get("assigned_to")
        logger.info(f"Found next pending task: '{next_pending_task['description']}'. Activating and assigning to '{assignee}'.")
        # --- 新增：分配新任务前，确保任务计数器已清零 ---
        state["task_revision_count"] = 0 
        next_pending_task["status"] = "active"
        return {
            "overall_plan": overall_plan,
            "active_subtask_id": next_pending_task["id"],
            "task_revision_count": 0, # 显式返回清零后的状态
            "current_agent_role": assignee, # <-- 关键修改：路由到具体的工人
            "last_agent_role": "supervisor"
        }
    else:
        # --- 2. 重写最终报告生成逻辑 ---
        logger.info("All tasks are completed. Invoking LLM for final summary.")
        
        try:
            # 准备上下文
            plan_and_results_json = json.dumps(overall_plan, indent=2, ensure_ascii=False)
            
            # 格式化 Prompt
            summary_prompt_str = final_summary_prompt.format(
                user_request=current_request,
                plan_and_results=plan_and_results_json
            )
            
            # 调用 LLM 生成最终报告
            final_response = supervisor_llm.invoke(summary_prompt_str)
            final_report = final_response.content
            
            logger.info(f"Generated final report: {final_report}")

            return {
                "messages": [AIMessage(content=final_report)],
                "current_agent_role": "end_process",
                "last_agent_role": "supervisor"
            }
        except Exception as e:
            logger.error(f"Failed to generate final summary: {e}", exc_info=True)
            # 发生错误时，返回一个标准的错误信息
            return {
                "messages": [AIMessage(content=f"An error occurred while generating the final report: {e}")],
                "current_agent_role": "end_process",
                "last_agent_role": "supervisor"
            }


