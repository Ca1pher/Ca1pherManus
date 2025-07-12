# Ca1pherManus 快速开始指南

## 🚀 5分钟快速启动

### 1. 环境准备

确保你的系统已安装：
- Python 3.8+
- Git

### 2. 克隆项目

```bash
git clone <repository-url>
cd Ca1pherManus
```

### 3. 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 配置环境变量

创建 `.env` 文件：

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，添加你的 OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here
```

### 6. 启动服务

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. 测试服务

打开浏览器访问：http://localhost:8000/docs

或者使用 curl 测试：

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "我想下载安装whistle"}'
```

## 📖 使用示例

### 基础聊天

```python
import requests

# 发送聊天请求
response = requests.post(
    "http://localhost:8000/api/v1/chat",
    json={"message": "我想下载安装whistle"}
)

print(response.json())
```

### 流式聊天

```python
import requests

# 流式聊天请求
response = requests.post(
    "http://localhost:8000/api/v1/chat/stream",
    json={"message": "我想下载安装whistle"},
    stream=True
)

for chunk in response.iter_content(chunk_size=1024):
    if chunk:
        print(chunk.decode(), end='')
```

### JavaScript 前端示例

```javascript
// 基础聊天
async function chat(message) {
    const response = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message })
    });
    
    const data = await response.json();
    return data.response;
}

// 流式聊天
async function chatStream(message, onChunk) {
    const response = await fetch('http://localhost:8000/api/v1/chat/stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                onChunk(data);
            }
        }
    }
}

// 使用示例
chatStream("我想下载安装whistle", (data) => {
    console.log(data);
});
```

## 🔧 配置说明

### 工人配置

编辑 `app/langgraph_core/agents/workers_config.yaml`：

```yaml
workers:
  - name: other_worker
    handler_function: "app.langgraph_core.agents.main.other_worker_agent.other_worker_node"
    tools: []
```

### LLM 配置

编辑 `app/llms/reasoning_models.py`：

```python
# Supervisor LLM
supervisor_llm = ChatOpenAI(
    model="gpt-4o-mini", 
    temperature=0.6
)

# Planner LLM
planner_llm = ChatOpenAI(
    model="gpt-4o-mini", 
    temperature=0.3
)

# Worker LLM
worker_llm = ChatOpenAI(
    model="gpt-4o-mini", 
    temperature=0.7
)
```

## 🐛 常见问题

### 1. 启动失败

**问题**：`ModuleNotFoundError: No module named 'app'`

**解决方案**：
```bash
# 确保在项目根目录
pwd
# 应该显示 /path/to/Ca1pherManus

# 检查 Python 路径
python -c "import sys; print(sys.path)"

# 重新安装依赖
pip install -r requirements.txt
```

### 2. API Key 错误

**问题**：`openai.AuthenticationError: Invalid API key`

**解决方案**：
```bash
# 检查环境变量
echo $OPENAI_API_KEY

# 或者在 Windows 上
echo %OPENAI_API_KEY%

# 重新设置环境变量
export OPENAI_API_KEY=your_api_key_here
```

### 3. 端口被占用

**问题**：`OSError: [Errno 98] Address already in use`

**解决方案**：
```bash
# 查找占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或者使用其他端口
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 4. 依赖安装失败

**问题**：`pip install` 失败

**解决方案**：
```bash
# 升级 pip
pip install --upgrade pip

# 清理缓存
pip cache purge

# 重新安装
pip install -r requirements.txt --no-cache-dir
```

## 📊 监控和日志

### 查看日志

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log
```

### 健康检查

```bash
# 检查服务状态
curl http://localhost:8000/health

# 检查 API 文档
curl http://localhost:8000/docs
```

## 🔍 调试技巧

### 1. 启用调试模式

```bash
# 设置调试环境变量
export DEBUG=1
export LOG_LEVEL=DEBUG

# 启动服务
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 查看详细日志

```python
import logging

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)

# 在代码中添加日志
logger = logging.getLogger(__name__)
logger.debug("调试信息")
logger.info("一般信息")
logger.error("错误信息")
```

### 3. 状态调试

```python
# 在代理中添加状态调试
def debug_state(state):
    print("=== 状态调试 ===")
    print(f"当前代理: {state.get('current_agent_role')}")
    print(f"当前请求: {state.get('current_request')}")
    print(f"计划步骤: {len(state.get('overall_plan', {}).get('steps', []))}")
    print("===============")
```

## 🚀 性能优化

### 1. 缓存配置

```python
# 启用缓存
from functools import lru_cache

@lru_cache(maxsize=128)
def cached_function(input_data):
    return expensive_operation(input_data)
```

### 2. 异步处理

```python
import asyncio

async def async_operation():
    # 异步操作
    result = await some_async_function()
    return result
```

### 3. 内存优化

```python
# 清理状态
def cleanup_state(state):
    # 清理过长的消息历史
    if len(state.get("messages", [])) > 100:
        state["messages"] = state["messages"][-50:]
    return state
```

## 📚 学习资源

### 1. 官方文档
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [LangChain 文档](https://python.langchain.com/)

### 2. 项目文档
- [技术架构文档](docs/TECHNICAL_ARCHITECTURE.md)
- [开发指南](docs/DEVELOPMENT_GUIDE.md)
- [项目状态](docs/PROJECT_STATUS.md)

### 3. 示例代码
- [测试文件](test/)
- [API 示例](test_main.http)

## 🤝 获取帮助

### 1. 查看日志
```bash
tail -f logs/app.log
```

### 2. 检查状态
```bash
# 检查服务状态
curl http://localhost:8000/health

# 检查配置
python -c "from app.core.config import settings; print(settings.dict())"
```

### 3. 联系支持
- 创建 Issue
- 查看文档
- 加入社区

---

**开始你的 Ca1pherManus 之旅！** 🚀

如有问题，请查看 [项目状态文档](docs/PROJECT_STATUS.md) 或创建 Issue。 