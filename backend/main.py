from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import research
from database.db import init_db

app = FastAPI(title="Company Research Agent API")

# Enable CORS for localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
