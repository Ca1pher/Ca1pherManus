# app/langgraph_core/agents/main/supervisor_agent.py

import json
import logging
from typing import Dict, Any, List, Optional
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

from app.langgraph_core.state.graph_state import AgentState, Plan, SubTask
from app.llms.reasoning_models import supervisor_llm
from app.langgraph_core.prompts.utils import load_prompt_template

# --- 加载所有需要的 Supervisor Prompts ---
plan_evaluation_prompt = load_prompt_template("supervisor/plan_evaluation.md")
result_evaluation_prompt = load_prompt_template("supervisor/result_evaluation.md")

logger = logging.getLogger(__name__)


def _find_subtask_by_id(plan: Dict[str, Any], task_id: str) -> Optional[Dict[str, Any]]:
    """Helper function to find a subtask dictionary by its ID in the plan."""
    for task in plan.get("steps", []):
        if task.get("id") == task_id:
            return task
    return None

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
        prompt = plan_evaluation_prompt.format(
            user_request=current_request,
            plan=json.dumps(overall_plan, indent=2, ensure_ascii=False)
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
                logger.warning("Plan rejected. Sending back to Planner with feedback.")
                return {
                    "messages": [AIMessage(content=evaluation.get("feedback", "No feedback provided."))],
                    "current_agent_role": "planner",
                    "last_agent_role": "supervisor"
                }
            
            logger.info("Plan approved. Finding next task to execute.")
            # 计划批准后，直接进入分配任务的逻辑（复用场景3的部分逻辑）
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse plan evaluation: {e}. Raw content: '{llm_response.content}'")
            return {"current_agent_role": "end_process", "last_agent_role": "supervisor"}

    # 场景3: 从 Worker 处收到结果，或从 Planner 处收到批准的计划后，决定下一步
    if last_agent_role == "other_worker":
        logger.info(f"Scenario 3: Received result from Worker for task '{state.get('active_subtask_id')}'. Evaluating result...")
        active_task = _find_subtask_by_id(overall_plan, state.get("active_subtask_id"))
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
                logger.warning(f"Result for task '{active_task['id']}' is not satisfactory. Re-assigning to worker with feedback.")
                return {
                    "messages": [AIMessage(content=evaluation.get("feedback", "Result was not satisfactory."))],
                    "current_agent_role": "other_worker", # 再次分配给工人
                    "last_agent_role": "supervisor"
                    # active_subtask_id 和 overall_plan 保持不变
                }

            logger.info(f"Result for task '{active_task['id']}' is satisfactory. Marking as completed.")
            active_task["status"] = "completed"
            active_task["result"] = state.get("last_worker_result")

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse result evaluation: {e}. Raw content: '{llm_response.content}'")
            return {"current_agent_role": "end_process", "last_agent_role": "supervisor"}

    # --- 任务分配逻辑 (场景2批准后和场景3完成后都会进入这里) ---
    logger.info("Entering task assignment logic...")
    next_pending_task = None
    for task in overall_plan.get("steps", []):
        if task.get("status") == "pending":
            next_pending_task = task
            break

    if next_pending_task:
        logger.info(f"Found next pending task: '{next_pending_task['description']}'. Activating and assigning to Worker.")
        next_pending_task["status"] = "active"
        return {
            "overall_plan": overall_plan,
            "active_subtask_id": next_pending_task["id"],
            "current_agent_role": "other_worker",
            "last_agent_role": "supervisor"
        }
    else:
        logger.info("All tasks are completed. Finalizing process.")
        final_report = "All tasks completed. Here is the summary:\n"
        for task in overall_plan.get("steps", []):
            final_report += f"- {task.get('description')}: {task.get('result')}\n"
        return {
            "messages": [AIMessage(content=final_report)],
            "current_agent_role": "end_process",
            "last_agent_role": "supervisor"
        }


