# ComicForge

[English](README.en.md) | 中文

AI 驱动的小说转漫画工具：基于 FastAPI + Vue 3 的前后端分离架构，集成 LLM 对话、SD 图像生成、模型管理等功能。

## ✨ 核心功能

### 🤖 AI 对话系统
- **多提供商**：OpenAI / xAI (Grok) / Ollama / Anthropic / Google / 自定义端点
- **双模式**：invoke（直接返回）和 stream（SSE 流式输出）
- **工具调用**：基于 LangChain + LangGraph，集成 43+ MCP 工具（项目、角色、记忆、小说、绘图等）
- **会话管理**：多会话支持，SQLite 持久化，自动摘要
- **迭代模式**：批量处理章节内容

### 🎨 图像生成
- **本地生成**：对接 SD-Forge/sd-webui（LoRA/模型切换）
- **Civitai 集成**：模型元数据导入（AIR 标识符）
- **任务管理**：批量创建（1-16），状态跟踪，图片预览
- **AI 参数生成**：LLM 自动生成绘图参数

### 📦 模型元数据
- **本地扫描**：自动扫描 Checkpoint/LoRA
- **Civitai 集成**：抓取示例图、参数、描述
- **筛选/喜爱**：按生态系统/基础模型筛选，标记常用模型
- **隐私模式**：隐藏预览图

### 👥 角色管理
- **创建编辑**：支持角色、地点、组织等实体
- **标签系统**：预定义标签（外观、服装、性格等）
- **立绘生成**：双模式（创建新任务/选择已有任务）
- **示例图管理**：多图上传，自动清理

### 🧠 记忆 & 小说
- **记忆系统**：键值对存储，预定义键，批量操作
- **小说阅读**：单行/批量/章节读取，摘要生成

## 🗂 项目结构

```
ComicForge/
├── src/
│   ├── api/                      # 后端 FastAPI
│   │   ├── main.py               # 应用入口
│   │   ├── routers/              # API 路由（11个）
│   │   │   ├── chat.py           # 对话（invoke/stream/iteration）
│   │   │   ├── context.py        # 内容服务（小说/章节/段落/图像）
│   │   │   ├── draw.py           # 绘图任务管理
│   │   │   ├── model_meta.py     # 模型元数据
│   │   │   ├── actor.py          # 角色管理
│   │   │   ├── project.py        # 项目管理
│   │   │   ├── memory.py         # 记忆管理
│   │   │   ├── history.py        # 会话历史
│   │   │   ├── llm.py            # LLM 相关
│   │   │   ├── settings.py       # 设置管理
│   │   │   └── help.py           # 帮助文档
│   │   ├── services/             # 业务服务层
│   │   │   ├── db/               # 数据库服务（SQLModel）
│   │   │   │   ├── base.py       # 数据库初始化
│   │   │   │   ├── history_service.py    # 会话/消息管理
│   │   │   │   ├── project_service.py    # 项目
│   │   │   │   ├── actor_service.py      # 角色
│   │   │   │   ├── memory_service.py     # 记忆
│   │   │   │   ├── novel_service.py      # 小说
│   │   │   │   ├── draw_service.py       # 绘图任务
│   │   │   │   └── summary_service.py    # 摘要
│   │   │   ├── llm/              # LLM 服务
│   │   │   │   ├── base.py       # 抽象基类（LangGraph）
│   │   │   │   ├── openai.py     # OpenAI 兼容
│   │   │   │   └── ollama.py     # Ollama
│   │   │   ├── draw/             # 绘图服务
│   │   │   │   ├── sd_forge.py   # SD-Forge
│   │   │   │   └── civitai.py    # Civitai
│   │   │   ├── model_meta/       # 模型元数据
│   │   │   │   ├── local.py      # 本地扫描
│   │   │   │   └── civitai.py    # Civitai 抓取
│   │   │   ├── novel_parser.py   # 小说解析器
│   │   │   └── transform.py      # 数据转换
│   │   ├── schemas/              # Pydantic 模型
│   │   ├── constants/            # 常量定义
│   │   ├── settings/             # 配置类
│   │   └── utils/                # 工具函数
│   │
│   ├── views/                    # Vue 视图（9个）
│   │   ├── ChatView.vue          # 对话界面
│   │   ├── TaskView.vue          # 任务管理
│   │   ├── ModelView.vue         # 模型管理
│   │   ├── ActorView.vue         # 角色管理
│   │   ├── MemoryView.vue        # 记忆管理
│   │   ├── ContentView.vue       # 内容管理
│   │   ├── HomeView.vue          # 主页
│   │   ├── SettingsView.vue      # 设置
│   │   └── HelpView.vue          # 帮助
│   ├── components/               # Vue 组件
│   ├── router/                   # 路由配置
│   ├── stores/                   # Pinia 状态管理
│   ├── utils/                    # 前端工具
│   └── api/                      # Axios 客户端
│
├── storage/                      # 数据存储
│   └── data/
│       ├── database.db           # SQLite
│       ├── model_meta/           # 模型缓存
│       └── projects/             # 项目数据
├── tests/                        # 测试
├── scripts/                      # 脚本
├── docker-compose.yml            # Docker 编排
├── Dockerfile.backend            # 后端镜像
├── Dockerfile.frontend           # 前端镜像
├── config.json                   # 配置文件
├── package.json                  # 前端依赖
└── pyproject.toml                # 后端依赖
```

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd ComicForge

# 2. 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 文件，添加 API Keys

# 3. 启动服务
docker-compose up -d

# 4. 访问应用
# 前端：http://localhost:7863
# 后端 API：http://localhost:7864/docs
```

**Docker 说明**：
- 自动构建前后端镜像
- 数据持久化（`./storage` 目录）
- 支持环境变量配置
- 健康检查和自动重启

### 方式二：本地开发

**环境要求**：Node.js 18+ / Python 3.13+

```bash
# 1. 安装依赖
pnpm install          # 前端
uv sync               # 后端

# 2. 启动后端（端口 7864）
uv run uvicorn api.main:app --reload --app-dir src
# 或使用优化脚本：scripts/dev-server.bat (Windows) / scripts/dev-server.sh (Linux/Mac)

# 3. 启动前端（端口 7863）
pnpm dev

# 4. 访问
# 前端：http://localhost:7863
# API 文档：http://localhost:7864/docs
```

### 配置说明

**优先级**：环境变量 > `config.json` > 默认值

```bash
# 环境变量示例
export OPENAI_API_KEY="sk-..."
export XAI_API_KEY="xai-..."
export CIVITAI_API_TOKEN="..."
```

或在 `config.json` 中配置：
```json
{
  "llm": {
    "provider": "xai",
    "api_key": "xai-...",
    "model": "grok-4-fast-reasoning"
  },
  "sd_forge": {
    "base_url": "http://127.0.0.1:7860"
  }
}
```

也可在 Web 界面的"设置"页面直接配置。

## 🏗 技术架构

### 前端（Vue 3 + TypeScript）
- **构建工具**：Vite (rolldown)
- **UI 框架**：Tailwind CSS + Headless UI
- **状态管理**：Pinia（project/theme/connection/navigation/privacy）
- **路由**：Vue Router
- **HTTP**：Axios（开发环境代理 `/api` → 后端）
- **Markdown**：marked + highlight.js
- **缓存**：localStorage（图片/状态持久化）

### 后端（FastAPI + Python 3.13）
- **Web 框架**：FastAPI
- **数据库**：SQLite + SQLModel
- **LLM**：LangChain + LangGraph（状态图管理）
- **工具系统**：fastapi-mcp（43+ MCP 工具）
- **HTTP 客户端**：httpx
- **图像生成**：SD-Forge API / Civitai API
- **日志**：loguru

### 主要 API 端点
- `/chat/*` - 对话（invoke/stream/iteration）
- `/draw/*` - 绘图任务（CRUD/批量/状态）
- `/model-meta/*` - 模型元数据（扫描/导入）
- `/actor/*` - 角色管理
- `/project/*` - 项目管理
- `/memory/*` - 记忆管理
- `/novel/*` - 小说内容
- `/history/*` - 会话历史
- `/settings/*` - 配置管理
- `/health` - 健康检查

## 📝 开发指南

### 项目特点
- **前后端分离**：清晰的架构，独立开发部署
- **类型安全**：全面类型提示（TypeScript + Python）
- **模块化设计**：分层架构（Router → Service → DB）
- **异步处理**：async/await + SSE 流式响应
- **状态管理**：LangGraph 状态图 + Pinia 前端状态
- **工具生态**：43+ MCP 工具，可扩展

## 🧪 测试

```bash
# 运行所有测试
uv run pytest tests/

# 运行特定测试
uv run pytest tests/api/test_chat.py -v

# 测试覆盖率
uv run pytest tests/ --cov=src/api --cov-report=html
```

**已覆盖**：对话（invoke/stream/iteration）、工具调用、会话管理、项目 CRUD、消息状态查询

## 📊 功能状态

### ✅ 核心功能（已完成）
- **后端**：11 个 API 路由，SQLite 数据库，LangChain + LangGraph 工具调用
- **前端**：9 个 Vue 视图，Pinia 状态管理，Axios HTTP 客户端
- **AI 对话**：invoke/stream/iteration 三种模式，43+ MCP 工具
- **图像生成**：SD-Forge 本地生成，Civitai 集成，批量任务管理
- **模型管理**：本地扫描，Civitai 元数据导入，筛选/喜爱
- **角色管理**：创建编辑，标签系统，立绘生成（双模式）
- **部署**：Docker Compose 容器化，健康检查，自动重启

### 🚧 持续改进
- 前端性能优化（虚拟滚动）
- 测试覆盖率提升
- 错误处理增强

## 📄 许可证

见 [LICENSE](LICENSE)
