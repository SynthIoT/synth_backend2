# services/chat_service.py
from utils.firebase import db
from services.ai_service import parse_and_respond
import time
from typing import List

def create_chat(project_id: str, user_id: str, first_message: str):
    # ownership check …
    chat_ref = (
        db.collection("projects")
        .document(project_id)
        .collection("chats")
        .document()
    )
    chat_ref.set(
        {
            "created_at": time.time(),
            "name": first_message,                    
            "messages": [
                {"role": "user", "content": first_message, "timestamp": time.time()}
            ],
        }
    )
    return {"chat_id": chat_ref.id}


def get_chat_list(project_id: str, user_id: str):
    # ownership check …
    chats = (
        db.collection("projects")
        .document(project_id)
        .collection("chats")
        .order_by("created_at", direction="DESCENDING")
        .stream()
    )
    result = []
    for c in chats:
        data = c.to_dict()
        preview = data.get("name") or (data.get("messages") or [{}])[0].get("content", "")[:60]
        result.append({"chat_id": c.id, "preview": preview})
    return result


def get_chat_history(project_id: str, chat_id: str, user_id: str):
    # ownership check …
    doc = (
        db.collection("projects")
        .document(project_id)
        .collection("chats")
        .document(chat_id)
        .get()
    )
    if not doc.exists:
        return None
    data = doc.to_dict()
    return {"messages": data.get("messages", [])}


# ------------------------------------------------------------------
# 4. Send a new user message → run AI → store both
# ------------------------------------------------------------------
def send_message(project_id: str, chat_id: str, user_id: str, user_prompt: str):
    # ---- verify ownership -------------------------------------------------
    proj = db.collection("projects").document(project_id).get()
    if not proj.exists or proj.to_dict().get("user_id") != user_id:
        return None

    chat_ref = (
        db.collection("projects")
        .document(project_id)
        .collection("chats")
        .document(chat_id)
    )
    doc = chat_ref.get()
    if not doc.exists:
        return None

    # ---- append user message ------------------------------------------------
    messages: List[dict] = doc.to_dict().get("messages", [])
    messages.append(
        {"role": "user", "content": user_prompt, "timestamp": time.time()}
    )

    # ---- call your AI parser ------------------------------------------------
    try:
        ai_result = parse_and_respond(user_prompt)
        ai_message = ai_result["message"]
    except Exception as e:
        ai_message = "Sorry, I couldn't understand that request."

    # ---- append AI reply ----------------------------------------------------
    messages.append(
        {"role": "assistant", "content": ai_message, "timestamp": time.time()}
    )

    # ---- write back ---------------------------------------------------------
    chat_ref.update({"messages": messages})
    return {"messages": messages[-2:]}  