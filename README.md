# Ca1pherManus - 智能多代理协作系统

## 项目简介（AI生成）

Ca1pherManus 是一个基于 FastAPI 和 LangGraph 构建的智能多代理协作系统。该系统采用分层代理架构，通过 Supervisor（主管）、Planner（规划师）和 Worker（工人）三个角色的协同工作，实现复杂任务的分解、规划和执行。

## 🚀 核心特性

### 多代理协作架构
- **Supervisor（主管）**：负责整体任务协调、计划评估和结果验证
- **Planner（规划师）**：负责任务分解和计划制定
- **Worker（工人）**：负责具体任务的执行

### 智能任务处理
- 自动任务分解和规划
- 动态工人分配
- 计划评估和修正机制
- 结果质量验证

### 技术特性
- 基于 LangGraph 的工作流管理
- 支持动态工人节点注册
- 完整的错误处理和重试机制
- 实时状态流式更新
- 跨域支持的前端接口

## 🏗️ 技术架构

### 后端技术栈
- **FastAPI**: Web 框架
- **LangGraph**: 工作流编排
- **LangChain**: LLM 集成
- **OpenAI GPT-4o-mini**: 大语言模型
- **Python 3.8+**: 主要开发语言

### 项目结构
```
Ca1pherManus/
├── app/
│   ├── api/v1/endpoints.py          # API 端点
│   ├── core/logging_config.py       # 日志配置
│   ├── langgraph_core/              # 核心工作流
│   │   ├── agents/main/             # 代理实现
│   │   ├── prompts/                 # 提示词模板
│   │   ├── state/                   # 状态管理
│   │   ├── tools/                   # 工具集成
│   │   └── workFlow/                # 工作流定义
│   ├── llms/                        # LLM 模型配置
│   ├── schemas/                     # 数据模型
│   └── services/                    # 业务服务
├── config/                          # 配置文件
├── logs/                            # 日志文件
├── test/                            # 测试文件
└── requirements.txt                 # 依赖管理
```

## 📦 安装和使用

### 环境要求
- Python 3.8+
- 虚拟环境（推荐）

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd Ca1pherManus
```

2. **创建虚拟环境**
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **启动服务**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API 使用

#### 聊天接口
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我计算边长3、4、5的三角形的面积"}'
```

#### 流式聊天接口
```bash
curl -X POST "http://localhost:8000/api/v1/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我计算边长3、4、5的三角形的面积"}' \
  --no-buffer
```

## 🔧 配置说明

### 工人配置 (`app/langgraph_core/agents/workers_config.yaml`)
```yaml
workers:
  - name: other_worker
    handler_function: "app.langgraph_core.agents.main.other_worker_agent.other_worker_node"
    tools: []
```

### LLM 配置 (`app/llms/reasoning_models.py`)
- Supervisor LLM: GPT-4o-mini (temperature=0.6)
- Planner LLM: GPT-4o-mini (temperature=0.3)
- Worker LLM: GPT-4o-mini (temperature=0.7)

## 📊 当前状态

### ✅ 已完成功能
- [x] 基础多代理架构搭建
- [x] Supervisor 代理实现（计划评估、任务分配）
- [x] Planner 代理实现（任务分解、计划生成）
- [x] Worker 代理实现（任务执行）
- [x] 工作流编排和路由
- [x] API 接口开发
- [x] 流式响应支持
- [x] 错误处理和重试机制
- [x] 跨域配置
- [x] 日志系统

### 🔄 当前问题修复
- [x] JSON 解析错误修复
- [x] 字符串格式化冲突解决
- [x] 字段名称统一化
- [x] 提示词模板优化

### 🧪 测试状态
- [x] 基础功能测试通过
- [x] Planner 代理测试通过
- [x] 工作流集成测试通过

## 🚀 未来规划

### 短期目标

#### 1. 工具集成扩展
- [ ] 文件操作工具（读写文件）
- [ ] 网络搜索工具
- [ ] 代码执行工具
- [ ] 数据库操作工具

#### 2. 工人类型扩展
- [ ] 研究工人（Research Worker）
- [ ] 开发工人（Development Worker）
- [ ] 测试工人（Testing Worker）
- [ ] 文档工人（Documentation Worker）

#### 3. 用户体验优化
- [ ] Web 前端界面开发
- [ ] 实时进度显示
- [ ] 任务状态可视化
- [ ] 历史记录管理

### 中期目标

#### 1. 高级功能
- [ ] 多轮对话支持
- [ ] 上下文记忆管理
- [ ] 知识库集成
- [ ] 自定义工具开发框架

#### 2. 性能优化
- [ ] 并发处理优化
- [ ] 缓存机制
- [ ] 负载均衡
- [ ] 监控和告警

#### 3. 部署和运维
- [ ] Docker 容器化
- [ ] Kubernetes 部署
- [ ] CI/CD 流水线
- [ ] 生产环境配置

### 长期目标

#### 1. 智能化升级
- [ ] 自适应学习机制
- [ ] 动态工人能力评估
- [ ] 智能任务分配算法
- [ ] 性能自优化

#### 2. 企业级特性
- [ ] 多租户支持
- [ ] 权限管理系统
- [ ] 审计日志
- [ ] 数据加密

#### 3. 生态系统
- [ ] 插件系统
- [ ] API 市场
- [ ] 社区贡献
- [ ] 文档和教程

## 🤝 贡献指南

### 开发环境设置
1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 创建 Pull Request

### 代码规范
- 遵循 PEP 8 代码风格
- 添加适当的注释和文档
- 编写单元测试
- 确保所有测试通过

## 📝 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 联系方式

- 项目维护者：[Your Name]
- 邮箱：[your.email@example.com]
- 项目地址：[GitHub Repository URL]

## 🙏 致谢

感谢以下开源项目的支持：
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [LangChain](https://github.com/langchain-ai/langchain)
- [FastAPI](https://github.com/tiangolo/fastapi)
- [OpenAI](https://openai.com/)

---

**Ca1pherManus** - 让智能代理协作变得简单高效 🚀 