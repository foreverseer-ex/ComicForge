# ComicForge

English | [中文](README.md)

**AI-Powered Novel Creation & Visualization Tool**. Built-in intelligent chat, image generation, and model management with modern frontend-backend separation architecture.

## ✨ Overview

- **AI Chat**: Multi-provider (OpenAI / xAI / Ollama / Anthropic / Google), streaming output, history auto-save, tool calling.
- **Image Generation**: SD-Forge local and Civitai cloud (basic), AIR identifier import, metadata caching.
- **Model Management**: Auto-scan local models (Checkpoint/LoRA/VAE), filter by ecosystem (SD1/SD2/SDXL).
- **Infrastructure**: Vue 3 + TypeScript frontend, FastAPI backend, SQLModel(SQLite), modern UI with Tailwind CSS + Headless UI + shadcn/ui.

## 🚀 Quick Start

- **Requirements**: 
  - Node.js 18+ (for frontend)
  - Python 3.13+ (for backend)
  - Optional: SD-Forge/sd-webui (for local image generation)

### Install Dependencies

#### Backend

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

#### Frontend

```bash
# Using pnpm (recommended)
pnpm install

# Or using npm
npm install

# Or using yarn
yarn install
```

### Run Application

#### Start Backend

```bash
# Development mode (auto-reload)
uv run uvicorn api.main:app --reload --host 127.0.0.1 --port 7864 --app-dir src

# Production mode
uv run uvicorn api.main:app --host 127.0.0.1 --port 7864 --app-dir src
```

Backend API Documentation:
- **Swagger UI**: http://127.0.0.1:7864/docs
- **ReDoc**: http://127.0.0.1:7864/redoc

#### Start Frontend

```bash
# Development mode
pnpm dev

# Or using npm
npm run dev

# Build for production
pnpm build

# Preview production build
pnpm preview
```

Frontend runs on: http://127.0.0.1:7863

**Note**: Both frontend and backend services need to be running simultaneously.

## ⚙️ Configuration

- **Environment variables (recommended)**:

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

- **config.json (optional)** in project root:

```json
{
  "llm": {"provider": "xai", "api_key": "your-key", "model": "grok-beta"},
  "sd_forge": {"base_url": "http://127.0.0.1:7860", "home": "C:\\path\\to\\sd-webui-forge"},
  "civitai": {"api_token": "optional-token"}
}
```

Priority: Env vars > Config file > Defaults. Visual config with auto-save is available in-app on the "Settings" page.

## 📁 Structure

```
ComicForge/
├── src/
│   ├── api/           # Backend FastAPI service
│   │   ├── routers/   # API routes: project/actor/memory/reader/novel/draw/llm/chat/history/file
│   │   ├── services/  # Business logic: llm/draw/model_meta/db/chat
│   │   ├── schemas/   # Pydantic models
│   │   ├── settings/  # Configuration
│   │   └── utils/     # Utilities
│   ├── App.vue        # Vue root component
│   ├── main.ts        # Frontend entry
│   ├── components/    # Vue components
│   └── style.css      # Global styles
├── package.json       # Frontend dependencies
├── pyproject.toml     # Backend dependencies
├── vite.config.ts     # Vite configuration
└── tsconfig.json      # TypeScript configuration
```

## 🔌 API Service

ComicForge provides a FastAPI-based RESTful API service. The frontend accesses all features through HTTP API.

### Main Routes

- `/project/*` - Project management
- `/actor/*` - Actor management
- `/memory/*` - Memory management
- `/reader/*` - Content reading
- `/novel/*` - Novel content
- `/draw/*` - Image generation
- `/llm/*` - LLM functionality
- `/chat/*` - Chat conversations
- `/history/*` - History records
- `/file/*` - File services

## 📄 License

See [LICENSE](LICENSE)
