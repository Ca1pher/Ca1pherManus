# app/langgraph_core/agents/main/supervisor_agent.py

from typing import Dict, Any, List, Optional  # 确保导入 Optional
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.langgraph_core.state.graph_state import AgentState, Plan, SubTask
from app.llms.reasoning_models import supervisor_llm


def supervisor_agent(state: AgentState) -> AgentState:
    print("\n--- Agent: Supervisor ---")
    messages = state["messages"]
    current_request = state.get("current_request")
    overall_plan = state.get("overall_plan")
    last_agent_role = state.get("last_agent_role")

    print(
        f"Supervisor: State on entry - current_request: {current_request}, overall_plan: {overall_plan}, last_agent_role: {last_agent_role}")

    # 场景1: 首次接收用户请求 (入口点)
    if not current_request:
        user_message_content = messages[-1].content if messages else ""
        print(f"Supervisor: Scenario 1 - Initial request. User message: '{user_message_content}'.")
        return {"current_request": user_message_content, "current_agent_role": "planner",
                "last_agent_role": "supervisor"}

    # 场景2: 接收到 Planner 的计划
    elif overall_plan and state.get("current_agent_role") == "supervisor" and last_agent_role == "planner":
        print(f"Supervisor: Scenario 2 - Received plan from Planner.")

        # 增加对 overall_plan 结构的检查
        if not isinstance(overall_plan, dict) or "steps" not in overall_plan or not isinstance(overall_plan["steps"],
                                                                                               list):
            print("Supervisor: Error: overall_plan is not in expected format.")
            return {"messages": [AIMessage(content="Supervisor: Internal error: Plan format invalid.")],
                    "current_agent_role": "end_process", "last_agent_role": "supervisor"}

        if not overall_plan["steps"]:
            response_message = "Supervisor: Planner could not generate a plan or generated an empty one. Please refine your request."
            print(response_message)
            return {"messages": [AIMessage(content=response_message)], "current_agent_role": "end_process",
                    "last_agent_role": "supervisor"}

        next_subtask: Optional[SubTask] = None  # 明确初始化并类型提示
        print(f"Supervisor: Searching for pending subtasks in plan with {len(overall_plan['steps'])} steps.")
        for subtask in overall_plan["steps"]:
            if subtask["status"] == "pending":
                next_subtask = subtask
                break

        if next_subtask:
            print(f"Supervisor: Assigning next subtask '{next_subtask['description']}' to Other Worker.")
            # 问题可能在这里：返回的 current_agent_role 应该是什么？
            # 如果要路由到 other_worker_node，那么 current_agent_role 应该设置为 "other_worker"
            return {"active_subtask_id": next_subtask["id"], "current_agent_role": "other_worker",
                    "last_agent_role": "supervisor", "overall_plan": overall_plan}  # 确保 overall_plan 也被传递
        else:
            # 所有子任务都已完成
            final_report = "Supervisor: All tasks completed. Here is the summary:\n"
            for subtask in overall_plan["steps"]:
                final_report += f"- {subtask['description']}: {subtask['result']}\n"
            print(final_report)
            # 如果所有任务都完成了，并且要结束流程，那么 current_agent_role 应该设置为 "end_process"
            return {"messages": [AIMessage(content=final_report)], "current_agent_role": "end_process",
                    "last_agent_role": "supervisor"}
    else:
        print("Supervisor: Error: Unexpected state.")
        return {"messages": [AIMessage(content="Supervisor: Internal error: Unexpected state.")],
                "current_agent_role": "end_process", "last_agent_role": "supervisor"}

