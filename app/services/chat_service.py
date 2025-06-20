# app/services/chat_service.py

import json
from typing import AsyncGenerator, Dict, Any
from langchain_core.messages import HumanMessage

from app.schemas.chat import ChatRequest, StreamEvent
from app.langgraph_core.graphs.main_graph import main_app_graph
from app.langgraph_core.state.graph_state import AgentState


async def stream_langgraph_response(request: ChatRequest) -> AsyncGenerator[str, None]:
    """
    Streams the execution state of the LangGraph workflow.
    Yields events in Server-Sent Events (SSE) format.
    """
    initial_state: AgentState = {
        "messages": [HumanMessage(content=request.message)],
        "current_agent_role": None, # <--- 第一次调用时，让它为 None，由 supervisor_agent 来设置下一个角色
        "current_request": None,
        "overall_plan": None,
        "active_subtask_id": None,
        "last_agent_role": None,
        "last_worker_result": None,
        "tool_calls": None,
        "tool_output": None
    }

    try:
        # Use astream() for asynchronous streaming
        async for state_update in main_app_graph.astream(initial_state):
            # 打印完整的状态更新，便于调试
            print(f"LangGraph Stream Update: {state_update}")

            # 提取节点名称和更新后的当前状态
            # LangGraph 的 astream 会返回 {node_name: state_after_node_execution}
            # 或者在图结束时返回 {__end__: final_state}
            node_name = list(state_update.keys())[0]
            current_state = state_update[node_name]  # 获取该节点执行后的完整状态

            event = StreamEvent(
                event_type="node_update",
                node=node_name,
                data=current_state,
                message=f"Node '{node_name}' executed."
            )
            yield f"data: {event.model_dump_json()}\n\n"

            final_state = current_state  # 持续跟踪最终状态

        # 循环结束后，输出最终答案
        if final_state and final_state.get("messages"):
            final_llm_message = final_state["messages"][-1]
            final_answer_content = final_llm_message.content

            final_event = StreamEvent(
                event_type="final_answer",
                data={"final_message": final_llm_message.dict()},
                message=final_answer_content
            )
            yield f"data: {final_event.model_dump_json()}\n\n"
        else:
            error_event = StreamEvent(
                event_type="error",
                data={},
                message="No final message found in LangGraph state."
            )
            yield f"data: {error_event.model_dump_json()}\n\n"

    except Exception as e:
        # 打印实际的异常类型和信息，这将提供关键的调试线索
        print(f"Error during LangGraph streaming: {type(e).__name__}: {e}")
        error_event = StreamEvent(
            event_type="error",
            data={"error_details": f"{type(e).__name__}: {e}"},
            message=f"An error occurred during processing: {type(e).__name__}: {e}"
        )
        yield f"data: {error_event.model_dump_json()}\n\n"

