import os
import sys
import uvicorn

# Add the current directory to sys.path to handle imports correctly in the restructured layout
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import research
from database.db import init_db

app = FastAPI(title="Company Research Agent API")

# Enable CORS for localhost:5173 (Vite default)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    """Initialize database on startup."""
    init_db()

@app.get("/health")
def health_check():
    """Liveness probe."""
    return {"status": "ok"}

# Include routers
app.include_router(research.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
