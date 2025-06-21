# app/langgraph_core/agents/main/planner_agent.py

import json
import logging
from app.langgraph_core.prompts.utils import load_chat_prompt_template, load_prompt_template
from app.llms.reasoning_models import planner_llm
from app.langgraph_core.state.graph_state import AgentState, Plan, SubTask
from langchain_core.messages import AIMessage
from typing import List

# 获取logger实例
logger = logging.getLogger(__name__)

# --- 加载所有需要的 Prompt ---
try:
    # 场景1: 首次生成计划的模板
    plan_generation_prompt = load_chat_prompt_template(
        agent_name="planner",
        human_template_name="plan_generation",
        system_template_name="system_prompt",
        examples_name="few_shot_examples"
    )
    # 场景2: 根据反馈修正计划的模板
    plan_revision_prompt = load_prompt_template("planner/plan_revision.md")
    logger.info("Planner prompts loaded successfully.")
except Exception as e:
    logger.critical(f"Failed to load planner prompts: {e}", exc_info=True)
    raise

def planner_agent(state: AgentState) -> AgentState:
    logger.info("--- Agent: Planner ---")
    
    current_request = state["current_request"]
    overall_plan = state.get("overall_plan")
    messages = state.get("messages", [])
    
    prompt_to_use = None
    llm_input = {}

    # 判断是"首次规划"还是"修正规划"
    # 我们通过检查是否有主管的反馈来判断。一个简单的标志是 messages 列表的最后一个消息是否来自AI（主管）。
    is_revision = overall_plan and messages and isinstance(messages[-1], AIMessage)

    if is_revision:
        logger.info("Scenario: Revising plan based on feedback.")
        prompt_to_use = plan_revision_prompt
        feedback = messages[-1].content
        
        llm_input = {
            "user_request": current_request,
            "original_plan": json.dumps(overall_plan, indent=2, ensure_ascii=False),
            "supervisor_feedback": feedback
        }
    else:
        logger.info("Scenario: Generating initial plan.")
        prompt_to_use = plan_generation_prompt
        llm_input = {
            "input": current_request,
            "messages": messages
        }

    try:
        # 使用选择好的 prompt 和 input 调用 LLM
        chain = prompt_to_use | planner_llm
        response = chain.invoke(llm_input)
        
        logger.info(f"LLM response content (first 200 chars): {response.content[:200]}...")

        # --- 解析 LLM 响应 ---
        # 这里的解析逻辑需要足够健壮以处理不同场景的输出
        # 首先尝试直接解析JSON
        try:
            raw_content = response.content
            json_start = raw_content.find('{')
            json_end = raw_content.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = raw_content[json_start:json_end]
                plan_data = json.loads(json_str)
                generated_subtasks = plan_data.get("steps", [])
            else:
                raise json.JSONDecodeError("No JSON object found", raw_content, 0)
        except json.JSONDecodeError:
            # 如果直接解析JSON失败，退回到基于文本分割的旧方法
            logger.warning("Failed to parse LLM response as JSON, falling back to text splitting.")
            plan_steps_raw = response.content.split('\n')
            subtasks_data = []
            for i, step_desc in enumerate(plan_steps_raw):
                step_desc = step_desc.strip()
                if step_desc:
                    if step_desc.startswith(f"{i + 1}. ") or step_desc.startswith(f"{i + 1}.") :
                        step_desc = step_desc.split('.', 1)[1].strip()
                    elif step_desc.startswith("- "):
                        step_desc = step_desc[2:]
                    
                    subtasks_data.append({"id": f"task_{i + 1}", "description": step_desc, "status": "pending"})
            generated_subtasks = subtasks_data

        generated_plan: Plan = {"steps": [SubTask(**task) for task in generated_subtasks]}
        logger.info(f"Generated plan: {generated_plan}")

        return {"overall_plan": generated_plan, "current_agent_role": "supervisor", "last_agent_role": "planner"}

    except Exception as e:
        logger.error(f"Error during LLM invocation or plan parsing: {e}", exc_info=True)
        return {
            "messages": [AIMessage(content=f"Planner: Failed to generate plan due to an internal error: {e}")],
            "current_agent_role": "supervisor",
            "last_agent_role": "planner",
            "overall_plan": {"steps": []}
        }
