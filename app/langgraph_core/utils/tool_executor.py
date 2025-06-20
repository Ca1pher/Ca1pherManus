# app/langgraph_core/utils/tool_executor.py

from langgraph.prebuilt import ToolNode

from app.langgraph_core.tools.common_tools import all_tools

# 实例化 ToolExecutor，传入所有工具
tool_executor = ToolNode(all_tools)
