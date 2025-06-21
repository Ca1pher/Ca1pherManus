# app/langgraph_core/agents/main/supervisor_agent.py

import json
import logging
from typing import Dict, Any, List, Optional  # 确保导入 Optional
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.langgraph_core.state.graph_state import AgentState, Plan, SubTask
from app.llms.reasoning_models import supervisor_llm
from app.langgraph_core.prompts.utils import load_prompt_template

# 加载新的评估 Prompt
plan_evaluation_prompt = load_prompt_template("supervisor/plan_evaluation.md")

# 获取logger实例，使用 __name__ 可以自动根据模块路径命名 logger
logger = logging.getLogger(__name__)


def supervisor_agent(state: AgentState) -> AgentState:
    logger.info("--- Agent: Supervisor ---")
    messages = state["messages"]
    current_request = state.get("current_request")
    overall_plan = state.get("overall_plan")
    last_agent_role = state.get("last_agent_role")

    logger.info(f"Supervisor state on entry: last_agent_role='{last_agent_role}', current_request exists: {bool(current_request)}, plan exists: {bool(overall_plan)}")

    # 场景1: 首次接收用户请求 (入口点)
    if not current_request:
        user_message_content = messages[-1].content if messages else ""
        logger.info(f"Scenario 1: Initial request received. User message: '{user_message_content}'.")
        return {"current_request": user_message_content, "current_agent_role": "planner",
                "last_agent_role": "supervisor"}

    # 场景2: 接收到 Planner 的计划
    elif overall_plan and state.get("current_agent_role") == "supervisor" and last_agent_role == "planner":
        logger.info("Scenario 2: Received plan from Planner. Evaluating plan...")

        # --- 新增：调用 LLM 评估计划 ---
        prompt_str = plan_evaluation_prompt.format(
            user_request=current_request,
            plan=json.dumps(overall_plan, indent=2, ensure_ascii=False)
        )
        logger.info("Formatted evaluation prompt. Preparing to call LLM...")
        
        # 将格式化后的字符串包装在 ChatPromptTemplate 中，或者直接作为字符串传递
        # 直接传递字符串更简单
        llm_response = supervisor_llm.invoke(prompt_str, response_format={"type": "json_object"})
        
        try:
            evaluation = json.loads(llm_response.content)
            logger.info(f"Plan evaluation result: {evaluation}")

            if not evaluation.get("is_approved", False):
                feedback = evaluation.get("feedback", "The plan was rejected without specific feedback.")
                logger.warning(f"Plan rejected. Feedback: {feedback}")
                # 计划被否决，将反馈信息放入消息列表，让planer重新生成计划
                return {
                    "messages": [AIMessage(content=f"Supervisor Feedback: {feedback}")],
                    "current_agent_role": "planner",
                    "last_agent_role": "supervisor"
                }

            logger.info("Plan approved. Proceeding to execution.")
            # 如果计划被批准，继续原有的逻辑
        except json.JSONDecodeError as e:
            error_message = f"Failed to decode LLM evaluation. Error: {e}. Raw content: '{llm_response.content}'"
            logger.error(error_message)
            return {
                "messages": [AIMessage(content=f"Supervisor: {error_message}")],
                "current_agent_role": "end_process",
                "last_agent_role": "supervisor"
            }
        # --- 评估结束 ---

        # 增加对 overall_plan 结构的检查
        if not isinstance(overall_plan, dict) or "steps" not in overall_plan or not isinstance(overall_plan["steps"],
                                                                                               list):
            logger.error("Error: overall_plan is not in expected format.")
            return {"messages": [AIMessage(content="Supervisor: Internal error: Plan format invalid.")],
                    "current_agent_role": "end_process", "last_agent_role": "supervisor"}

        if not overall_plan["steps"]:
            response_message = "Planner could not generate a plan or generated an empty one. Please refine your request."
            logger.warning(response_message)
            return {"messages": [AIMessage(content=f"Supervisor: {response_message}")], "current_agent_role": "end_process",
                    "last_agent_role": "supervisor"}

        active_subtask: Optional[SubTask] = None  # 明确初始化并类型提示
        next_subtask: Optional[SubTask] = None  # 明确初始化并类型提示
        # 当前激活的子任务并检查结果是否与子任务提问匹配
        logger.info(f"Searching for active and next subtasks in plan with {len(overall_plan['steps'])} steps.")
        for subtask in overall_plan["steps"]:
            if subtask["status"] == "active":
                active_subtask = subtask
            if subtask["status"] == "pending":
                next_subtask = subtask
                break

        if active_subtask:
            logger.info(f"Active subtask '{active_subtask['description']}' found.")
            # 拿任务历史，当前任务和本次任务结果，评估结果是否采纳并记录原因

        if next_subtask:
            logger.info(f"Assigning next subtask '{next_subtask['description']}' to Other Worker.")
            # 问题可能在这里：返回的 current_agent_role 应该是什么？
            # 如果要路由到 other_worker_node，那么 current_agent_role 应该设置为 "other_worker"
            return {"active_subtask_id": next_subtask["id"], "current_agent_role": "other_worker",
                    "last_agent_role": "supervisor", "overall_plan": overall_plan}  # 确保 overall_plan 也被传递
        else:
            # 所有子任务都已完成
            final_report = "All tasks completed. Here is the summary:\n"
            for subtask in overall_plan["steps"]:
                final_report += f"- {subtask['description']}: {subtask['result']}\n"
            logger.info(final_report)
            # 如果所有任务都完成了，并且要结束流程，那么 current_agent_role 应该设置为 "end_process"
            return {"messages": [AIMessage(content=f"Supervisor: {final_report}")], "current_agent_role": "end_process",
                    "last_agent_role": "supervisor"}
    # 场景3: 接收到非planner的结果
    else:
        logger.info("Scenario 3: Received result from Others.")
        # 增加对 overall_plan 结构的检查
        if not isinstance(overall_plan, dict) or "steps" not in overall_plan or not isinstance(overall_plan["steps"],
                                                                                               list):
            logger.error("Error: overall_plan is not in expected format.")
            return {"messages": [AIMessage(content="Supervisor: Internal error: Plan format invalid.")],
                    "current_agent_role": "end_process", "last_agent_role": "supervisor"}

        if not overall_plan["steps"]:
            response_message = "Planner could not generate a plan or generated an empty one. Please refine your request."
            logger.warning(response_message)
            return {"messages": [AIMessage(content=f"Supervisor: {response_message}")], "current_agent_role": "end_process",
                    "last_agent_role": "supervisor"}

        next_subtask: Optional[SubTask] = None  # 明确初始化并类型提示
        logger.info(f"Searching for pending subtasks in plan with {len(overall_plan['steps'])} steps.")
        for subtask in overall_plan["steps"]:
            if subtask["status"] == "pending":
                next_subtask = subtask
                break

        if next_subtask:
            logger.info(f"Assigning next subtask '{next_subtask['description']}' to Other Worker.")
            # 问题可能在这里：返回的 current_agent_role 应该是什么？
            # 如果要路由到 other_worker_node，那么 current_agent_role 应该设置为 "other_worker"
            return {"active_subtask_id": next_subtask["id"], "current_agent_role": "other_worker",
                    "last_agent_role": "supervisor", "overall_plan": overall_plan}  # 确保 overall_plan 也被传递
        else:
            # 所有子任务都已完成
            final_report = "All tasks completed. Here is the summary:\n"
            for subtask in overall_plan["steps"]:
                final_report += f"- {subtask['description']}: {subtask['result']}\n"
            logger.info(final_report)
            # 如果所有任务都完成了，并且要结束流程，那么 current_agent_role 应该设置为 "end_process"
            return {"messages": [AIMessage(content=f"Supervisor: {final_report}")], "current_agent_role": "end_process",
                    "last_agent_role": "supervisor"}


