from utils.firebase import db
import time

def create_chat(project_id: str, message: str, user_id: str):
    # Verify project belongs to user
    proj = db.collection('projects').document(project_id).get()
    if not proj.exists or proj.to_dict()['user_id'] != user_id:
        return None

    chat_ref = db.collection('projects').document(project_id).collection('chats').document()
    chat_ref.set({
        'messages': [
            {"role": "user", "content": message, "timestamp": time.time()}
        ],
        'created_at': firestore.SERVER_TIMESTAMP
    })
    return {"chat_id": chat_ref.id, "message": message}

def get_chat_list(project_id: str, user_id: str):
    proj = db.collection('projects').document(project_id).get()
    if not proj.exists or proj.to_dict()['user_id'] != user_id:
        return None
    chats = db.collection('projects').document(project_id).collection('chats').stream()
    return [{"chat_id": c.id, "preview": (c.to_dict().get('messages') or [{}])[0].get('content', '')[:50]} for c in chats]

def get_chat_history(project_id: str, chat_id: str, user_id: str):
    proj = db.collection('projects').document(project_id).get()
    if not proj.exists or proj.to_dict()['user_id'] != user_id:
        return None
    chat_ref = db.collection('projects').document(project_id).collection('chats').document(chat_id)
    chat = chat_ref.get()
    if not chat.exists:
        return None
    return {"chat_id": chat_id, "messages": chat.to_dict().get('messages', [])}