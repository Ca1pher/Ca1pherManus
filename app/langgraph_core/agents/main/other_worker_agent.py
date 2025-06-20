# app/langgraph_core/agents/main/other_worker_agent.py

from typing import Dict, Any
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.langgraph_core.state.graph_state import AgentState, SubTask, Plan
from app.llms.reasoning_models import other_worker_llm # 导入为 Other Worker 准备的 LLM
from app.langgraph_core.prompts.utils import load_chat_prompt_template

# 加载 Other Worker 的提示词模板
worker_prompt_template = load_chat_prompt_template(
    agent_name="worker", # 对应 prompts/worker 目录
    human_template_name="task_execution", # 对应 prompts/worker/task_execution.md
    system_template_name="system_prompt" # 对应 prompts/worker/system_prompt.md
    # 暂时不使用 few_shot_examples
)

def other_worker_agent(state: AgentState) -> AgentState:
    print("\n--- Agent: Other Worker ---")
    active_subtask_id = state.get("active_subtask_id")
    overall_plan = state.get("overall_plan")

    if not active_subtask_id or not overall_plan:
        print("Other Worker: No active subtask or plan found.")
        return {"messages": [AIMessage(content="Other Worker: Error - No active subtask or plan.")], "current_agent_role": "supervisor", "last_agent_role": "other_worker", "last_worker_result": "Error: No subtask."}

    # 找到当前活跃的子任务
    current_subtask: Optional[SubTask] = None
    for subtask in overall_plan["steps"]:
        if subtask["id"] == active_subtask_id:
            current_subtask = subtask
            break

    if not current_subtask:
        print(f"Other Worker: Subtask with ID '{active_subtask_id}' not found in plan.")
        return {"messages": [AIMessage(content=f"Other Worker: Error - Subtask '{active_subtask_id}' not found.")], "current_agent_role": "supervisor", "last_agent_role": "other_worker", "last_worker_result": f"Error: Subtask '{active_subtask_id}' not found."}

    print(f"Other Worker: Executing subtask: '{current_subtask['description']}'")

    # 构建 chain
    chain = worker_prompt_template | other_worker_llm

    # 调用 LLM 来模拟执行任务并生成结果
    response = chain.invoke({
        "task_description": current_subtask["description"],
        "messages": state["messages"] # 传递消息历史作为上下文
    })

    worker_result = response.content
    print(f"Other Worker: Subtask result: '{worker_result}'")

    # 返回更新后的状态，将结果传递给 Supervisor
    return {
        "current_agent_role": "supervisor", # 任务完成后，将控制权交回给 Supervisor
        "last_agent_role": "other_worker",
        "last_worker_result": worker_result # 将任务结果存储起来
    }

