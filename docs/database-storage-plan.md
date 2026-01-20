# 数据库和图片存储方案

## 📋 概述

采用纯数据库实现，所有结构化数据存储在 SQLite 数据库中。对于无法存储在数据库中的二进制内容（如图片），统一存储在 `storage/data/images/` 目录下，使用 MD5 哈希值作为文件名。

**模板设计**：模板作为一类特殊的角色（`isTemplate = true`），不关联项目（`projectId = null`），用于提供给 LLM 参考绘图参数。模板可以有多个示例（exampleJobs），每个示例代表一个参数变体。

## 🗄️ 数据库设计（Prisma Schema）

### 核心表结构

#### 1. Project（项目表）
```prisma
model Project {
  id              String   @id @default(uuid())
  title           String
  novelPath       String?  // 小说文件路径
  projectPath     String   // 项目路径
  totalLines      Int      @default(0)
  totalChapters   Int      @default(0)
  currentLine     Int      @default(0)
  currentChapter  Int      @default(0)
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt
  deletedAt       DateTime? // 软删除

  // 关联关系
  actors          Actor[]
  memories        Memory[]
  contents        Content[]
  summaries       Summary[]
  chatMessages    ChatMessage[]

  @@index([deletedAt])
}
```

#### 2. Actor（角色表，也用于模板）
```prisma
model Actor {
  id          String   @id @default(uuid())
  projectId   String?  // 项目 ID（模板时为 null）
  name        String
  desc        String
  color       String   // 颜色代码（如 #808080）
  tags        Json?    // 标签（JSON 对象，键值对结构）
  isTemplate  Boolean  @default(false)  // 是否为模板（模板不关联 project）
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  deletedAt   DateTime?

  project     Project? @relation(fields: [projectId], references: [id], onDelete: Cascade)
  exampleJobs Job[]    @relation("ActorExamples")  // 关联的示例任务

  @@index([projectId])
  @@index([name])
  @@index([isTemplate])
  @@index([deletedAt])
}
```

**角色和模板的区别：**
- **角色**：`isTemplate = false`，必须关联 `projectId`，属于特定项目
- **模板**：`isTemplate = true`，`projectId = null`，全局可用，用于 LLM 参考绘图参数

**获取角色示例：**
- 通过 `Job` 表查询，`where source = 'actor_example' and actorId = {actorId}`
- 每个示例是一个完整的 Job 记录，包含 drawArgs 和生成的图片哈希值

**模板的使用：**
- 模板通过 `exampleJobs` 关联多个示例（Job），每个示例代表一个参数变体
- LLM 生成绘图参数时，直接获取所有模板及其示例作为参考
- 例如："白皙少女" 模板可以有多个示例（基础、白裙子、红裙子等）

#### 3. Memory（记忆表）
```prisma
model Memory {
  id          String   @id @default(uuid())
  projectId   String
  key         String   // 记忆键
  value       String   // 记忆值
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  deletedAt   DateTime?

  project     Project  @relation(fields: [projectId], references: [id], onDelete: Cascade)

  @@index([projectId])
  @@index([key])
  @@index([deletedAt])
}
```

#### 4. Content（内容表）
```prisma
model Content {
  id          Int      @id @default(autoincrement())
  projectId   String
  chapter     Int
  line        Int      // 行号
  content     String   // 文本内容
  imageHash   String?  // 关联的图片哈希值（可选）
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  project     Project  @relation(fields: [projectId], references: [id], onDelete: Cascade)

  @@index([projectId])
  @@index([projectId, chapter])
  @@index([projectId, chapter, line])
  @@index([imageHash])
}
```

#### 5. Summary（摘要表）
```prisma
model Summary {
  id          String   @id @default(uuid())
  projectId   String
  content     String   // 摘要内容
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  deletedAt   DateTime?

  project     Project  @relation(fields: [projectId], references: [id], onDelete: Cascade)

  @@index([projectId])
  @@index([deletedAt])
}
```

#### 6. ChatMessage（聊天消息表）
```prisma
model ChatMessage {
  id          String   @id @default(uuid())
  projectId   String?
  index       Int      // 消息索引
  status      String   // 状态：pending, ready, error
  messageType String   // 类型：normal, thinking, tool
  role        String   // 角色：user, assistant, system
  context     String   // 消息内容
  tools       Json     // 工具调用记录
  suggests    Json     // 建议
  data        Json     // 额外数据
  createdAt   DateTime @default(now())

  project     Project? @relation(fields: [projectId], references: [id], onDelete: Cascade)

  @@index([projectId])
  @@index([index])
  @@index([status])
}
```

#### 7. DrawArgs（绘图参数表）
```prisma
model DrawArgs {
  id            String   @id @default(uuid())
  model         String   // 模型名称
  prompt        String   // 提示词
  negativePrompt String? // 负面提示词
  steps         Int      @default(30)
  cfgScale      Float    @default(7.0)
  sampler       String?  // 采样器
  seed          Int?     // 种子，-1 表示随机
  width         Int      @default(1024)
  height        Int      @default(1024)
  clipSkip      Int?     // CLIP skip
  vae           String?  // VAE
  loras         Json?    // LoRA 配置（键值对）
  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt

  jobs          Job[]

  @@index([model])
  @@index([sampler])
}
```

#### 8. Job（绘图任务表）
```prisma
model Job {
  id            String   @id @default(uuid())
  name          String?
  desc          String?
  status        String   // pending, completed, failed
  source        String   // 来源：batch, single, actor_portrait, actor_example, model_example
  drawArgsId    String   // 绘图参数 ID
  results       String[] @default([]) // 结果列表（始终是列表，未完成时为空列表）
  expectedCount Int?     // 预期数量（批量任务时使用，单个任务为 null）
  actorId       String?  // 关联的角色 ID（如果是角色相关任务）
  modelMetaId   Int?     // 关联的模型元数据 ID（如果是模型示例）
  createdAt     DateTime @default(now())
  completedAt   DateTime?

  drawArgs      DrawArgs @relation(fields: [drawArgsId], references: [id])
  actor         Actor?   @relation("ActorExamples", fields: [actorId], references: [id])
  modelMeta     ModelMeta? @relation(fields: [modelMetaId], references: [versionId])

  @@index([status])
  @@index([source])
  @@index([drawArgsId])
  @@index([actorId])
  @@index([modelMetaId])
}
```

**source 字段说明：**
- `batch`: 批量任务
- `single`: 单点任务
- `actor_portrait`: 角色立绘生成
- `actor_example`: 角色示例图片
- `model_example`: 模型示例图片

**results 字段说明：**
- 始终是 `String[]` 类型，统一表示结果列表
- 未完成：`[]`（空列表）
- 单个任务完成：`["hash1"]`（一个元素的列表）
- 批量任务完成：`["hash1", "hash2", "hash3"]`（多个元素的列表）
- 部分失败：直接标记 `status = 'failed'`，不存储部分结果

**expectedCount 字段说明：**
- 单个任务：`null`（不需要预期数量）
- 批量任务：设置预期数量，如 `8`（表示要生成 8 张图片）
- 进度跟踪：`results.length / expectedCount`


#### 9. ModelMeta（模型元数据表）
```prisma
model ModelMeta {
  versionId   Int      @id @default(autoincrement())
  filename    String
  name        String
  version     String
  desc        String?
  modelId     Int
  type        String   // checkpoint, lora
  ecosystem   String   // sdxl, pony, illustrious
  baseModel   String?
  sha256      String   // 文件 SHA-256（用于文件完整性校验）
  trainedWords Json?   // 训练关键词（数组结构，但内容灵活，保持 Json）
  url         String?
  webPageUrl  String?
  preference  String?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  exampleJobs Job[]    // 关联的示例任务

  @@unique([versionId])
  @@index([modelId])
  @@index([type])
  @@index([ecosystem])
  @@index([name, version])
}
```

**获取模型示例：**
- 通过 `Job` 表查询，`where source = 'model_example' and modelMetaId = {versionId}`
- 每个示例是一个完整的 Job 记录，包含 drawArgs 和生成的图片哈希值

#### 10. User（用户表）
```prisma
model User {
  id          String   @id @default(uuid())
  username    String   @unique
  password    String   // bcrypt 哈希
  isAdmin     Boolean  @default(false)
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}
```

## 🖼️ 图片存储方案

### 设计原则

1. **统一存储位置**：所有图片存储在 `storage/data/images/` 目录下
2. **MD5 哈希命名**：使用 MD5 哈希值作为文件名，格式：`{hash}.{ext}`
3. **去重机制**：相同内容的图片只存储一份（相同内容 = 相同 MD5）
4. **直接存储哈希值**：在需要图片的地方（Actor.examples, Content.imageHash, Job.data 等）直接存储哈希值字符串

### 为什么选择 MD5？

1. **性能优势**：MD5 计算速度比 SHA-256 快约 2-3 倍，对于大量图片处理更友好
2. **文件名长度**：MD5 生成 32 个字符，SHA-256 生成 64 个字符，更短的文件名更易管理
3. **足够安全**：对于图片去重场景，MD5 的碰撞概率极低（2^128），完全满足需求
4. **广泛支持**：所有编程语言和工具都原生支持 MD5

**注意**：如果未来需要密码学级别的安全性（如文件完整性校验），可以在 ModelMeta 表中使用 SHA-256（已包含 sha256 字段）。

### 文件路径结构

```
storage/
├── data/
│   ├── database.db           # SQLite 数据库
│   ├── images/               # 统一图片存储目录
│   │   ├── a1b2c3d4e5f6...png
│   │   ├── b2c3d4e5f6a1...jpg
│   │   └── ...
│   ├── model_meta/           # 模型元数据缓存
│   └── projects/             # 项目相关文件（如小说文件）
└── temp/                      # 临时文件
    └── image-cache/          # 处理后的图片缓存
```

### 图片存储工具函数

**文件位置**：`lib/utils/image.ts`

主要函数：
- `saveImage(buffer, options?)` - 保存图片，返回哈希值和元数据
- `getImage(hash, mimeType?)` - 根据哈希值读取图片
- `imageExists(hash, mimeType?)` - 检查图片是否存在
- `deleteImage(hash, mimeType?)` - 删除图片文件
- `getImageUrl(hash, mimeType?)` - 获取图片访问 URL

详细实现参见 `lib/utils/image.ts`

### 图片使用场景

#### 1. 创建模板

模板是一类特殊的角色，用于 LLM 参考绘图参数：

```typescript
// 创建模板（不关联项目）
const template = await prisma.actor.create({
  data: {
    name: "白皙少女",
    desc: "用于生成白皙少女角色的参考模板",
    color: "#FFFFFF",
    isTemplate: true,  // 标记为模板
    projectId: null,  // 模板不关联项目
  }
});

// 为模板创建示例（参数变体）
const drawArgs = await prisma.drawArgs.create({
  data: {
    model: "WAI-illustrious-SDXL-v15.0",
    prompt: "1girl, fair skin, beautiful, ...",
    // ... 其他参数
  }
});

const exampleJob = await prisma.job.create({
  data: {
    name: "基础",
    status: "completed",
    source: "actor_example",
    drawArgsId: drawArgs.id,
    actorId: template.id,
    results: [imageHash],  // 示例图片哈希值
  }
});
```

#### 2. Actor 示例图片

在创建或更新 Actor 时，保存示例图片：

```typescript
// 创建绘图参数
const drawArgs = await prisma.drawArgs.create({
  data: {
    model: "WAI-illustrious-SDXL-v15.0",
    prompt: "...",
    negativePrompt: "...",
    // ... 其他参数
  }
});

// 创建任务（标记为 actor_example）
const job = await prisma.job.create({
  data: {
    name: "示例标题",
    desc: "示例描述",
    status: "pending",
    source: "actor_example",
    drawArgsId: drawArgs.id,
    actorId: actorId,
    results: [],  // 未完成时为空列表
  }
});

// 任务完成后，保存图片并更新任务
const imageInfo = await saveImage(imageBuffer);
await prisma.job.update({
  where: { id: job.id },
  data: {
    status: "completed",
    results: [imageInfo.hash],  // 存储图片哈希值列表
    completedAt: new Date(),
  }
});
```

#### 3. Content 段落图片

在绑定段落图片时：

```typescript
// 保存图片
const imageInfo = await saveImage(imageBuffer);
const hash = imageInfo.hash;

// 更新 Content 记录
await prisma.content.update({
  where: { id: contentId },
  data: {
    imageHash: hash  // 直接存储哈希值
  }
});
```

#### 4. Job 生成的图片

**单个任务完成：**
```typescript
// 保存生成的图片
const imageInfo = await saveImage(imageBuffer);
const hash = imageInfo.hash;

// 更新 Job 的 results 字段
await prisma.job.update({
  where: { id: jobId },
  data: {
    status: 'completed',
    results: [hash],  // 单个任务：一个元素的列表
    completedAt: new Date(),
  }
});
```

**批量任务完成：**
```typescript
// 批量生成图片
const hashes: string[] = [];
for (const imageBuffer of imageBuffers) {
  const imageInfo = await saveImage(imageBuffer);
  hashes.push(imageInfo.hash);
}

// 更新 Job 的 results 字段
await prisma.job.update({
  where: { id: jobId },
  data: {
    status: 'completed',
    results: hashes,  // 批量任务：多个元素的列表
    completedAt: new Date(),
  }
});
```

**批量任务创建：**
```typescript
// 创建批量任务
const job = await prisma.job.create({
  data: {
    name: "批量生成8张图片",
    status: "pending",
    source: "batch",
    drawArgsId: drawArgs.id,
    results: [],  // 未完成时为空列表
    expectedCount: 8,  // 预期生成8张图片
  }
});
```

#### 5. 图片访问 API

**文件位置**：`app/api/file/image/[hash]/route.ts`

**使用方式**：
- 前端访问：`/api/file/image/{hash}?mimeType=image/png`
- 或直接使用：`/api/file/image/{hash}`（会自动检测扩展名）

**响应头**：
- `Content-Type`: 图片 MIME 类型
- `Cache-Control`: `public, max-age=31536000, immutable`（缓存 1 年）

## 🔄 数据迁移方案

### 从旧版迁移图片

1. **扫描旧版图片目录**：
   - `storage/data/projects/{project_id}/actors/{actor_name}/` 下的所有图片

2. **处理每张图片**：
   - 读取图片文件
   - 计算 MD5 哈希值
   - 移动到 `storage/data/images/{hash}.{ext}`
   - 更新数据库中的引用（Actor.examples, Content.imageHash 等）

3. **迁移脚本示例**：
```typescript
// scripts/migrate-images.ts
import { saveImage } from '@/lib/utils/image';
import fs from 'fs/promises';
import path from 'path';

async function migrateImages() {
  const oldProjectsDir = path.join(process.cwd(), 'storage', 'data', 'projects');
  const projects = await fs.readdir(oldProjectsDir);
  
  for (const projectId of projects) {
    const actorsDir = path.join(oldProjectsDir, projectId, 'actors');
    // ... 遍历所有图片并迁移
  }
}
```

## ✅ 方案优势

1. **简单直接**：不需要额外的 Image 表，直接在需要的地方存储哈希值
2. **自动去重**：相同内容的图片只存储一份，节省空间
3. **快速查询**：通过哈希值快速定位文件，无需遍历目录
4. **易于管理**：所有图片集中存储，便于备份和清理
5. **性能优化**：MD5 计算速度快，适合大量图片处理
6. **扩展性好**：未来可以轻松添加图片元数据（如标签、描述）到对应的 JSON 字段中

## 📝 注意事项

1. **文件清理**：删除数据时，需要检查图片是否还有其他引用，避免误删
2. **备份策略**：定期备份 `storage/data/images/` 目录
3. **文件完整性**：虽然 MD5 可以检测文件是否损坏，但对于关键文件（如模型文件），仍使用 SHA-256
4. **扩展名处理**：如果不知道 MIME 类型，需要尝试多个扩展名或从数据库查询
5. **Json 字段使用**：
   - `Actor.tags`: 保持 Json（键值对结构，灵活）
   - `DrawArgs.loras`: 保持 Json（LoRA 配置键值对）
   - `ModelMeta.trainedWords`: 保持 Json（数组结构，但内容灵活）
   - `ChatMessage.tools/suggests/data`: 保持 Json（结构复杂且可能变化）
   - `Job.results`: 改为 `String[]`（统一为列表，单个任务 `["hash"]`，批量任务 `["hash1", "hash2", ...]`）
   - `Actor.examples`: 改为通过 Job 表关联（规范化）
   - `ModelMeta.examples`: 改为通过 Job 表关联（规范化）
   - `Job.drawArgs`: 改为独立表 `DrawArgs`（规范化）
   - 不需要 `BatchJob` 表：批量任务就是一个 Job，通过 `expectedCount` 和 `results.length` 跟踪进度

6. **模板设计**：
   - 模板作为特殊的角色：`Actor.isTemplate = true`
   - 模板不关联项目：`Actor.projectId = null`
   - 模板可以有多个示例（exampleJobs），每个示例代表一个参数变体
   - LLM 生成绘图参数时，直接获取所有模板及其示例作为参考

## 🚀 快速开始

### 1. 安装依赖

```bash
bun install
```

### 2. 初始化数据库

```bash
# 生成 Prisma 客户端
bun run db:generate

# 推送 Schema 到数据库（开发环境）
bun run db:push

# 或使用迁移（生产环境）
bun run db:migrate
```

### 3. 使用图片工具

```typescript
import { saveImage, getImageUrl } from '@/lib/utils/image';

// 保存图片
const imageInfo = await saveImage(imageBuffer);
const hash = imageInfo.hash;  // 存储到数据库

// 获取图片 URL（用于前端显示）
const imageUrl = getImageUrl(hash, imageInfo.mimeType);
```

### 4. 使用模板

```typescript
// 获取所有模板（用于 LLM 参考）
const templates = await prisma.actor.findMany({
  where: {
    isTemplate: true,
    deletedAt: null,
  },
  include: {
    exampleJobs: {
      include: {
        drawArgs: true,
      },
      where: {
        status: 'completed',
      },
    },
  },
});

// LLM 生成绘图参数时，直接使用模板的 drawArgs 作为参考
// 模板的 exampleJobs 提供了多个参数变体供 LLM 选择
```
