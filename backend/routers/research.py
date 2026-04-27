from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict, Optional, Any
import json
from pydantic import BaseModel, Field

# Updated imports for consolidated backend structure
from agent.agent_core import generate_agent_reply, generate_agent_reply_stream
from database.db import get_research_history
from models import AccountPlanModel
from dependencies import validate_session_id

router = APIRouter(prefix="/api")

INJECTION_PATTERNS = [
    "ignore previous", "ignore above", "disregard",
    "forget instructions", "you are now", "act as", 
    "jailbreak"
]

class ResearchRequest(BaseModel):
    user_message: str = Field(..., max_length=500)
    company_name: str
    session_id: str
    chat_history: List[Dict[str, str]]
    current_plan: Optional[Dict[str, Any]] = None

class ResearchResponse(BaseModel):
    reply: str
    plan: Dict[str, Any]
    chat_history: List[Dict[str, Any]]
    diff_result: Dict[str, Any]
    company_name: str

@router.post("/research", response_model=ResearchResponse)
async def perform_research(request: ResearchRequest):
    # Validation against injection patterns
    msg_lower = request.user_message.lower()
    if any(pattern in msg_lower for pattern in INJECTION_PATTERNS):
        raise HTTPException(
            status_code=400, 
            detail="Invalid input detected. Please ask about a real company."
        )

    # Validate session_id
    validate_session_id(request.session_id)

    # Reconstruct AccountPlanModel if provided
    current_plan_model = None
    if request.current_plan:
        try:
            current_plan_model = AccountPlanModel(**request.current_plan)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid plan structure: {str(e)}")

    try:
        # Call existing agent logic
        reply, plan, history, diff_result = await generate_agent_reply(
            user_message=request.user_message,
            company_name=request.company_name,
            current_plan=current_plan_model,
            chat_history=request.chat_history,
            session_id=request.session_id
        )

        return ResearchResponse(
            reply=reply,
            plan=plan.model_dump(),
            chat_history=history,
            diff_result=diff_result,
            company_name=request.company_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/research/stream")
async def perform_research_stream(request: ResearchRequest):
    # Validation against injection patterns
    msg_lower = request.user_message.lower()
    if any(pattern in msg_lower for pattern in INJECTION_PATTERNS):
        raise HTTPException(
            status_code=400, 
            detail="Invalid input detected. Please ask about a real company."
        )

    # Validate session_id
    validate_session_id(request.session_id)

    # Reconstruct AccountPlanModel if provided
    current_plan_model = None
    if request.current_plan:
        try:
            current_plan_model = AccountPlanModel(**request.current_plan)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid plan structure: {str(e)}")

    async def event_generator():
        try:
            async for event in generate_agent_reply_stream(
                user_message=request.user_message,
                company_name=request.company_name,
                current_plan=current_plan_model,
                chat_history=request.chat_history,
                session_id=request.session_id
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/history/{company}/{session_id}")
async def get_history(company: str, session_id: str):
    # Validate session_id
    validate_session_id(session_id)
    
    try:
        history = get_research_history(company, session_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
