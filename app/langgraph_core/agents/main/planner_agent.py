# app/langgraph_core/agents/main/planner_agent.py

import json
import logging
from app.langgraph_core.prompts.utils import load_prompt_template
from app.llms.reasoning_models import planner_llm
from app.langgraph_core.state.graph_state import AgentState, Plan, SubTask
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from typing import List

# 导入工人配置
from app.langgraph_core.agents.config_loader import WORKERS_CONFIG

# 获取logger实例
logger = logging.getLogger(__name__)

# --- 加载所有需要的 Prompt 模板 ---
try:
    # 场景1: 首次生成计划的系统模板
    system_prompt_template = load_prompt_template("planner/system_prompt.md")
    # 场景2: 根据反馈修正计划的模板
    plan_revision_prompt = load_prompt_template("planner/plan_revision.md")
    # 加载 Few-shot 示例
    with open('app/langgraph_core/prompts/planner/few_shot_examples.json', 'r', encoding='utf-8') as f:
        few_shot_examples = json.load(f)
    logger.info("Planner prompts and examples loaded successfully.")
except Exception as e:
    logger.critical(f"Failed to load planner prompts or examples: {e}", exc_info=True)
    raise

def generate_worker_descriptions() -> str:
    """根据配置文件生成工人描述字符串"""
    descriptions = []
    for worker in WORKERS_CONFIG.get("workers", []):
        # 使用 .get() 安全地访问 'description'，并提供默认值
        worker_desc = worker.get("description", "一个通用的工人，负责处理未分配或常规的任务。")
        description = f"- **{worker['name']}**: {worker_desc}"
        descriptions.append(description)
    return "\n".join(descriptions)

def planner_agent(state: AgentState) -> AgentState:
    logger.info("--- Agent: Planner ---")
    
    current_request = state["current_request"]
    overall_plan = state.get("overall_plan")
    messages = state.get("messages", [])
    
    prompt_to_use = None
    llm_input = {}
    
    # 动态生成当前可用的工人描述
    available_workers_desc = generate_worker_descriptions()
    
    # --- 根据场景选择和构建 Prompt ---
    is_revision = overall_plan and messages and isinstance(messages[-1], AIMessage)

    if is_revision:
        logger.info("Scenario: Revising plan based on feedback.")
        prompt_to_use = plan_revision_prompt
        feedback = messages[-1].content
        
        llm_input = {
            "user_request": current_request,
            "original_plan": json.dumps(overall_plan, indent=2, ensure_ascii=False),
            "supervisor_feedback": feedback,
            "available_workers": available_workers_desc
        }
    else:
        logger.info("Scenario: Generating initial plan.")
        # 从加载的模板动态构建系统 Prompt
        final_system_prompt = system_prompt_template.format(available_workers=available_workers_desc)
        
        # 构建包含 few-shot 示例的完整提示
        few_shot_text = ""
        for example in few_shot_examples:
            few_shot_text += f"\n用户请求: {example['input']}\n"
            # 直接使用字符串拼接，避免 JSON 格式化问题
            steps_text = ""
            for step in example['output']['steps']:
                steps_text += f"  - 任务ID: {step['task_id']}, 名称: {step['task_name']}, 描述: {step['description']}, 工人: {step['worker']}, 时间: {step['estimated_time']}\n"
            few_shot_text += f"计划输出:\n{steps_text}\n"
        
        complete_prompt = final_system_prompt + "\n\n示例:\n" + few_shot_text + "\n\n现在请为以下用户请求生成计划:\n"
        
        # 直接使用字符串格式化，避免 ChatPromptTemplate 的问题
        formatted_prompt = complete_prompt + f"\n\n用户请求: {current_request}"
        
        llm_input = {
            "prompt": formatted_prompt
        }

    try:
        # --- 2. 直接调用 LLM 并解析响应 ---
        if is_revision:
            # 对于修订场景，使用原有的 prompt_to_use
            parser = JsonOutputParser()
            chain = prompt_to_use | planner_llm | parser
            parsed_response = chain.invoke(llm_input)
        else:
            # 对于初始计划生成，直接调用 LLM
            response = planner_llm.invoke(llm_input["prompt"])
            # 尝试解析 JSON 响应
            try:
                import re
                # 提取 JSON 部分
                content = response.content
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    parsed_response = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
            except Exception as json_error:
                logger.error(f"Failed to parse JSON from response: {json_error}")
                raise ValueError(f"Could not parse LLM response as JSON: {response.content}")
        
        logger.info(f"LLM parsed response: {parsed_response}")

        # --- 3. 重写解析逻辑，使其更健壮 ---
        generated_subtasks = []
        if isinstance(parsed_response, dict):
            # 兼容两种常见格式: {"plan": [...]} 或 {"steps": [...]}
            if "plan" in parsed_response and isinstance(parsed_response["plan"], list):
                generated_subtasks = parsed_response["plan"]
            elif "steps" in parsed_response and isinstance(parsed_response["steps"], list):
                generated_subtasks = parsed_response["steps"]
            else:
                logger.error(f"Parsed JSON dictionary has unexpected structure: {parsed_response}")
        elif isinstance(parsed_response, list):
            # LLM 直接返回了一个步骤列表
            generated_subtasks = parsed_response
        else:
            logger.error(f"Unexpected response type from LLM after parsing: {type(parsed_response)}")

        if not generated_subtasks:
             raise ValueError("Could not extract subtasks from LLM response.")

        # 为每个任务添加默认的 status 和 result 字段
        processed_subtasks = []
        for task in generated_subtasks:
            if isinstance(task, dict):
                # 确保所有必需字段都存在
                processed_task = {
                    "task_id": task.get("task_id", ""),
                    "task_name": task.get("task_name", ""),
                    "description": task.get("description", ""),
                    "worker": task.get("worker", "other_worker"),
                    "estimated_time": task.get("estimated_time", "1小时"),
                    "dependencies": task.get("dependencies", []),
                    "status": "pending",
                    "result": None
                }
                processed_subtasks.append(processed_task)
            else:
                logger.error(f"Invalid task format: {task}")

        generated_plan: Plan = {"steps": processed_subtasks}
        logger.info(f"Generated plan: {generated_plan}")

        return {"overall_plan": generated_plan, "current_agent_role": "supervisor", "last_agent_role": "planner"}

    except Exception as e:
        # 这个 Exception 会捕获 JsonOutputParser 的解析错误以及其他所有错误
        logger.error(f"Error during LLM invocation or plan parsing: {e}", exc_info=True)
        return {
            "messages": [AIMessage(content=f"Planner: Failed to generate a valid plan. Error: {e}")],
            "current_agent_role": "supervisor",
            "last_agent_role": "planner",
            "overall_plan": {"steps": []}
        }
