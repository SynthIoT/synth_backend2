# routers/ai_router.py
from fastapi import APIRouter, HTTPException
from models.ai import ParseRequest
from services.ai_service import parse_and_respond

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/parse")
def parse_endpoint(req: ParseRequest):
    if not req.prompt:
        raise HTTPException(status_code=400, detail="Prompt required")
    res = parse_and_respond(req.prompt)
    return res