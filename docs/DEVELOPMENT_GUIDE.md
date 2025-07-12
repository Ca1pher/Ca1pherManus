# Ca1pherManus 开发指南

## 开发环境设置

### 1. 环境准备

#### 系统要求
- Python 3.8+
- Git
- IDE (推荐 VS Code 或 PyCharm)

#### 安装步骤
```bash
# 1. 克隆项目
git clone <repository-url>
cd Ca1pherManus

# 2. 创建虚拟环境
python -m venv .venv

# 3. 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 安装开发依赖
pip install -r requirements-dev.txt
```

### 2. 开发工具配置

#### VS Code 配置
```json
{
    "python.defaultInterpreterPath": "./.venv/Scripts/python.exe",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true
}
```

#### 预提交钩子
```bash
# 安装 pre-commit
pip install pre-commit
pre-commit install
```

## 代码规范

### 1. Python 代码规范

#### PEP 8 规范
- 使用 4 个空格缩进
- 行长度不超过 88 字符
- 使用 snake_case 命名变量和函数
- 使用 PascalCase 命名类

#### 导入规范
```python
# 标准库导入
import os
import sys
from typing import List, Optional

# 第三方库导入
import fastapi
from langchain_core.messages import HumanMessage

# 本地模块导入
from app.core.config import settings
from app.services.chat_service import ChatService
```

#### 文档字符串
```python
def process_message(message: str) -> dict:
    """
    处理用户消息并返回响应。
    
    Args:
        message: 用户输入的消息
        
    Returns:
        dict: 包含处理结果的字典
        
    Raises:
        ValueError: 当消息格式不正确时
    """
    pass
```

### 2. 项目结构规范

#### 文件命名
- 使用小写字母和下划线
- 避免使用连字符
- 使用有意义的名称

#### 目录结构
```
app/
├── api/                    # API 层
│   └── v1/
│       └── endpoints.py
├── core/                   # 核心配置
│   ├── config.py
│   └── logging_config.py
├── langgraph_core/         # LangGraph 核心
│   ├── agents/            # 代理实现
│   ├── prompts/           # 提示词模板
│   ├── state/             # 状态管理
│   └── workFlow/          # 工作流定义
├── llms/                  # LLM 配置
├── schemas/               # 数据模型
└── services/              # 业务服务
```

### 3. 日志规范

#### 日志级别
```python
import logging

logger = logging.getLogger(__name__)

# 调试信息
logger.debug("调试信息")

# 一般信息
logger.info("一般信息")

# 警告信息
logger.warning("警告信息")

# 错误信息
logger.error("错误信息", exc_info=True)

# 严重错误
logger.critical("严重错误", exc_info=True)
```

#### 日志格式
```python
# 在 logging_config.py 中配置
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 开发工作流

### 1. 功能开发流程

#### 1.1 创建功能分支
```bash
# 从主分支创建新分支
git checkout -b feature/new-feature

# 或者从开发分支创建
git checkout develop
git checkout -b feature/new-feature
```

#### 1.2 开发代码
```python
# 1. 编写代码
# 2. 添加测试
# 3. 更新文档
# 4. 提交代码
```

#### 1.3 代码审查
```bash
# 推送分支
git push origin feature/new-feature

# 创建 Pull Request
# 等待代码审查
# 根据反馈修改代码
```

#### 1.4 合并代码
```bash
# 审查通过后合并到主分支
git checkout main
git merge feature/new-feature
git push origin main
```

### 2. 测试策略

#### 单元测试
```python
# test_planner_agent.py
import pytest
from app.langgraph_core.agents.main.planner_agent import planner_agent

def test_planner_agent_basic():
    """测试 Planner 代理的基本功能"""
    state = {
        "current_request": "测试请求",
        "messages": [],
        "overall_plan": None
    }
    
    result = planner_agent(state)
    
    assert "overall_plan" in result
    assert "current_agent_role" in result
    assert result["current_agent_role"] == "supervisor"
```

#### 集成测试
```python
# test_integration.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_chat_endpoint():
    """测试聊天接口"""
    response = client.post(
        "/api/v1/chat",
        json={"message": "测试消息"}
    )
    
    assert response.status_code == 200
    assert "response" in response.json()
```

#### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest test/test_planner_agent.py

# 运行特定测试函数
pytest test/test_planner_agent.py::test_planner_agent_basic

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

### 3. 调试技巧

#### 3.1 日志调试
```python
import logging

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)

# 在关键位置添加日志
logger.debug(f"状态: {state}")
logger.info(f"处理结果: {result}")
```

#### 3.2 断点调试
```python
# 使用 pdb
import pdb; pdb.set_trace()

# 或者使用 ipdb (需要安装)
import ipdb; ipdb.set_trace()
```

#### 3.3 状态检查
```python
def debug_state(state: dict):
    """调试状态信息"""
    print("=== 状态调试信息 ===")
    print(f"当前代理角色: {state.get('current_agent_role')}")
    print(f"上一个代理角色: {state.get('last_agent_role')}")
    print(f"当前请求: {state.get('current_request')}")
    print(f"计划步骤数: {len(state.get('overall_plan', {}).get('steps', []))}")
    print("==================")
```

## 代理开发指南

### 1. 创建新代理

#### 1.1 代理结构
```python
# app/langgraph_core/agents/main/new_agent.py
import logging
from app.langgraph_core.state.graph_state import AgentState

logger = logging.getLogger(__name__)

def new_agent(state: AgentState) -> AgentState:
    """
    新代理的实现。
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    logger.info("--- Agent: New Agent ---")
    
    # 代理逻辑
    # ...
    
    return {
        "current_agent_role": "supervisor",
        "last_agent_role": "new_agent",
        # 其他状态更新
    }
```

#### 1.2 注册代理
```python
# 在 workFlow.py 中注册
from app.langgraph_core.agents.main.new_agent import new_agent

workflow.add_node("new_agent", new_agent)
```

### 2. 创建新工人

#### 2.1 工人实现
```python
# app/langgraph_core/agents/main/new_worker.py
import logging
from app.langgraph_core.state.graph_state import AgentState
from app.llms.reasoning_models import worker_llm

logger = logging.getLogger(__name__)

def new_worker_agent(state: AgentState) -> AgentState:
    """新工人代理"""
    logger.info("--- Agent: New Worker ---")
    
    # 获取当前任务
    active_task_id = state.get("active_subtask_id")
    overall_plan = state.get("overall_plan")
    
    # 执行任务逻辑
    # ...
    
    return {
        "current_agent_role": "supervisor",
        "last_agent_role": "new_worker",
        "last_worker_result": result
    }
```

#### 2.2 配置工人
```yaml
# app/langgraph_core/agents/workers_config.yaml
workers:
  - name: new_worker
    handler_function: "app.langgraph_core.agents.main.new_worker.new_worker_agent"
    tools: []
```

### 3. 创建新工具

#### 3.1 工具实现
```python
# app/langgraph_core/tools/new_tool.py
from typing import Any
from langchain_core.tools import BaseTool

class NewTool(BaseTool):
    name = "new_tool"
    description = "新工具的描述"
    
    def _run(self, input_text: str) -> str:
        """工具执行逻辑"""
        # 工具实现
        return "工具执行结果"
    
    async def _arun(self, input_text: str) -> str:
        """异步工具执行逻辑"""
        return await self._run(input_text)
```

#### 3.2 注册工具
```python
# 在工人中注册工具
from app.langgraph_core.tools.new_tool import NewTool

tools = [NewTool()]
```

## 提示词开发

### 1. 提示词模板结构

#### 1.1 系统提示词
```markdown
# app/langgraph_core/prompts/agent/system_prompt.md

你是一个专业的代理。

## 角色定义
你的主要职责是...

## 约束条件
1. 条件1
2. 条件2

## 输出格式
你的输出必须是...

## 示例
示例1
示例2
```

#### 1.2 任务提示词
```markdown
# app/langgraph_core/prompts/agent/task_prompt.md

## 任务描述
{task_description}

## 上下文信息
{context}

## 输出要求
{output_requirements}
```

### 2. 提示词优化技巧

#### 2.1 清晰性
- 使用明确的指令
- 避免歧义
- 提供具体示例

#### 2.2 结构化
- 使用标题和子标题
- 使用列表和编号
- 保持一致的格式

#### 2.3 测试和迭代
```python
# 测试提示词
def test_prompt():
    prompt = load_prompt_template("agent/system_prompt.md")
    result = llm.invoke(prompt.format(...))
    print(result.content)
```

## 性能优化

### 1. 代码优化

#### 1.1 异步处理
```python
async def async_agent(state: AgentState) -> AgentState:
    """异步代理实现"""
    # 异步操作
    result = await async_operation()
    return result
```

#### 1.2 缓存机制
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def cached_function(input_data):
    """缓存函数结果"""
    return expensive_operation(input_data)
```

#### 1.3 批量处理
```python
def batch_process(items: List[str]) -> List[str]:
    """批量处理数据"""
    results = []
    for batch in chunks(items, 10):
        batch_result = process_batch(batch)
        results.extend(batch_result)
    return results
```

### 2. 内存优化

#### 2.1 状态清理
```python
def cleanup_state(state: AgentState) -> AgentState:
    """清理状态中的不必要数据"""
    # 清理过长的消息历史
    if len(state.get("messages", [])) > 100:
        state["messages"] = state["messages"][-50:]
    
    return state
```

#### 2.2 资源管理
```python
import contextlib

@contextlib.contextmanager
def resource_manager():
    """资源管理器"""
    resource = acquire_resource()
    try:
        yield resource
    finally:
        release_resource(resource)
```

## 部署指南

### 1. 开发环境部署

#### 1.1 本地开发
```bash
# 启动开发服务器
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动测试服务器
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

#### 1.2 Docker 开发
```dockerfile
# Dockerfile.dev
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 生产环境部署

#### 2.1 Docker 生产
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python -m compileall app/

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2.2 Kubernetes 部署
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ca1phermanus
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ca1phermanus
  template:
    metadata:
      labels:
        app: ca1phermanus
    spec:
      containers:
      - name: ca1phermanus
        image: ca1phermanus:latest
        ports:
        - containerPort: 8000
```

## 故障排除

### 1. 常见问题

#### 1.1 导入错误
```bash
# 检查 Python 路径
python -c "import sys; print(sys.path)"

# 检查虚拟环境
which python
pip list
```

#### 1.2 配置错误
```python
# 检查配置加载
from app.core.config import settings
print(settings.dict())
```

#### 1.3 网络错误
```bash
# 检查网络连接
curl -X GET "http://localhost:8000/health"

# 检查端口占用
netstat -tulpn | grep 8000
```

### 2. 调试工具

#### 2.1 性能分析
```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # 执行函数
    function_to_profile()
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats()
```

#### 2.2 内存分析
```python
import tracemalloc

tracemalloc.start()
# 执行代码
current, peak = tracemalloc.get_traced_memory()
print(f"当前内存使用: {current / 1024 / 1024:.1f} MB")
print(f"峰值内存使用: {peak / 1024 / 1024:.1f} MB")
tracemalloc.stop()
```

## 最佳实践总结

### 1. 代码质量
- 编写清晰的文档字符串
- 使用类型注解
- 遵循 PEP 8 规范
- 编写单元测试

### 2. 性能优化
- 使用异步处理
- 实现缓存机制
- 优化内存使用
- 监控性能指标

### 3. 错误处理
- 实现优雅的错误处理
- 记录详细的错误日志
- 提供用户友好的错误信息
- 实现重试机制

### 4. 安全考虑
- 验证用户输入
- 实现访问控制
- 保护敏感数据
- 定期安全更新

---

**开发愉快！** 🚀 