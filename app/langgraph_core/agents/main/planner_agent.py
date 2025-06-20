# app/langgraph_core/agents/main/planner_agent.py

import sys  # 导入 sys 模块用于错误输出

print("DEBUG: planner_agent.py module loading started.")

from app.langgraph_core.prompts.utils import load_chat_prompt_template
from app.llms.reasoning_models import planner_llm
from app.langgraph_core.state.graph_state import AgentState, Plan, SubTask
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import MessagesPlaceholder
from typing import List

print("DEBUG: planner_agent.py: All dependencies imported.")

try:
    # 加载 Planner 的提示词模板
    planner_prompt_template = load_chat_prompt_template(
        agent_name="planner",
        human_template_name="plan_generation",
        system_template_name="system_prompt",
        examples_name="few_shot_examples"
    )
    print("DEBUG: planner_agent.py: planner_prompt_template created successfully.")
except Exception as e:
    print(
        f"ERROR: planner_agent.py: Failed to load planner prompt template during module import: {type(e).__name__}: {e}",
        file=sys.stderr)
    # 重新抛出异常，确保错误被 Uvicorn 捕获并显示
    raise


def planner_agent(state: AgentState) -> AgentState:
    print("\n--- Agent: Planner ---")
    current_task = state["current_request"]
    print(f"Planner: Current task received: '{current_task}'")

    # 构建 chain
    chain = planner_prompt_template | planner_llm

    try:
        # 调用 LLM 生成计划
        response = chain.invoke({
            "input": current_task,
            "messages": state["messages"]
        })
        print(f"Planner: LLM response content (first 200 chars): {response.content[:200]}...")

        # --- 解析 LLM 响应，创建 generated_plan ---
        plan_steps_raw = response.content.split('\n')
        generated_subtasks: List[SubTask] = []
        for i, step_desc in enumerate(plan_steps_raw):
            step_desc = step_desc.strip()
            if step_desc:
                if step_desc.startswith(f"{i + 1}. "):
                    step_desc = step_desc[len(f"{i + 1}. "):]
                elif step_desc.startswith("- "):
                    step_desc = step_desc[2:]

                generated_subtasks.append(SubTask(
                    id=f"task_{i + 1}",
                    description=step_desc,
                    status="pending",
                    assigned_to=None,
                    result=None
                ))

        generated_plan: Plan = {"steps": generated_subtasks}
        print(f"Planner: Generated plan: {generated_plan}")

        return {"overall_plan": generated_plan, "current_agent_role": "supervisor", "last_agent_role": "planner"}

    except Exception as e:
        print(f"ERROR: Planner: Error during LLM invocation or plan parsing: {type(e).__name__}: {e}", file=sys.stderr)
        return {
            "messages": [AIMessage(
                content=f"Planner: Failed to generate plan due to an internal error: {type(e).__name__}: {e}")],
            "current_agent_role": "supervisor",
            "last_agent_role": "planner",
            "overall_plan": {"steps": []}
        }


print("DEBUG: planner_agent.py module loading finished.")
