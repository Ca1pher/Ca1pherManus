# app/langgraph_core/graphs/main_graph.py
import logging
from langgraph.graph import StateGraph, END
from app.langgraph_core.state.graph_state import AgentState
# 导入我们新定义的节点函数和路由函数
from app.langgraph_core.agents.main.supervisor_agent import supervisor_agent
from app.langgraph_core.agents.main.planner_agent import planner_agent
from app.langgraph_core.agents.main.other_worker_agent import other_worker_agent  # 导入 Other Worker Agent

# 获取logger实例，使用 __name__ 可以自动根据模块路径命名 logger
logger = logging.getLogger(__name__)

# 路由函数 (根据 current_agent_role 决定流向)
def route_to_agent(state: AgentState) -> str:
    role = state.get("current_agent_role")

    # 这些返回的字符串必须与 add_conditional_edges 字典中的键匹配
    if role == "planner":
        return "planner"  # <-- 返回键 "planner"
    elif role == "other_worker":
        return "other_worker"  # <-- 返回键 "other_worker"
    elif role == "supervisor":  # 当 planner 或 worker 路由回 supervisor 时
        return "supervisor"  # <-- 返回键 "supervisor"
    elif role == "end_process":
        return END

    logger.error(f"Routing Error: Unknown role '{role}' or missing role in state.")
    return END  # 异常情况下结束图


def build_main_graph():
    workflow = StateGraph(AgentState)

    # 添加所有顶层图的节点
    workflow.add_node("supervisor_node", supervisor_agent)
    logger.info("Added node 'supervisor_node'.")
    workflow.add_node("planner_node", planner_agent)
    logger.info("Added node 'planner_node'.")
    workflow.add_node("other_worker_node", other_worker_agent)
    logger.info("Added node 'other_worker_node'.")

    # 设置入口点为 Supervisor 节点
    workflow.set_entry_point("supervisor_node")

    # 定义从 Supervisor 节点的条件边
    workflow.add_conditional_edges(
        "supervisor_node",
        route_to_agent,  # Supervisor 处理后，路由到 Planner 或 Other Worker 或结束
        {
            "planner": "planner_node",
            "other_worker": "other_worker_node",
            END: END  # 如果 route_to_agent 返回 END，则图结束
        }
    )

    # 定义从 Planner 节点的条件边 (策划完成后总是返回给 Supervisor)
    workflow.add_conditional_edges(
        "planner_node",
        route_to_agent,  # Planner 处理后，路由回 Supervisor
        {"supervisor": "supervisor_node"}
    )

    # 定义从 Other Worker 节点的条件边 (工人完成后总是返回给 Supervisor)
    workflow.add_conditional_edges(
        "other_worker_node",
        route_to_agent,  # Other Worker 处理后，路由回 Supervisor
        {"supervisor": "supervisor_node"}
    )

    return workflow.compile(name="main_graph")


# 编译图
main_app_graph = build_main_graph()
