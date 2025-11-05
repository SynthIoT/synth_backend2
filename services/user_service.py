from utils.firebase import db, auth
from models.user import UserCreate, UserLogin
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(user_data: UserCreate):
    # Create Auth user
    auth_user = auth.create_user(email=user_data.email, password=user_data.password)
    hashed_pw = hash_password(user_data.password)
    
    # Store in Firestore
    user_ref = db.collection('users').document(auth_user.uid)
    user_ref.set({
        'uid': auth_user.uid,
        'name': user_data.name,
        'email': user_data.email,
        'password_hash': hashed_pw
    })
    return {"uid": auth_user.uid, "name": user_data.name, "email": user_data.email}

def login_user(login: UserLogin):
    try:
        # Verify via Firestore (since we store hash)
        users_ref = db.collection('users').where('email', '==', login.email).stream()
        for user_doc in users_ref:
            user = user_doc.to_dict()
            if user['password_hash'] == hash_password(login.password):
                return {"uid": user['uid'], "name": user['name'], "email": user['email']}
        return None
    except:
        return None

def update_user(uid: str, name: str = None, password: str = None):
    user_ref = db.collection('users').document(uid)
    update_data = {}
    if name:
        update_data['name'] = name
    if password:
        update_data['password_hash'] = hash_password(password)
        auth.update_user(uid, password=password)
    if update_data:
        user_ref.update(update_data)
    return {"message": "Updated"}