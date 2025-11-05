from fastapi import APIRouter, HTTPException
from models.chat import ChatCreate
from services.chat_service import create_chat, get_chat_list, get_chat_history

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/create-chat/{project_id}/{user_id}")
def create(project_id: str, user_id: str, chat: ChatCreate):
    res = create_chat(project_id, chat.message, user_id)
    if not res:
        raise HTTPException(404, "Project not found or unauthorized")
    return res

@router.get("/get-chat-list/{project_id}/{user_id}")
def chat_list(project_id: str, user_id: str):
    res = get_chat_list(project_id, user_id)
    if res is None:
        raise HTTPException(404, "Unauthorized")
    return res

@router.get("/get-chat-history/{project_id}/{chat_id}/{user_id}")
def history(project_id: str, chat_id: str, user_id: str):
    res = get_chat_history(project_id, chat_id, user_id)
    if not res:
        raise HTTPException(404, "Chat not found")
    return res