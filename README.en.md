# ComicForge

English | [中文](README.md)

AI-powered novel-to-comic tool: FastAPI + Vue 3 frontend-backend separation, integrating LLM chat, SD image generation, and model management.

## ✨ Core Features

### 🤖 AI Dialogue System
- **Multi-Provider**: OpenAI / xAI (Grok) / Ollama / Anthropic / Google / Custom endpoints
- **Dual Modes**: invoke (direct) and stream (SSE streaming)
- **Tool Calling**: Based on LangChain + LangGraph, 43+ MCP tools (project, actor, memory, novel, draw, etc.)
- **Session Management**: Multi-session support, SQLite persistence, auto-summarization
- **Iteration Mode**: Batch process chapter content

### 🎨 Image Generation
- **Local Generation**: Connect to SD-Forge/sd-webui (LoRA/model switching)
- **Civitai Integration**: Model metadata import (AIR identifier)
- **Task Management**: Batch create (1-16), status tracking, image preview
- **AI Parameter Generation**: LLM auto-generates drawing parameters

### 📦 Model Metadata
- **Local Scan**: Auto-scan Checkpoint/LoRA
- **Civitai Integration**: Fetch example images, parameters, descriptions
- **Filter/Favorite**: Filter by ecosystem/base model, mark common models
- **Privacy Mode**: Hide preview images

### 👥 Actor Management
- **Create/Edit**: Support actors, locations, organizations
- **Tag System**: Predefined tags (appearance, clothing, personality, etc.)
- **Portrait Generation**: Dual modes (create new task / select existing task)
- **Example Images**: Multi-image upload, auto-cleanup

### 🧠 Memory & Novel
- **Memory System**: Key-value storage, predefined keys, batch operations
- **Novel Reading**: Single/batch/chapter reading, summary generation

## 🗂 Project Structure

```
ComicForge/
├── src/
│   ├── api/                      # Backend FastAPI
│   │   ├── main.py               # App entry
│   │   ├── routers/              # API routes (14)
│   │   │   ├── chat.py           # Chat (invoke/stream/iteration)
│   │   │   ├── draw.py           # Draw tasks
│   │   │   ├── model_meta.py     # Model metadata
│   │   │   ├── actor.py          # Actor management
│   │   │   ├── project.py        # Project management
│   │   │   ├── memory.py         # Memory management
│   │   │   ├── novel.py          # Novel content
│   │   │   ├── reader.py         # Content reader
│   │   │   ├── history.py        # Session history
│   │   │   ├── llm.py            # LLM related
│   │   │   ├── settings.py       # Settings
│   │   │   ├── file.py           # File service
│   │   │   └── help.py           # Help docs
│   │   ├── services/             # Business services
│   │   │   ├── db/               # Database (SQLModel)
│   │   │   │   ├── base.py       # DB initialization
│   │   │   │   ├── history_service.py    # Session/message
│   │   │   │   ├── project_service.py    # Project
│   │   │   │   ├── actor_service.py      # Actor
│   │   │   │   ├── memory_service.py     # Memory
│   │   │   │   ├── novel_service.py      # Novel
│   │   │   │   ├── draw_service.py       # Draw tasks
│   │   │   │   └── summary_service.py    # Summary
│   │   │   ├── llm/              # LLM services
│   │   │   │   ├── base.py       # Base class (LangGraph)
│   │   │   │   ├── openai.py     # OpenAI compatible
│   │   │   │   └── ollama.py     # Ollama
│   │   │   ├── draw/             # Draw services
│   │   │   │   ├── sd_forge.py   # SD-Forge
│   │   │   │   └── civitai.py    # Civitai
│   │   │   ├── model_meta/       # Model metadata
│   │   │   │   ├── local.py      # Local scan
│   │   │   │   └── civitai.py    # Civitai fetch
│   │   │   ├── novel_parser.py   # Novel parser
│   │   │   └── transform.py      # Data transform
│   │   ├── schemas/              # Pydantic models
│   │   ├── constants/            # Constants
│   │   ├── settings/             # Config classes
│   │   └── utils/                # Utilities
│   │
│   ├── views/                    # Vue views (9)
│   │   ├── ChatView.vue          # Chat interface
│   │   ├── TaskView.vue          # Task management
│   │   ├── ModelView.vue         # Model management
│   │   ├── ActorView.vue         # Actor management
│   │   ├── MemoryView.vue        # Memory management
│   │   ├── ContentView.vue       # Content management
│   │   ├── HomeView.vue          # Home
│   │   ├── SettingsView.vue      # Settings
│   │   └── HelpView.vue          # Help
│   ├── components/               # Vue components
│   ├── router/                   # Router config
│   ├── stores/                   # Pinia state
│   ├── utils/                    # Frontend utils
│   └── api/                      # Axios client
│
├── storage/                      # Data storage
│   └── data/
│       ├── database.db           # SQLite
│       ├── model_meta/           # Model cache
│       └── projects/             # Project data
├── tests/                        # Tests
├── scripts/                      # Scripts
├── docker-compose.yml            # Docker orchestration
├── Dockerfile.backend            # Backend image
├── Dockerfile.frontend           # Frontend image
├── config.json                   # Config file
├── package.json                  # Frontend deps
└── pyproject.toml                # Backend deps
```

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

```bash
# 1. Clone project
git clone <repository-url>
cd ComicForge

# 2. Configure environment (optional)
cp .env.example .env
# Edit .env file, add API Keys

# 3. Start services
docker-compose up -d

# 4. Access application
# Frontend: http://localhost:7863
# Backend API: http://localhost:7864/docs
```

**Docker Features**:
- Auto-build frontend/backend images
- Data persistence (`./storage` directory)
- Environment variable support
- Health check and auto-restart

### Option 2: Local Development

**Requirements**: Node.js 18+ / Python 3.13+

```bash
# 1. Install dependencies
pnpm install          # Frontend
uv sync               # Backend

# 2. Start backend (port 7864)
uv run uvicorn api.main:app --reload --app-dir src
# Or use optimized script: scripts/dev-server.bat (Windows) / scripts/dev-server.sh (Linux/Mac)

# 3. Start frontend (port 7863)
pnpm dev

# 4. Access
# Frontend: http://localhost:7863
# API docs: http://localhost:7864/docs
```

### Configuration

**Priority**: Environment variables > `config.json` > Defaults

```bash
# Environment variable example
export OPENAI_API_KEY="sk-..."
export XAI_API_KEY="xai-..."
export CIVITAI_API_TOKEN="..."
```

Or configure in `config.json`:
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

You can also configure directly in the web "Settings" page.

## 🏗 Technical Architecture

### Frontend (Vue 3 + TypeScript)
- **Build Tool**: Vite (rolldown)
- **UI Framework**: Tailwind CSS + Headless UI
- **State Management**: Pinia (project/theme/connection/navigation/privacy)
- **Router**: Vue Router
- **HTTP**: Axios (dev proxy `/api` → backend)
- **Markdown**: marked + highlight.js
- **Cache**: localStorage (image/state persistence)

### Backend (FastAPI + Python 3.13)
- **Web Framework**: FastAPI
- **Database**: SQLite + SQLModel
- **LLM**: LangChain + LangGraph (state graph)
- **Tool System**: fastapi-mcp (43+ MCP tools)
- **HTTP Client**: httpx
- **Image Generation**: SD-Forge API / Civitai API
- **Logging**: loguru

### Main API Endpoints
- `/chat/*` - Chat (invoke/stream/iteration)
- `/draw/*` - Draw tasks (CRUD/batch/status)
- `/model-meta/*` - Model metadata (scan/import)
- `/actor/*` - Actor management
- `/project/*` - Project management
- `/memory/*` - Memory management
- `/novel/*` - Novel content
- `/history/*` - Session history
- `/settings/*` - Config management
- `/health` - Health check

## 📝 Development Guide

### Project Features
- **Frontend-Backend Separation**: Clear architecture, independent development/deployment
- **Type Safety**: Full type hints (TypeScript + Python)
- **Modular Design**: Layered architecture (Router → Service → DB)
- **Async Processing**: async/await + SSE streaming
- **State Management**: LangGraph state graph + Pinia frontend state
- **Tool Ecosystem**: 43+ MCP tools, extensible

## 🧪 Testing

```bash
# Run all tests
uv run pytest tests/

# Run specific test
uv run pytest tests/api/test_chat.py -v

# Test coverage
uv run pytest tests/ --cov=src/api --cov-report=html
```

**Coverage**: Chat (invoke/stream/iteration), tool calling, session management, project CRUD, message status query

## 📊 Feature Status

### ✅ Core Features (Completed)
- **Backend**: 14 API routes, SQLite database, LangChain + LangGraph tool calling
- **Frontend**: 9 Vue views, Pinia state management, Axios HTTP client
- **AI Chat**: invoke/stream/iteration modes, 43+ MCP tools
- **Image Generation**: SD-Forge local generation, Civitai integration, batch task management
- **Model Management**: Local scan, Civitai metadata import, filter/favorite
- **Actor Management**: Create/edit, tag system, portrait generation (dual modes)
- **Deployment**: Docker Compose containerization, health check, auto-restart

### 🚧 Continuous Improvement
- Frontend performance optimization (virtual scrolling)
- Test coverage improvement
- Error handling enhancement

## 📄 License

See [LICENSE](LICENSE)
