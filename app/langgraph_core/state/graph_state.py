# app/langgraph_core/state/graph_state.py

import operator
from typing import Annotated, List, TypedDict, Optional, Dict, Any
from langchain_core.messages import BaseMessage

class SubTask(TypedDict):
    task_id: str
    task_name: str
    description: str
    worker: Optional[str] # e.g., "other_worker", "dev_team"
    estimated_time: str
    dependencies: List[str]
    status: Optional[str] # "pending", "in_progress", "completed", "failed"
    result: Optional[str] # 任务结果

class Plan(TypedDict):
    steps: List[SubTask] # 计划现在包含子任务列表

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add] # 对话历史
    current_request: Optional[str] # 用户的原始请求
    overall_plan: Optional[Plan] # 策划生成的总计划
    active_subtask_id: Optional[str] # 当前正在处理的子任务ID
    current_agent_role: Optional[str] # 当前活跃的代理角色 (e.g., "supervisor", "planner", "other_worker")
    last_agent_role: Optional[str] # 上一个执行的代理角色，用于路由判断
    last_worker_result: Optional[str] # Other Worker 返回的结果
    plan_revision_count: int  # 计划被修改的次数
    task_revision_count: int  # 单个子任务被修改的次数
    # tool_calls 和 tool_output 暂时保留，以防未来需要
    tool_calls: Optional[List[dict]]
    tool_output: Optional[str]
