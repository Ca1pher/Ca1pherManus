# app/langgraph_core/graphs/main_graph.py
import logging
import importlib
from langgraph.graph import StateGraph, END
from app.langgraph_core.state.graph_state import AgentState, SubTask
from app.langgraph_core.agents.main.supervisor_agent import supervisor_agent
from app.langgraph_core.agents.main.planner_agent import planner_agent

# 导入我们的配置加载器
from app.langgraph_core.agents.config_loader import WORKERS_CONFIG

logger = logging.getLogger(__name__)

def _find_active_task(state: AgentState) -> SubTask | None:
    """在计划中找到当前激活的任务"""
    active_task_id = state.get("active_subtask_id")
    if not active_task_id:
        return None
    for task in state.get("overall_plan", {}).get("steps", []):
        if task.get("id") == active_task_id:
            return task
    return None

def import_from_string(path: str):
    """根据字符串路径动态导入函数或类"""
    try:
        module_path, class_name = path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to import '{path}': {e}")
        raise

# 路由函数
def route_to_agent(state: AgentState) -> str:
    # 场景1：如果 supervisor 决定分配任务，则根据任务的 assigned_to 路由
    active_task = _find_active_task(state)
    if active_task and active_task.get("status") == "active":
        assignee = active_task.get("assigned_to")
        if assignee:
            logger.info(f"Routing to assigned worker: '{assignee}'")
            return assignee # <-- 直接返回工人名字，如 "research_worker"
        else:
            logger.error("Active task has no assignee! Ending process.")
            return END
            
    # 场景2：其他情况，根据 current_agent_role 路由
    role = state.get("current_agent_role")
    if role == "planner":
        return "planner"
    elif role == "supervisor":
        return "supervisor"
    elif role == "end_process":
        return END

    logger.error(f"Routing Error: Unknown role '{role}' or state. Cannot determine next step.")
    return END

def build_main_graph():
    workflow = StateGraph(AgentState)

    # 静态添加核心节点：supervisor 和 planner
    workflow.add_node("supervisor", supervisor_agent)
    workflow.add_node("planner", planner_agent)
    logger.info("Added core nodes: 'supervisor', 'planner'.")

    # 动态添加所有工人节点
    worker_nodes = {}
    for worker_config in WORKERS_CONFIG.get("workers", []):
        worker_name = worker_config["name"]
        handler_path = worker_config["handler_function"]
        try:
            handler_function = import_from_string(handler_path)
            workflow.add_node(worker_name, handler_function)
            worker_nodes[worker_name] = worker_name # 用于后面条件边的映射
            logger.info(f"Dynamically added worker node: '{worker_name}' from '{handler_path}'")
        except Exception as e:
            logger.critical(f"Could not add worker node '{worker_name}'. Skipping. Error: {e}")

    # 设置入口点
    workflow.set_entry_point("supervisor")

    # 定义从 Supervisor 出发的条件边
    # 它可以路由到 planner，或者任何一个 worker，或者结束
    supervisor_edges = {"planner": "planner", END: END}
    supervisor_edges.update(worker_nodes)
    workflow.add_conditional_edges("supervisor", route_to_agent, supervisor_edges)

    # Planner 完成后总是返回给 Supervisor
    workflow.add_edge("planner", "supervisor")

    # 所有工人节点完成后，也总是返回给 Supervisor
    for worker_name in worker_nodes:
        workflow.add_edge(worker_name, "supervisor")

    # 编译图
    return workflow.compile(checkpointer=None, name="DynamicAgentGraph") # 使用内存 checkpointer

# --- 编译图 ---
main_app_graph = build_main_graph()
logger.info("Main graph compiled successfully.")
