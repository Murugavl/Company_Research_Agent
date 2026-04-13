# Company Intelligence Research Agent

A powerful, distributed AI agent designed to perform deep-dive company research, competitor analysis, and strategic opportunity identification.

## 🚀 Project Overview

This application leverages **LangGraph** to orchestrate a sophisticated research workflow. It performs real-time web searching, structured data extraction, and quality-controlled merging to produce comprehensive intelligence reports.

### ✨ Key Features
- **Deterministic Orchestration**: Uses LangGraph StateGraph for reliable, traceable AI workflows.
- **Real-time Intelligence**: Integrates Tavily Search for up-to-the-minute company data.
- **Structured Reporting**: Automatically generates deep-dive reports across 9 strategic sections.
- **Delta Analysis**: Detects and highlights changes between research sessions.
- **Modern UI**: A premium React-based dashboard with real-time chat and structured data views.

## 🛠️ Tech Stack

### Backend (`/backend`)
- **FastAPI**: High-performance Python API framework.
- **LangGraph**: Workflow orchestration for the research agent.
- **Groq (Llama 3)**: High-speed LLM inference.
- **Redis**: Distributed caching for search results.
- **SQLite**: Local persistence for research history.

### Frontend (`/frontend`)
- **React 18**: Modern UI library.
- **Vite**: Ultra-fast build tool and dev server.
- **Tailwind CSS**: Utility-first styling with dark mode support.
- **Lucide React**: Premium iconography.

## 🏁 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker (for Redis)

### Quick Start (Local)

1.  **Start Redis**:
    ```bash
    docker run -d -p 6379:6379 redis:7-alpine
    ```

2.  **Configure Backend**:
    - Go to `backend/`
    - Create `.env` from `.env.example`
    - Add your `GROQ_API_KEY` and `TAVILY_API_KEY`
    - Install dependencies: `pip install -r requirements.txt`
    - Start server: `python -m uvicorn main:app --reload` (from root using `$env:PYTHONPATH="."`)

3.  **Configure Frontend**:
    - Go to `frontend/`
    - Install dependencies: `npm install`
    - Start dev server: `npm run dev`

Visit `http://localhost:5173` to start researching.

## 📁 Project Structure
```text
Company_Research_Agent/
├── backend/            # Python FastAPI & Agent logic
│   ├── agent/          # LangGraph definitions
│   ├── database/       # SQLite & logic
│   ├── routers/        # API endpoints
│   └── .env            # Private keys
├── frontend/           # React + Vite frontend
│   ├── src/            # Components & App logic
│   └── tailwind.config.js
└── docker-compose.yml  # Full stack orchestration
```
