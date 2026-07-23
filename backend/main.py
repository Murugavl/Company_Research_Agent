import os
import sys
import uvicorn

# Add the current directory to sys.path to handle imports correctly in the restructured layout
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import research
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="Company Research Agent API", lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000", 
        "https://company-research-agent-s3ib.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """Root endpoint."""
    return {"status": "Company Research Agent API is running", "message": "Welcome!"}

@app.get("/health")
def health_check():
    """Liveness probe."""
    return {"status": "ok"}

# Include routers
app.include_router(research.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
