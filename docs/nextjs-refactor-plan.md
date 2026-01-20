# Next.js 重构计划

## 📋 概述

将当前 FastAPI + Vue 3 架构重构为纯 Next.js 全栈应用，移除 Python 后端依赖。

## 🛠 技术栈

### 核心框架
- **Next.js 14+** (App Router)
- **TypeScript**
- **React 18+**
- **Bun** - 包管理和运行时（替代 npm/pnpm）

### 数据库
- **Prisma** - ORM
- **SQLite** - 数据库（全新设计，可优化现有架构）

### LLM 服务
- **@langchain/core** - LangChain 核心
- **@langchain/openai** - OpenAI 兼容（xAI/Anthropic/Google等）
- **@langchain/ollama** - Ollama 支持
- **@langchain/langgraph** - 状态图管理
- **zod** - 数据验证和工具定义

### SD-Forge 集成
- **sharp** - 图像处理（替代 PIL，仅 Node.js Runtime）
- **axios** - HTTP 客户端（替代 requests）

### 前端 UI
- **Tailwind CSS** - 样式框架
- **shadcn/ui** - UI 组件库（替代 Headless UI）
- **lucide-react** - 图标库（替代 Heroicons）
- **sonner** - Toast 通知

### 状态管理
- **Zustand** - 轻量级状态管理（支持持久化到 localStorage）

### 其他
- **自定义 JWT** - 用户认证（不使用 next-auth，保持简单）
- **bcryptjs** - 密码哈希
- **marked** + **highlight.js** - Markdown 渲染

## 📁 项目结构

```
nextjs-comicforge/
├── app/                          # Next.js App Router
│   ├── api/                      # API Routes（后端逻辑）
│   │   ├── chat/
│   │   │   ├── route.ts          # 聊天对话（invoke/stream）
│   │   │   └── iteration/route.ts # 迭代式对话
│   │   ├── llm/
│   │   │   ├── generate-params/route.ts  # AI生成绘图参数
│   │   │   ├── extract-actors/route.ts   # 角色提取
│   │   │   └── bind-images/route.ts      # 段落图像绑定
│   │   ├── draw/
│   │   │   ├── txt2img/route.ts  # 文本生成图像
│   │   │   ├── img2img/route.ts  # 图像到图像
│   │   │   └── batch/route.ts    # 批量生成
│   │   ├── project/              # 项目管理 CRUD
│   │   ├── actor/                # 角色管理 CRUD
│   │   ├── memory/               # 记忆管理 CRUD
│   │   ├── content/              # 内容管理 CRUD
│   │   ├── summary/              # 摘要管理 CRUD
│   │   ├── history/              # 历史记录 CRUD
│   │   ├── model-meta/           # 模型元数据（本地扫描/Civitai）
│   │   ├── auth/                 # 用户认证
│   │   ├── settings/             # 配置管理
│   │   └── file/                 # 文件服务
│   │
│   ├── (pages)/                  # 前端页面
│   │   ├── page.tsx              # 主页
│   │   ├── chat/                 # 聊天页面
│   │   ├── actor/                # 角色管理
│   │   ├── memory/               # 记忆管理
│   │   ├── content/              # 内容管理
│   │   ├── model/                # 模型管理
│   │   ├── task/                 # 任务管理
│   │   ├── settings/             # 设置页面
│   │   ├── help/                 # 帮助页面
│   │   └── login/                # 登录页面
│   │
│   ├── layout.tsx                # 根布局
│   └── globals.css               # 全局样式
│
├── lib/                          # 共享库代码
│   ├── llm/                      # LLM 服务
│   │   ├── service.ts            # LLM 服务基类
│   │   ├── openai-service.ts    # OpenAI 兼容服务
│   │   ├── ollama-service.ts    # Ollama 服务
│   │   └── tools/                # 39个工具函数
│   │       ├── project-tools.ts
│   │       ├── actor-tools.ts
│   │       ├── memory-tools.ts
│   │       ├── content-tools.ts
│   │       ├── draw-tools.ts
│   │       └── model-tools.ts
│   │
│   ├── sd-forge/                 # SD-Forge 客户端
│   │   ├── webuiapi.ts           # WebUIApi 实现（TypeScript）
│   │   ├── types.ts              # 类型定义
│   │   └── utils.ts              # 工具函数
│   │
│   ├── db/                       # 数据库
│   │   ├── prisma.ts             # Prisma 客户端
│   │   └── migrations/           # 数据库迁移
│   │
│   ├── auth/                     # 认证相关
│   │   ├── jwt.ts                # JWT 工具
│   │   └── password.ts           # 密码哈希
│   │
│   ├── utils/                    # 工具函数
│   │   ├── image.ts              # 图像处理
│   │   ├── file.ts               # 文件处理
│   │   └── parser.ts             # 小说解析器
│   │
│   └── constants/                # 常量定义
│       ├── llm.ts               # LLM 相关常量
│       ├── actor.ts              # 角色标签
│       └── memory.ts             # 记忆键定义
│
├── components/                   # React 组件
│   ├── ui/                       # 通用 UI 组件
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   └── Dialog.tsx
│   │
│   ├── Navigation.tsx            # 导航组件
│   ├── ActorCard.tsx             # 角色卡片
│   ├── ActorDetailDialog.tsx     # 角色详情对话框
│   ├── CreateDrawTaskDialog.tsx  # 创建绘图任务
│   ├── ImageGalleryDialog.tsx    # 图片画廊
│   ├── ModelCard.tsx             # 模型卡片
│   └── settings/                 # 设置相关组件
│
├── stores/                       # 状态管理（Zustand + 持久化）
│   ├── project.ts                # 项目状态（持久化到 localStorage）
│   ├── auth.ts                   # 认证状态（持久化到 localStorage）
│   ├── connection.ts             # 连接状态（内存状态）
│   └── privacy.ts                # 隐私模式（持久化到 localStorage）
│
├── types/                        # TypeScript 类型定义
│   ├── project.ts
│   ├── actor.ts
│   ├── memory.ts
│   ├── draw.ts
│   └── llm.ts
│
├── prisma/
│   └── schema.prisma             # Prisma 数据模型
│
├── public/                       # 静态资源
│
└── storage/                       # 数据存储（与现有保持一致）
    ├── data/
    │   ├── database.db           # SQLite 数据库
    │   ├── images/               # 统一图片存储（MD5 哈希命名）
    │   ├── model_meta/           # 模型元数据缓存
    │   └── projects/             # 项目数据
    └── temp/                     # 临时文件
```

## 🔑 核心模块说明

### 1. LLM 服务模块 (`lib/llm/`)
- **service.ts**: LLM 服务抽象基类，管理工具调用、状态图
- **openai-service.ts**: OpenAI 兼容服务（xAI/Anthropic/Google）
- **ollama-service.ts**: Ollama 本地模型服务
- **tools/**: 39个工具函数，直接访问 Prisma 数据库

### 2. SD-Forge 客户端 (`lib/sd-forge/`)
- **webuiapi.ts**: WebUIApi 的 TypeScript 实现
  - 使用 `sharp` 处理图像
  - 使用 `axios` 发送 HTTP 请求
  - 实现所有 webuiapi 的方法（txt2img, img2img, get_models 等）

### 3. 数据库层 (`lib/db/`)
- **prisma.ts**: Prisma 客户端单例
- **schema.prisma**: 数据模型定义（全新设计，可优化现有架构）
  - 考虑改进点：索引优化、关系设计、字段类型选择

### 4. API Routes (`app/api/`)
- 所有业务逻辑的 HTTP 端点
- 使用 Next.js Server Actions 或 Route Handlers
- 流式响应使用 Server-Sent Events (SSE)

### 5. 前端页面 (`app/(pages)/`)
- 从 Vue 3 组件迁移到 React 组件
- 使用 Server Components 和 Client Components
- 保持现有 UI 和交互逻辑

## ⚠️ 技术决策

### 1. 数据库设计
- **全新设计**: 不迁移现有数据库，使用 Prisma 重新设计 Schema
- **优化点**:
  - **索引优化**: 所有 `project_id` 外键添加索引，高频查询字段添加索引，组合索引优化多条件查询
  - **关系设计**: 使用 Prisma 关系（`@relation`）替代手动管理外键，考虑级联删除策略
  - **字段类型**: JSON 数据使用 `Json` 类型，时间戳使用 `DateTime`，大文本使用 `String`（SQLite TEXT）
  - **软删除**: 建议添加 `deletedAt DateTime?` 字段实现软删除

### 2. 工具函数实现
- **直接访问 Prisma**: 工具函数直接调用 Prisma 客户端，不需要 Service Layer 中间层
- **统一错误处理**: 使用错误处理包装器，工具函数返回统一格式（成功返回数据，失败返回错误对象）
- **按功能分组**: project-tools, actor-tools, memory-tools 等
- **类型安全**: 使用 TypeScript 严格类型检查

### 3. 流式响应
- **实现方式**: 使用 Route Handlers + SSE（Server-Sent Events）
- **超时策略**: 默认 5 分钟，可配置
- **连接管理**: Next.js 自动管理，无需手动处理

### 4. 图像处理
- **Runtime**: 仅在 Node.js Runtime 使用 `sharp`（非 Edge Runtime）
- **图像缓存**: 多层缓存策略
  - **内存缓存**: 使用 Map 实现 LRU 缓存（最近使用的图像）
  - **文件缓存**: 缓存处理后的图像到 `storage/temp/image-cache/`
  - **缓存键**: 基于图像路径 + 处理参数的哈希值
  - **缓存大小**: 可配置（默认 100MB 内存，1000 个文件）
  - **缓存清理**: 定期清理过期缓存，限制缓存大小

### 5. 文件系统访问和图片存储
- **图片存储**: 所有图片统一存储在 `storage/data/images/` 目录下
- **命名策略**: 使用 MD5 哈希值作为文件名，格式：`{hash}.{ext}`
- **去重机制**: 相同内容的图片只存储一份（相同内容 = 相同 MD5）
- **存储方式**: 在需要图片的地方（Actor.examples, Content.imageHash, Job.data 等）直接存储哈希值字符串
- **实现方式**: 使用 Node.js `fs/promises` API + `sharp` 处理图片
- **文件访问**: 通过 `/api/file/image/[hash]` API 访问图片
- **详细方案**: 参见 `docs/database-storage-plan.md`

### 6. 配置管理
- **配置文件**: 使用 `storage/config.json`，不使用环境变量
- **配置加载**: 应用启动时读取，支持热更新（通过 API 更新）
- **配置验证**: 使用 Zod Schema 验证配置格式
- **默认值**: 配置缺失时使用默认值
- **敏感信息**: API Keys 存储在配置文件中（生产环境建议加密）

### 7. 认证系统
- **实现方式**: 自定义 JWT 实现（不使用 next-auth，保持简单）
- **Token 策略**:
  - **Access Token**: JWT，15分钟有效期，存储在 localStorage
  - **Refresh Token**: 随机字符串，14天有效期，存储在 HttpOnly Cookie
- **刷新策略**: Axios 拦截器自动刷新，401 时调用 `/api/auth/refresh`
- **Session 管理**: 无状态 JWT，不需要服务端 Session 存储

### 8. 状态管理
- **方案**: 使用 Zustand + 持久化到 localStorage
- **持久化策略**: 使用 Zustand `persist` middleware 自动持久化
- **状态分类**:
  - **前端状态**（持久化到 localStorage）: 项目选择、隐私模式、导航状态、认证 Token
  - **内存状态**: 连接状态（不需要持久化）
- **不需要数据库**: 前端状态不需要服务端同步，不需要数据库存储

### 9. 模型元数据
- **Civitai 集成**: 重写为 TypeScript，直接调用 Civitai HTTP API
- **本地扫描**: 使用 Node.js `fs` API 扫描模型目录
- **缓存策略**: 元数据存储在 `storage/data/model_meta/`，支持增量更新

### 10. 部署策略
- **Runtime**: 使用 Node.js Runtime（非 Edge Runtime）
- **部署方式**: 纯服务端部署，不考虑 Serverless
- **支持特性**: 长时间运行的流式请求，本地文件系统访问
- **数据库**: 数据库文件存储在本地文件系统

### 11. 测试策略
- **全新项目**: 不需要一致性测试和回滚
- **测试重点**: 按需编写单元测试和集成测试，重点测试核心功能（LLM 工具调用、绘图功能）

## 📝 迁移步骤

### 阶段1: 前端页面迁移（Vue → React）

**目标**: 将现有 Vue 3 页面迁移到 React，保持 UI 和交互逻辑不变

**详细任务**:

1. **项目初始化**
   - 使用 Bun 创建 Next.js 项目
   - 配置 TypeScript
   - 配置 Tailwind CSS
   - 初始化 shadcn/ui

2. **基础组件迁移**
   - 迁移 Navigation 组件
   - 迁移通用 UI 组件（Button, Input, Dialog 等）
   - 配置 Zustand 状态管理
   - 配置路由（Next.js App Router）

3. **页面组件迁移**
   - `HomeView.vue` → `app/page.tsx`
   - `ChatView.vue` → `app/chat/page.tsx`
   - `ActorView.vue` → `app/actor/page.tsx`
   - `MemoryView.vue` → `app/memory/page.tsx`
   - `ContentView.vue` → `app/content/page.tsx`
   - `ModelView.vue` → `app/model/page.tsx`
   - `TaskView.vue` → `app/task/page.tsx`
   - `SettingsView.vue` → `app/settings/page.tsx`
   - `HelpView.vue` → `app/help/page.tsx`
   - `LoginView.vue` → `app/login/page.tsx`

4. **业务组件迁移**
   - ActorCard, ActorDetailDialog
   - CreateDrawTaskDialog, DrawTaskForm
   - ImageGalleryDialog
   - ModelCard, ModelDetailDialog
   - 设置相关组件

5. **状态管理迁移**
   - Pinia → Zustand（使用 persist middleware）
   - 项目状态、认证状态、隐私模式等

**产出**: 可运行的前端页面（使用 Mock 数据，UI 和交互与现有一致）

---

### 阶段2: 核心功能迁移

**目标**: 实现核心业务逻辑的 API 和数据库

**详细任务**:

1. **数据库设计**
   - 设计 Prisma Schema（优化现有架构）
     - 索引优化：所有 `project_id` 外键添加索引
     - 关系设计：使用 Prisma `@relation`
     - 软删除：添加 `deleted_at` 字段
   - 创建数据库迁移
   - 初始化数据库（`storage/data/database.db`）

2. **基础 CRUD API**
   - **项目管理** (`app/api/project/route.ts`)
     - GET `/api/project/all` - 列表
     - GET `/api/project/{id}` - 详情
     - POST `/api/project/create` - 创建
     - PUT `/api/project/{id}` - 更新
     - DELETE `/api/project/{id}` - 删除
   
   - **角色管理** (`app/api/actor/route.ts`)
     - GET `/api/actor/all` - 列表
     - GET `/api/actor/{id}` - 详情
     - POST `/api/actor/create` - 创建
     - PUT `/api/actor/{id}` - 更新
     - DELETE `/api/actor/{id}` - 删除
     - POST `/api/actor/export` - 导出
   
   - **记忆管理** (`app/api/memory/route.ts`)
     - GET `/api/memory/all` - 列表
     - GET `/api/memory/{id}` - 详情
     - POST `/api/memory/create` - 创建
     - PUT `/api/memory/{id}` - 更新
     - DELETE `/api/memory/{id}` - 删除
     - POST `/api/memory/clear` - 批量删除
   
   - **内容管理** (`app/api/content/route.ts`)
     - POST `/api/content/upload` - 文件上传
     - GET `/api/content/line` - 单行查询
     - GET `/api/content/lines` - 批量查询
     - GET `/api/content/chapters` - 章节列表
     - GET `/api/content/chapter/{id}` - 章节详情
     - PUT `/api/content/chapter/{id}` - 更新章节
     - GET `/api/content/stats` - 统计信息
   
   - **摘要管理** (`app/api/summary/route.ts`)
     - GET `/api/summary/all` - 列表
     - POST `/api/summary/create` - 创建
     - PUT `/api/summary/{id}` - 更新
     - DELETE `/api/summary/{id}` - 删除
   
   - **历史记录** (`app/api/history/route.ts`)
     - GET `/api/history/sessions` - 会话列表
     - GET `/api/history/messages` - 消息列表
     - PUT `/api/history/message/{id}` - 更新消息
     - DELETE `/api/history/session/{id}` - 删除会话

3. **SD-Forge 客户端**
   - 实现 WebUIApi TypeScript 版本 (`lib/sd-forge/webuiapi.ts`)
     - txt2img, img2img 方法
     - get_sd_models, get_loras 等查询方法
     - ControlNet 支持
   - 实现绘图 API (`app/api/draw/`)
     - POST `/api/draw/txt2img` - 文本生成图像
     - POST `/api/draw/img2img` - 图像到图像
     - POST `/api/draw/batch` - 批量生成
     - GET `/api/draw/job/{id}` - 查询任务状态
     - GET `/api/draw/models` - 获取模型列表
   - 实现图像缓存系统 (`lib/utils/image-cache.ts`)
     - 内存 LRU 缓存
     - 文件缓存
     - 缓存清理机制

4. **文件服务**
   - POST `/api/file/upload` - 文件上传
   - GET `/api/file/image/{path}` - 图像访问
   - GET `/api/file/line-image/{project_id}/{index}` - 段落图像

**产出**: 完整的 CRUD API 和 SD-Forge 集成，前端可以连接真实后端

---

### 阶段3: LLM 服务和工具调用

**目标**: 实现 AI 对话和工具调用系统

**详细任务**:

1. **LLM 服务实现**
   - LLM 服务基类 (`lib/llm/service.ts`)
     - 抽象基类定义
     - 工具初始化（39个工具函数）
     - 状态图管理（LangGraph）
     - 上下文构建（项目信息、记忆、历史记录）
   - OpenAI 兼容服务 (`lib/llm/openai-service.ts`)
     - 支持 xAI/OpenAI/Anthropic/Google/自定义端点
   - Ollama 服务 (`lib/llm/ollama-service.ts`)
     - 本地模型支持

2. **工具函数实现** (`lib/llm/tools/`)
   - **project-tools.ts**: get_project, update_project
   - **actor-tools.ts**: get_actor, get_all_actors, create_actor, update_actor, remove_actor, add_example, remove_example, add_portrait_from_batch_tool, add_portrait_from_job_tool, get_tag_description, get_all_tag_descriptions
   - **memory-tools.ts**: get_memory, get_all_memories, create_memory, update_memory, delete_memory, clear_memories, get_key_description, get_all_key_descriptions
   - **content-tools.ts**: get_line, get_chapter_lines, get_lines_range, get_chapters, get_chapter, get_stats, get_project_content, update_chapter
   - **draw-tools.ts**: get_loras, get_checkpoints, create_draw_job, create_batch_job, batch_from_jobs, get_draw_job, delete_draw_job, get_image
   - **model-tools.ts**: （模型查询相关）
   - **内部工具**: _add_suggestions, _start_iteration
   - **统一错误处理**: 使用错误处理包装器

3. **LangGraph 集成**
   - 状态图配置（读取工具 vs 写入工具）
   - 工具调用流程
   - 递归限制配置
   - 流式响应实现

4. **聊天 API**
   - POST `/api/chat/invoke` - 直接对话（非流式）
   - POST `/api/chat/stream` - 流式对话（SSE）
   - POST `/api/chat/iteration` - 迭代式对话
   - GET `/api/chat/status/{message_id}` - 消息状态查询

5. **LLM 辅助功能**
   - POST `/api/llm/generate-params` - AI 生成绘图参数
   - POST `/api/llm/extract-actors` - 角色提取
   - POST `/api/llm/bind-images` - 段落图像绑定
   - POST `/api/llm/enhance-desc` - 根据参考图像增强描述

**产出**: 完整的 AI 对话和工具调用系统，支持流式响应和工具调用

---

### 阶段4: 边缘功能迁移

**目标**: 实现辅助功能和配置管理

**详细任务**:

1. **模型元数据**
   - 本地模型扫描 (`app/api/model-meta/scan/route.ts`)
     - 扫描 Checkpoint 模型目录
     - 扫描 LoRA 模型目录
   - Civitai 集成 (`app/api/model-meta/civitai/route.ts`)
     - 重写为 TypeScript，直接调用 Civitai HTTP API
     - 批量导入支持
   - 元数据缓存管理 (`storage/data/model_meta/`)
   - GET `/api/model-meta/models` - 模型列表
   - POST `/api/model-meta/import` - 导入元数据
   - PUT `/api/model-meta/{id}/favorite` - 标记喜爱

2. **认证系统**
   - JWT 实现 (`lib/auth/jwt.ts`)
     - Access Token 生成和验证
     - Refresh Token 管理
   - 密码哈希 (`lib/auth/password.ts`)
     - 使用 bcryptjs
   - 认证 API (`app/api/auth/`)
     - POST `/api/auth/register` - 注册（仅管理员）
     - POST `/api/auth/login` - 登录
     - POST `/api/auth/logout` - 登出
     - POST `/api/auth/refresh` - 刷新令牌
     - GET `/api/auth/me` - 当前用户信息
   - 路由守卫（中间件）
     - 保护需要认证的路由
     - 自动跳转到登录页

3. **配置管理**
   - 配置文件读取 (`lib/config/`)
     - 读取 `storage/config.json`
     - Zod Schema 验证
     - 默认值处理
   - 配置 API (`app/api/settings/`)
     - GET `/api/settings` - 获取配置
     - PUT `/api/settings` - 更新配置
   - 配置热更新支持

4. **帮助文档**
   - GET `/api/help/tools` - 工具说明
   - 帮助页面 (`app/help/page.tsx`)

**产出**: 完整的辅助功能和配置系统

---

### 阶段5: 细节打磨

**目标**: 性能优化、错误处理、用户体验

**详细任务**:

1. **性能优化**
   - 图像缓存优化（LRU 策略调优）
   - 数据库查询优化（添加缺失索引，优化查询语句）
   - 流式响应优化（减少延迟）
   - 前端代码分割和懒加载

2. **错误处理**
   - 统一错误处理中间件
   - 错误日志记录（文件日志）
   - 用户友好的错误提示
   - 错误恢复机制

3. **用户体验**
   - 加载状态优化（骨架屏、进度指示）
   - 错误提示优化（Toast 通知）
   - 交互细节优化（动画、反馈）
   - 响应式布局优化

4. **测试**
   - 核心功能单元测试（工具函数、LLM 服务）
   - API 集成测试（关键 API 端点）
   - 端到端测试（可选，关键流程）

**产出**: 生产就绪的应用

## 🏗 实现细节

### 数据库 Schema 设计要点
- **索引**: 所有 `project_id` 外键添加 `@@index([project_id])`
- **关系**: 使用 Prisma `@relation` 管理外键关系
- **软删除**: 添加 `deletedAt DateTime?` 字段，查询时过滤已删除记录
- **JSON 字段**: 使用 `Json` 类型存储复杂数据结构（如 tags, draw_args）
- **图片存储**: 不需要单独的 Image 表，在需要图片的地方直接存储 MD5 哈希值
- **详细 Schema**: 参见 `prisma/schema.prisma`

### 工具函数实现要点
- **错误处理**: 统一使用 `toolWrapper` 包装，返回 `{ error: string }` 或数据
- **类型定义**: 使用 Zod Schema 定义工具参数和返回值
- **直接访问**: 工具函数直接调用 Prisma 客户端，不需要 Service Layer

### 流式响应实现要点
- **SSE 格式**: 使用 `data: {json}\n\n` 格式发送事件
- **事件类型**: content, tool_start, tool_end, suggest, message_id, status, done, error
- **超时处理**: 设置合理的超时时间（默认 5 分钟）

### 图像缓存实现要点
- **内存缓存**: 使用 `Map` + LRU 算法，限制内存使用
- **文件缓存**: 缓存到 `storage/temp/image-cache/`，使用哈希文件名
- **缓存键生成**: `hash(imagePath + JSON.stringify(processParams))`

### 配置管理实现要点
- **配置文件**: `storage/config.json`，JSON 格式
- **配置 Schema**: 使用 Zod 定义配置结构，验证类型和必填字段
- **热更新**: 通过 API 更新配置后，重新加载配置对象

## 🔗 相关文档

- [Bun 文档](https://bun.sh/docs)
- [Next.js 文档](https://nextjs.org/docs)
- [shadcn/ui 文档](https://ui.shadcn.com/)
- [Zustand 文档](https://zustand-demo.pmnd.rs/)
- [LangChain.js 文档](https://js.langchain.com/)
- [LangGraph.js 文档](https://js.langchain.com/docs/langgraph)
- [Prisma 文档](https://www.prisma.io/docs)
- [Sharp 文档](https://sharp.pixelplumbing.com/)
