# ComicForge

[English](README.en.md) | 中文

AI 驱动的小说创作与可视化工具：对话、绘图、模型元数据，一体化前后端分离架构。

## ✨ 功能概览

### 🤖 AI 对话系统
- **多提供商支持**：OpenAI / xAI (Grok) / Ollama / Anthropic (Claude) / Google (Gemini) / 自定义端点
- **对话模式**：支持 invoke（直接返回）和 stream（流式输出/SSE）两种模式
- **流式输出**：实时显示 AI 响应，支持 Markdown 渲染和代码高亮
- **会话管理**：多会话支持，会话历史持久化到 SQLite 数据库
- **自动总结**：当消息数量达到配置的倍数时，自动生成对话摘要，保持长期对话连贯性
- **工具调用**：基于 LangChain + LangGraph 构建，集成 43+ 个 MCP 工具函数，支持：
  - 项目管理（查询、更新、进度跟踪）
  - 角色管理（创建、更新、删除、立绘生成、标签管理）
  - 记忆管理（创建、查询、更新、删除、批量操作）
  - 小说内容读取（单行、批量、章节、摘要）
  - 图像生成（SD-Forge 本地生成）
  - 迭代模式（批量处理章节内容）
- **消息状态**：支持消息状态查询（ready/error/success），实时跟踪处理进度
- **开发者模式**：突破模型限制，支持自定义系统提示词
- **超时控制**：可配置的网络请求超时时间
- **递归限制**：可配置的工具调用递归深度限制

### 🎨 图像生成
- **本地生成**：对接 SD-Forge/sd-webui，支持 LoRA/模型切换
- **Civitai 集成**：支持从 Civitai 导入模型元数据（AIR 标识符）
- **结果管理**：按会话/批次保存生成的图像
- **AI 参数生成**：使用 LLM 根据任务名称和描述自动生成绘图参数（prompt、模型、LoRA 等）
- **参数粘贴**：支持从剪切板粘贴绘图参数
- **任务管理**：完整的绘图任务管理系统，支持创建、查看、删除、批量操作
- **状态跟踪**：自动检查任务状态，实时刷新生成中的任务
- **图片预览**：图片画廊对话框，支持键盘导航和缩放

### 📦 模型元数据管理
- **本地扫描**：自动扫描本地 Checkpoint/LoRA 模型
- **Civitai 集成**：抓取模型示例图、参数、描述等信息
- **筛选功能**：按生态系统（SD1/SD2/SDXL）和基础模型筛选
- **元数据缓存**：本地缓存模型元数据，支持离线查看

### 👥 角色（Actor）管理
- **角色创建**：支持创建角色、地点、组织等实体
- **标签系统**：预定义标签（外观、服装、性格、背景等）
- **示例图管理**：为角色添加多张示例图
- **立绘生成**：自动为角色生成 AI 立绘（使用 SD-Forge）
- **颜色标识**：每个角色支持自定义颜色标识

### 🧠 记忆管理
- **键值存储**：基于键值对的记忆条目管理
- **预定义键**：提供常用键的描述和建议
- **批量操作**：支持批量删除会话的所有记忆

### 📖 小说内容管理
- **内容读取**：支持单行、批量、章节范围读取
- **章节管理**：章节列表、摘要、进度跟踪
- **迭代模式**：批量处理章节内容，支持自定义步长和范围
- **段落导航**：便捷的前后段落切换

### ⚙️ 设置与配置
- **可视化配置**：图形界面配置所有设置项
- **自动保存**：配置修改自动保存到 `config.json`
- **环境变量支持**：优先使用环境变量配置
- **响应式布局**：支持不同窗口尺寸的自适应布局
- **前端设置**：图片缓存数量配置（10-1000，默认100）
- **导航栏折叠**：支持导航栏折叠/展开，状态持久化到 localStorage

### 🔌 连接状态管理
- **健康检查**：后端提供 `/health` 健康检查端点
- **自动监控**：前端自动定期检查后端服务连接状态（默认每5秒）
- **状态指示**：导航栏显示实时连接状态（已连接/未连接）
- **连接保护**：服务端未连接时显示遮罩层，阻止用户操作
- **自动恢复**：连接恢复后自动恢复正常功能

## 🗂 目录结构

```
ComicForge/
├── src/
│   ├── api/                   # 后端 FastAPI 服务
│   │   ├── main.py            # FastAPI 主应用
│   │   ├── routers/           # API 路由
│   │   │   ├── project.py     # 项目管理路由
│   │   │   ├── actor.py       # 角色管理路由
│   │   │   ├── memory.py      # 记忆管理路由
│   │   │   ├── reader.py      # 内容读取路由
│   │   │   ├── novel.py       # 小说内容路由
│   │   │   ├── draw.py        # 图像生成路由
│   │   │   ├── llm.py         # LLM 路由
│   │   │   ├── chat.py        # 聊天路由
│   │   │   ├── history.py     # 历史记录路由
│   │   │   ├── file.py        # 文件路由
│   │   │   ├── help.py        # 帮助路由
│   │   │   ├── settings.py    # 设置路由
│   │   │   └── model_meta.py  # 模型元数据路由
│   │   ├── services/          # 业务服务层
│   │   │   ├── db/            # 数据库服务（SQLModel）
│   │   │   │   ├── base.py          # 数据库基础类
│   │   │   │   ├── project_service.py   # 项目管理
│   │   │   │   ├── actor_service.py     # 角色管理
│   │   │   │   ├── memory_service.py    # 记忆管理
│   │   │   │   ├── novel_service.py     # 小说内容
│   │   │   │   ├── draw_service.py      # 绘图服务
│   │   │   │   ├── history_service.py   # 历史记录（包含聊天消息管理）
│   │   │   │   ├── summary_service.py   # 摘要服务
│   │   │   │   └── desperate/            # 旧版聊天服务（已废弃）
│   │   │   ├── llm/           # LLM 服务
│   │   │   │   ├── base.py    # 抽象基类
│   │   │   │   ├── openai.py  # OpenAI 兼容（xAI/OpenAI/Anthropic/Google）
│   │   │   │   └── ollama.py  # Ollama 本地模型
│   │   │   ├── draw/          # 绘图服务
│   │   │   │   ├── base.py        # 绘图服务基类
│   │   │   │   ├── sd_forge.py    # SD-Forge 本地生成
│   │   │   │   └── civitai.py     # Civitai 云端生成
│   │   │   ├── model_meta/    # 模型元数据服务
│   │   │   │   ├── base.py    # 元数据服务基类
│   │   │   │   ├── local.py   # 本地模型扫描
│   │   │   │   └── civitai.py # Civitai 元数据获取
│   │   │   ├── novel_parser.py # 小说解析器
│   │   │   └── transform.py   # 数据转换工具
│   │   │   # 注意：聊天服务功能在 history_service.py 中实现
│   │   ├── schemas/           # Pydantic 数据模型
│   │   │   ├── project.py
│   │   │   ├── actor.py
│   │   │   ├── memory.py
│   │   │   ├── novel.py
│   │   │   ├── chat.py
│   │   │   ├── draw.py
│   │   │   └── model_meta.py
│   │   ├── constants/         # 常量定义
│   │   │   ├── llm.py         # LLM 提供商、模型列表
│   │   │   ├── actor.py       # 角色标签定义
│   │   │   ├── memory.py      # 记忆键定义
│   │   │   ├── model_meta.py  # 模型元数据常量
│   │   │   ├── civitai.py     # Civitai 相关常量
│   │   │   ├── color.py       # 颜色常量
│   │   │   └── ui.py          # UI 相关常量
│   │   ├── settings/          # 配置设置
│   │   │   ├── llm_setting.py      # LLM 配置
│   │   │   ├── draw_setting.py     # 绘图配置
│   │   │   ├── sd_forge_setting.py # SD-Forge 配置
│   │   │   ├── civitai_setting.py  # Civitai 配置
│   │   │   └── frontend_setting.py # 前端 UI 配置
│   │   └── utils/             # 工具函数
│   │       ├── path.py        # 路径工具
│   │       ├── download.py    # 下载工具
│   │       ├── civitai.py     # Civitai 工具
│   │       ├── hash.py        # 哈希工具
│   │       ├── url_util.py    # URL 工具
│   │       ├── pubsub.py      # 发布订阅工具
│   │       ├── responsive.py # 响应式工具（Flet UI，已废弃）
│   │       └── flet_util.py   # Flet 工具（已废弃）
│   │
│   ├── views/                 # Vue 视图页面
│   │   ├── HomeView.vue       # 主页视图
│   │   ├── ChatView.vue       # 聊天视图
│   │   ├── ActorView.vue      # 角色管理视图
│   │   ├── MemoryView.vue     # 记忆管理视图
│   │   ├── ContentView.vue    # 内容管理视图
│   │   ├── ModelView.vue      # 模型管理视图
│   │   ├── TaskView.vue       # 任务管理视图
│   │   ├── HelpView.vue       # 帮助视图
│   │   └── SettingsView.vue   # 设置视图
│   ├── components/            # Vue 组件
│   │   ├── Navigation.vue     # 导航组件
│   │   ├── ActorCard.vue      # 角色卡片组件
│   │   ├── ActorDetailDialog.vue  # 角色详情对话框
│   │   ├── AlertDialog.vue    # 提示对话框
│   │   ├── ConfirmDialog.vue  # 确认对话框
│   │   ├── CreateDrawTaskDialog.vue  # 创建绘图任务对话框
│   │   ├── DrawTaskForm.vue   # 绘图任务表单
│   │   ├── GeneratePortraitDialog.vue  # 生成立绘对话框
│   │   ├── ImageGalleryDialog.vue  # 图片画廊对话框
│   │   ├── ModelCard.vue      # 模型卡片组件
│   │   ├── ModelDetailDialog.vue  # 模型详情对话框
│   │   ├── ModelParamsDialog.vue  # 模型参数对话框
│   │   └── settings/          # 设置相关组件
│   │       ├── LlmSettingsSection.vue
│   │       ├── DrawSettingsSection.vue
│   │       ├── SdForgeSettingsSection.vue
│   │       ├── CivitaiSettingsSection.vue
│   │       └── FrontendSettingsSection.vue
│   ├── router/                # Vue Router 配置
│   │   └── index.ts
│   ├── stores/                # Pinia 状态管理
│   │   ├── index.ts
│   │   ├── project.ts         # 项目状态
│   │   ├── theme.ts           # 主题状态
│   │   ├── connection.ts      # 连接状态管理
│   │   └── navigation.ts      # 导航状态管理（折叠状态）
│   ├── styles/                # 样式文件
│   │   └── highlight.css      # 代码高亮样式
│   ├── utils/                 # 前端工具函数
│   │   ├── apiConfig.ts       # API 配置（基础URL管理）
│   │   ├── device.ts          # 设备检测工具
│   │   ├── imageCache.ts      # 图片缓存管理
│   │   ├── imageUtils.ts      # 图片工具函数（file:// URL 处理）
│   │   └── toast.ts           # Toast 通知工具
│   ├── api/                   # 前端 API 客户端
│   │   └── index.ts           # Axios 实例配置（请求/响应拦截器）
│   ├── assets/                # 静态资源
│   │   └── vue.svg
│   ├── desperate/             # 旧版 Flet UI（已废弃）
│   ├── App.vue                # Vue 根组件
│   ├── main.ts                # 前端入口文件
│   └── style.css              # 全局样式
│
├── storage/                   # 数据存储目录
│   └── data/
│       ├── database.db        # SQLite 数据库（包含聊天历史）
│       ├── model_meta/        # 模型元数据缓存
│       └── projects/          # 项目数据（图像等）
│
├── tests/                     # 测试文件
│   ├── api/                   # API 测试
│   └── sd_forge/              # SD-Forge 测试
│
├── scripts/                   # 开发脚本
│   ├── dev-server.py          # 开发服务器启动脚本
│   ├── dev-server.bat         # Windows 启动脚本
│   └── dev-server.sh          # Linux/Mac 启动脚本
│
├── config.json                # 配置文件（自动生成）
├── package.json               # 前端依赖配置
├── pyproject.toml             # 后端依赖配置
├── vite.config.ts             # Vite 配置
└── tsconfig.json              # TypeScript 配置
```

## 🚀 快速开始

### 环境要求

- **Node.js**: 18+ (用于前端)
- **Python**: 3.13+ (用于后端)
- **可选**: SD-Forge/sd-webui（用于本地图像生成）

### 安装依赖

#### 后端依赖

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -r requirements.txt
```

#### 前端依赖

```bash
# 使用 pnpm（推荐）
pnpm install

# 或使用 npm
npm install

# 或使用 yarn
yarn install
```

### 运行应用

#### 启动后端服务

```bash
# 开发模式（自动重载）- 基础版本
uv run uvicorn api.main:app --reload --host 127.0.0.1 --port 7864 --app-dir src

# 开发模式（优化重载速度）- 推荐
# Windows
scripts\dev-server.bat

# Linux/Mac
chmod +x scripts/dev-server.sh
./scripts/dev-server.sh

# 或使用 Python 脚本（跨平台）
python scripts/dev-server.py

# 生产模式
uv run uvicorn api.main:app --host 127.0.0.1 --port 7864 --app-dir src
```

**优化重载说明**：
- 默认的 `--reload` 会监听所有文件变化，导致重载较慢
- 优化版本只监听 `src/api` 目录，排除 `__pycache__`、`storage`、`tests`、`desperate`、`resources` 等不需要的目录
- 这样可以显著提高重载速度

后端 API 文档：
- **Swagger UI**: http://127.0.0.1:7864/docs
- **ReDoc**: http://127.0.0.1:7864/redoc

#### 启动前端服务

```bash
# 开发模式
pnpm dev

# 或使用 npm
npm run dev

# 构建生产版本
pnpm build

# 预览生产构建
pnpm preview
```

前端默认运行在：http://127.0.0.1:7863

**注意**：需要同时运行前端和后端服务才能正常使用应用。

**开发环境代理**：
- 前端开发服务器（Vite）会自动将 `/api` 开头的请求代理到后端 `http://127.0.0.1:7864`
- 前端代码中使用 `getApiBaseURL()` 获取基础URL，开发环境返回 `/api`，生产环境使用环境变量或默认值

### 配置

#### 方式一：环境变量（推荐）

```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "sk-..."
$env:XAI_API_KEY = "xai-..."
$env:CIVITAI_API_TOKEN = "..."

# Linux/macOS
export OPENAI_API_KEY="sk-..."
export XAI_API_KEY="xai-..."
export CIVITAI_API_TOKEN="..."
```

#### 方式二：应用内设置

启动应用后，在前端界面的"设置"页面中配置：
- 提供商选择（OpenAI / xAI / Ollama / Anthropic / Google / 自定义）
- API Key
- Base URL
- 模型名称
- Temperature
- 请求超时时间

#### 方式三：配置文件

在项目根目录创建或编辑 `config.json`：

```json
{
  "llm": {
    "provider": "xai",
    "api_key": "xai-...",
    "base_url": "https://api.x.ai/v1",
    "model": "grok-4-fast-reasoning",
    "temperature": 0.7,
    "timeout": 60.0,
    "developer_mode": true
  },
  "sd_forge": {
    "base_url": "http://127.0.0.1:7860",
    "home": "C:\\path\\to\\sd-webui-forge",
    "timeout": 30.0,
    "generate_timeout": 300.0
  },
  "civitai": {
    "api_token": "optional-token",
    "timeout": 30.0
  },
  "ui": {
    "ecosystem_filter": null,
    "base_model_filter": null,
    "privacy_mode": true
  },
  "frontend": {
    "image_cache_size": 100
  }
}
```

**配置优先级**：环境变量 > 配置文件 > 默认值

## 🎨 前端架构

ComicForge 使用 Vue 3 + TypeScript 构建现代化的前后端分离架构。

### 主要视图页面

- **HomeView** - 项目主页（项目信息、小说段落、图片展示）
- **ChatView** - AI 对话页面（流式对话、工具调用、迭代模式）
- **ActorView** - 角色管理页面（角色列表、创建编辑、立绘生成）
- **MemoryView** - 记忆管理页面（键值对管理、批量操作）
- **ContentView** - 内容管理页面（章节导航、段落编辑）
- **ModelView** - 模型管理页面（本地扫描、Civitai 集成、元数据查看）
- **TaskView** - 任务管理页面（绘图任务列表、状态跟踪、批量操作、图片预览）
- **HelpView** - 帮助文档页面（MCP 工具说明、使用指南）
- **SettingsView** - 设置页面（LLM、绘图、SD-Forge、Civitai、前端配置）

### 状态管理（Pinia）

- **project** - 当前项目状态、项目列表、项目选择持久化（localStorage）
- **theme** - 主题设置（深色/浅色模式）
- **connection** - 前后端连接状态监控（健康检查、自动重连，默认每5秒检查一次）
- **navigation** - 导航状态管理（导航栏折叠/展开状态，持久化到 localStorage）

### 路由配置

使用 Vue Router 进行单页应用路由管理，支持动态路由和路由守卫。

## 🔌 API 服务

ComicForge 提供 FastAPI 实现的 RESTful API 服务，前端通过 HTTP API（Axios）访问所有功能。

### API 客户端配置

前端 API 客户端（`src/api/index.ts`）使用 Axios 实现：
- **开发环境**：通过 Vite 代理，使用 `/api` 路径（自动转发到 `http://127.0.0.1:7864`）
- **生产环境**：使用环境变量 `VITE_API_BASE_URL`（默认：`http://127.0.0.1:7864`）
- **配置管理**：`src/utils/apiConfig.ts` 提供 `getApiBaseURL()` 函数统一管理基础URL
- **请求拦截器**：自动处理 FormData（不设置 Content-Type，让浏览器自动设置）
- **响应拦截器**：统一错误处理，自动提取 `response.data`

### 主要路由

- `/project/*` - 项目管理（CRUD、列表）
- `/actor/*` - 角色管理（创建、更新、删除、立绘生成）
- `/memory/*` - 记忆管理（键值存储、预定义键）
- `/reader/*` - 内容读取（单行、批量、章节）
- `/novel/*` - 小说内容（章节列表、摘要）
- `/draw/*` - 图像生成（创建任务、任务管理、状态查询、批量删除、清空任务、获取图像）
- `/model-meta/*` - 模型元数据管理（本地扫描、Civitai 导入、元数据查询、示例图片）
- `/llm/*` - LLM 相关功能（模型列表、工具定义、AI 生成绘图参数、选项管理）
- `/chat/*` - 聊天对话（invoke/stream 双模式、迭代模式、消息状态查询）
- `/history/*` - 历史记录（会话管理、消息历史）
- `/file/*` - 文件服务（图片访问）
- `/help/*` - 帮助文档（MCP 工具说明）
- `/settings/*` - 设置管理（配置读取与保存）
- `/health` - 健康检查端点（用于连接状态监控）

## 🛠 主要功能详解

### AI 对话

- **对话模式**：支持 invoke（直接返回完整结果）和 stream（SSE 流式返回）两种模式
- **流式输出**：实时显示 AI 响应，支持 Markdown 格式
- **会话历史**：自动保存对话历史，支持多会话切换
- **自动总结**：当消息数量达到配置阈值时，自动生成对话摘要并保存到记忆系统
- **工具调用**：基于 LangChain 的 tool 机制，AI 可以调用 43+ 个工具函数执行实际操作
  - 工具函数通过路由层暴露，确保安全性（所有工具必须来自 `routers` 目录，不能直接调用服务层）
  - 支持工具调用状态跟踪和错误处理
  - 使用 LangGraph 管理工具调用的状态流转
- **重新编辑**：支持重新编辑已发送的消息（重新发送并继续对话）
- **迭代模式**：批量处理章节内容，支持自定义范围和步长
- **图片缓存**：前端自动缓存图片，提升加载速度

### 项目管理

- **项目选择**：支持多项目切换，自动保存当前选择的项目
- **项目持久化**：使用 localStorage 保存项目选择，刷新后自动恢复
- **自动加载**：启动时自动加载项目列表，并恢复上次选择的项目

### 角色管理

- **创建角色**：设置名称、描述、颜色、标签
- **标签系统**：预定义标签分类（外观、服装、性格、背景、性别等）
- **示例图**：为角色添加多张示例图
- **立绘生成**：使用 SD-Forge 自动生成立绘
- **右键删除**：支持右键删除角色

### 记忆管理

- **键值存储**：基于键值对的记忆条目
- **预定义键**：提供常用键的描述和建议
- **批量删除**：支持批量删除会话的所有记忆

### 模型管理

- **本地扫描**：自动扫描本地 Checkpoint/LoRA 模型
- **Civitai 导入**：通过 AIR 标识符导入模型元数据
- **筛选功能**：按生态系统和基础模型筛选
- **一键打开**：一键在浏览器中打开所有模型的网页链接

### 任务管理

- **任务列表**：查看所有绘图任务，显示任务名称、描述、状态、Job ID
- **状态跟踪**：自动检查任务状态（已完成/生成中），实时刷新生成中的任务（每3秒）
- **批量操作**：支持全选、批量删除、清空所有任务
- **图片预览**：点击已完成任务可预览图片，支持键盘导航（←/→）和缩放
- **图片下载**：支持下载任务生成的图片
- **任务创建**：通过对话框创建新任务，支持 AI 生成参数和从剪切板粘贴参数

## 📝 开发说明

### 技术栈

#### 前端
- **构建工具**: Vite (rolldown-vite) - 使用 rolldown 引擎提升构建性能
- **框架**: Vue 3 + TypeScript
- **UI 框架**: Tailwind CSS + Headless UI + Heroicons
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP 客户端**: Axios（`src/api/index.ts`，支持开发环境代理和生产环境配置）
- **API 配置**: `src/utils/apiConfig.ts` - 统一管理 API 基础URL（开发环境使用代理，生产环境使用环境变量）
- **Markdown 渲染**: marked + highlight.js（代码高亮）
- **图片缓存**: 前端图片缓存机制（`src/utils/imageCache.ts`，支持配置缓存数量，持久化到 localStorage）
- **Toast 通知**: 自定义 Toast 通知系统（`src/utils/toast.ts`）
- **图片工具**: 图片 URL 处理工具（`src/utils/imageUtils.ts`，支持 file:// URL 转换和缓存集成）
- **设备检测**: 设备检测工具（`src/utils/device.ts`）
- **类型系统**: TypeScript

#### 后端
- **Web 框架**: FastAPI
- **数据库**: SQLite (SQLModel)
- **LLM 集成**: LangChain + LangGraph（状态图管理）
- **工具系统**: fastapi-mcp（MCP 工具协议）
- **HTTP 客户端**: httpx
- **数据验证**: Pydantic + Pydantic Settings
- **异步支持**: asyncio
- **图像处理**: Pillow
- **Civitai 集成**: civitai-py
- **日志**: loguru

### 项目特点

- **前后端分离**：清晰的架构分离，便于开发和维护
- **类型安全**：前后端全面使用类型提示（TypeScript + Python）
- **模块化设计**：清晰的分层架构
- **异步支持**：后端使用 async/await 处理异步操作
- **响应式布局**：前端支持不同屏幕尺寸的自适应布局
- **错误处理**：完善的错误处理和日志记录
- **API 文档**：自动生成的 Swagger/OpenAPI 文档

## 🧪 测试

### 后端测试

项目使用 `pytest` 和 FastAPI 的 `TestClient` 进行后端 API 测试。

### 运行测试

```bash
# 运行所有测试
uv run pytest tests/

# 运行特定测试文件
uv run pytest tests/api/test_chat.py

# 运行测试并显示详细输出
uv run pytest tests/api/test_chat.py -v

# 运行测试并显示覆盖率
uv run pytest tests/ --cov=src/api --cov-report=html
```

### 测试结构

```
tests/
├── api/                    # API 测试
│   ├── __init__.py
│   └── test_chat.py        # 聊天对话 API 测试
├── sd_forge/               # SD-Forge 相关测试
└── ...
```

### 测试示例

测试使用 FastAPI 的 `TestClient`，无需启动实际服务器：

```python
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "ComicForge API"

def test_chat_stream():
    response = client.post(
        "/chat/stream",
        json={
            "message": "你好",
            "project_id": "test-project"
        }
    )
    assert response.status_code in [200, 500, 502]  # 可能是成功或服务错误
```

### 测试覆盖的功能

- ✅ 根端点和健康检查
- ✅ 直接对话端点（`/chat/invoke`）- invoke 模式
- ✅ 流式对话端点（`/chat/stream`）- stream 模式
- ✅ 迭代式对话端点（`/chat/iteration`）
- ✅ 聊天总结功能（自动生成对话摘要）
- ✅ 工具调用测试（invoke 和 stream 模式下的工具调用）
- ✅ 消息状态查询（`/chat/status/{message_id}`）
- ✅ 历史记录 CRUD 操作
- ✅ 项目管理 CRUD 操作
- ✅ 请求验证和错误处理

### 注意事项

1. **数据库**：测试会自动初始化数据库，测试数据会写入实际数据库文件
2. **LLM 服务**：测试不验证 LLM 实际调用（需要 API 密钥），仅验证端点可访问性
3. **依赖**：`httpx` 已包含在 `pyproject.toml` 中（TestClient 需要）

### 编写新测试

创建新的测试文件时，遵循以下模式：

```python
import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_your_endpoint(client):
    response = client.get("/your-endpoint")
    assert response.status_code == 200
```

## 📊 项目进度

### ✅ 已完成功能

#### 后端 API（FastAPI）
- ✅ 项目管理（CRUD、列表、切换）
- ✅ 角色管理（创建、更新、删除、示例图、立绘生成）
- ✅ 记忆管理（键值存储、预定义键、批量操作）
- ✅ 小说内容读取（单行、批量、章节范围、摘要）
- ✅ 图像生成（SD-Forge 本地生成、Civitai 集成）
- ✅ 任务管理（创建、查询、删除、批量操作、状态跟踪、图片获取）
- ✅ 模型元数据（本地扫描、Civitai 抓取、筛选）
- ✅ LLM 集成（OpenAI/xAI/Ollama/Anthropic/Google）
- ✅ AI 对话（invoke/stream 双模式、流式输出、工具调用、迭代模式、自动总结）
- ✅ AI 参数生成（使用 LLM 生成绘图参数）
- ✅ 历史记录（会话管理、消息持久化）
- ✅ 配置管理（读取、保存、环境变量优先级）
- ✅ 文件服务（图片访问、静态资源）
- ✅ 帮助文档（MCP 工具定义、使用说明）
- ✅ 健康检查端点（`/health` 用于连接状态监控）

#### 前端 UI（Vue 3 + TypeScript）
- ✅ 主页视图（项目信息、小说段落、图片展示）
- ✅ 聊天视图（流式对话、Markdown 渲染、代码高亮、工具调用显示、消息状态、消息编辑）
- ✅ 角色管理视图（角色列表、创建编辑、立绘生成、颜色标识）
- ✅ 记忆管理视图（键值对编辑、批量删除、预定义键查询）
- ✅ 内容管理视图（章节导航、段落浏览、章节编辑）
- ✅ 模型管理视图（模型列表、元数据查看、筛选、一键打开链接）
- ✅ 任务管理视图（任务列表、状态跟踪、批量操作、图片预览、下载）
- ✅ 设置视图（LLM、绘图、SD-Forge、Civitai、前端配置，自动保存）
- ✅ 帮助视图（MCP 工具说明、使用指南）
- ✅ 导航组件（侧边栏、路由切换、连接状态指示、折叠/展开）
- ✅ 状态管理（Pinia：项目状态、主题切换、连接状态监控、导航状态）
- ✅ 连接状态管理（自动健康检查、状态指示、连接保护、自动恢复）
- ✅ 响应式布局（适配不同屏幕尺寸）
- ✅ 图片缓存系统（自动缓存、过期管理、可配置缓存数量）
- ✅ Toast 通知系统（成功/错误/信息提示）
- ✅ 图片工具函数（file:// URL 处理、图片缓存集成）
- ✅ API 客户端（Axios 配置、请求/响应拦截器、开发环境代理支持）

#### 工具与服务
- ✅ MCP 工具系统（43+ 工具函数，基于 LangChain tool 机制，所有工具通过路由层暴露）
- ✅ 数据库服务（SQLite + SQLModel，自动初始化）
- ✅ 聊天服务（LangGraph 状态图管理、流式处理、工具调用解析、自动总结，聊天消息管理在 `HistoryService` 中）
- ✅ LLM 服务（抽象基类设计，支持多提供商扩展）
- ✅ 小说解析器（章节识别、摘要生成）
- ✅ 数据转换工具（格式转换、数据映射）
- ✅ 章节摘要服务（章节摘要的 CRUD 操作）
- ✅ 图片缓存系统（前端自动缓存，提升性能，持久化到 localStorage）
- ✅ Toast 通知系统（前端消息提示）
- ✅ 图片工具函数（file:// URL 转换、缓存集成）
- ✅ API 配置系统（统一管理 API 基础URL，支持开发环境代理和生产环境配置）

#### 开发工具
- ✅ 开发服务器脚本（优化重载速度）
- ✅ 测试框架（pytest + FastAPI TestClient）
  - ✅ 聊天功能测试（invoke、stream、iteration、summary 等模式）
  - ✅ 项目管理测试（CRUD、服务层测试）
  - ✅ 详细的测试文档和总结（SUMMARY.md）
- ✅ API 文档（Swagger UI + ReDoc）
- ✅ 类型提示（Python + TypeScript 全面覆盖）

### 🚧 进行中

- 🔄 前端性能优化（虚拟滚动、懒加载）
- 🔄 更多单元测试覆盖（其他路由和服务）
- 🔄 错误处理增强

### 📋 计划中

- 📝 用户手册和开发文档
- 📝 Docker 容器化部署
- 📝 更多 LLM 提供商支持
- 📝 插件系统（可扩展工具）
- 📝 多语言支持（i18n）

### 🗑️ 已废弃

- ❌ **desperate/** 目录 - 旧版 Flet UI 实现（已迁移到 Vue 3）
  - 注意：部分遗留代码仍在 `src/api/schemas/desperate/` 和 `src/api/services/db/desperate/` 中，但不影响新版本功能
  - `src/desperate/` - 旧版 Flet UI 页面和组件（已废弃）

## 📄 许可证

见 [LICENSE](LICENSE)
