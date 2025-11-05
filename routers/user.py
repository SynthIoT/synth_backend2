from fastapi import APIRouter, HTTPException
from models.user import UserCreate, UserLogin, UserUpdate
from services.user_service import create_user, login_user, update_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/create-users")
def create(user: UserCreate):
    try:
        return create_user(user)
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/get-users")
def login(login: UserLogin):
    user = login_user(login)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    return user

@router.put("/update-users/{uid}")
def update(uid: str, update: UserUpdate):
    return update_user(uid, update.name, update.password)