# backend/main.py
from typing import Annotated, Dict, Any, Optional, List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, validator
import uuid
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, auth, firestore
from firebase_admin.exceptions import FirebaseError

# ---------------- CONFIG ----------------
SERVICE_ACCOUNT_KEY_PATH = "firebase_service_account.json"  # <-- update path if needed
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

# ---------------- Firebase init (Auth + Firestore) ----------------
def initialize_firebase_admin():
    try:
        firebase_admin.get_app()
        return
    except ValueError:
        pass
    except Exception as e:
        raise RuntimeError(f"FATAL ERROR during Firebase check: {e}")

    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
        firebase_admin.initialize_app(cred)
        # warm Firestore client
        firestore.client()
        print("--- Firebase Admin SDK (Auth + Firestore) initialized ---")
    except FileNotFoundError:
        raise RuntimeError(f"FATAL ERROR: Service account key not found at {SERVICE_ACCOUNT_KEY_PATH}")
    except Exception as e:
        raise RuntimeError(f"FATAL ERROR initializing Firebase: {e}")

# ---------------- Auth dependency ----------------
bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    token_credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)]
) -> Dict[str, Any]:
    try:
        initialize_firebase_admin()
    except RuntimeError as e:
        print(f"FATAL CONFIGURATION ERROR: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server config error")

    if not token_credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: Bearer token missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    id_token = token_credentials.credentials
    try:
        decoded = auth.verify_id_token(id_token)
        return decoded
    except FirebaseError as e:
        print(f"Firebase Authentication Error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")
    except Exception as e:
        print(f"Unexpected token verification error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token verification failed.")

# ---------------- FastAPI app + CORS ----------------
app = FastAPI(title="SynthIoT API (Firestore)", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Pydantic models ----------------
class CreateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    owner_uid: str
    name: str
    description: Optional[str] = None
    created_at: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None

    @validator("password")
    def min_password(cls, v):
        if not v or len(v) < 6:
            raise ValueError("Password must be at least 6 characters.")
        return v

class SignupResponse(BaseModel):
    uid: str
    email: EmailStr
    display_name: Optional[str] = None
    created_at: str

class UserDetailsRequest(BaseModel):
    display_name: str

class UserDetailsResponse(BaseModel):
    uid: str
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None
    updated_at: str

# ---------------- Firestore helpers ----------------
def _fs_client():
    initialize_firebase_admin()
    return firestore.client()

def projects_collection():
    return _fs_client().collection("project_details")

def user_details_collection():
    return _fs_client().collection("user_details")

def create_project_for_user(uid: str, name: str, description: Optional[str]) -> Dict[str, Any]:
    coll = projects_collection()
    proj_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat() + "Z"
    doc = coll.document(proj_id)
    doc.set({
        "owner_uid": uid,
        "name": name,
        "description": description or "",
        "created_at": created_at,
    })
    return {"id": proj_id, "owner_uid": uid, "name": name, "description": description or "", "created_at": created_at}

def list_projects_for_user(uid: str) -> List[Dict[str, Any]]:
    coll = projects_collection()
    try:
        docs = coll.where("owner_uid", "==", uid).stream()
    except Exception as e:
        print(f"[Firestore] query error for uid={uid}: {e}")
        raise
    projects: List[Dict[str, Any]] = []
    for d in docs:
        data = d.to_dict() or {}
        projects.append({
            "id": d.id,
            "owner_uid": data.get("owner_uid", ""),
            "name": data.get("name", ""),
            "description": data.get("description", ""),
            "created_at": data.get("created_at", ""),
        })
    projects.sort(key=lambda p: p.get("created_at") or "", reverse=True)
    return projects

def create_user_record_in_firestore(uid: str, email: str, display_name: Optional[str]) -> None:
    coll = user_details_collection()
    now = datetime.utcnow().isoformat() + "Z"
    try:
        coll.document(uid).set({
            "uid": uid,
            "email": email,
            "display_name": display_name or "",
            "created_at": now,
        }, merge=True)
    except Exception as e:
        print(f"[Firestore] error writing user_details for uid={uid}: {e}")
        raise

def get_user_details_from_firestore(uid: str) -> Dict[str, Any]:
    doc = user_details_collection().document(uid).get()
    if not doc.exists:
        return {}
    return doc.to_dict() or {}

# ---------------- Endpoints ----------------
@app.get("/")
async def root():
    return {"message": "API is running."}

# Protected example
@app.get("/protected_data")
async def protected_data(user_claims: Annotated[Dict[str, Any], Depends(get_current_user)]):
    return {"message": "ok", "uid": user_claims.get("uid"), "email": user_claims.get("email")}

# Projects
@app.get("/projects", response_model=List[ProjectResponse])
async def get_projects(user_claims: Annotated[Dict[str, Any], Depends(get_current_user)]):
    uid = user_claims.get("uid")
    print(f"[INFO] GET /projects by uid={uid}")
    if not uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    try:
        projects = list_projects_for_user(uid)
        print(f"[INFO] found {len(projects)} projects for uid={uid}")
        return projects
    except Exception as e:
        print(f"Error reading projects: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to read projects")

@app.post("/projects", status_code=status.HTTP_201_CREATED, response_model=ProjectResponse)
async def post_project(payload: CreateProjectRequest, user_claims: Annotated[Dict[str, Any], Depends(get_current_user)]):
    uid = user_claims.get("uid")
    if not uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Project name required")
    project = create_project_for_user(uid, name, payload.description)
    return project

# Signup (public)
@app.post("/signup", status_code=status.HTTP_201_CREATED, response_model=SignupResponse)
async def signup(payload: SignupRequest):
    """
    Creates Firebase Auth user (server-side) and writes a user_details document.
    Expects JSON: { "email": "...", "password": "...", "display_name": "..." }
    """
    try:
        initialize_firebase_admin()
    except RuntimeError as e:
        print(f"FATAL: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server config error")

    try:
        user_rec = auth.create_user(
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name or None
        )
    except Exception as e:
        msg = str(e)
        print(f"[Auth] create_user error: {msg}")
        if "EMAIL_EXISTS" in msg or "email already exists" in msg.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
        if "Password should be at least" in msg or "WEAK_PASSWORD" in msg:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Weak password")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")

    uid = user_rec.uid
    try:
        create_user_record_in_firestore(uid=uid, email=payload.email, display_name=payload.display_name)
    except Exception as e:
        print(f"[Firestore] failed to write user_details for uid={uid}: {e} - rolling back auth user")
        try:
            auth.delete_user(uid)
        except Exception as e2:
            print(f"[Auth] failed rollback delete for uid={uid}: {e2}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user record")

    created_at = datetime.utcnow().isoformat() + "Z"
    return SignupResponse(uid=uid, email=payload.email, display_name=payload.display_name, created_at=created_at)

# Protected user_details endpoints
@app.post("/user_details", response_model=UserDetailsResponse)
async def set_user_details(payload: UserDetailsRequest, user_claims: Annotated[Dict[str, Any], Depends(get_current_user)]):
    uid = user_claims.get("uid")
    email = user_claims.get("email")
    if not uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    try:
        create_user_record_in_firestore(uid=uid, email=email or "", display_name=payload.display_name)
        updated_at = datetime.utcnow().isoformat() + "Z"
        return UserDetailsResponse(uid=uid, email=email, display_name=payload.display_name, updated_at=updated_at)
    except Exception as e:
        print(f"[Firestore] set_user_details error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to store user details")

@app.get("/user_details", response_model=UserDetailsResponse)
async def get_user_details(user_claims: Annotated[Dict[str, Any], Depends(get_current_user)]):
    uid = user_claims.get("uid")
    email = user_claims.get("email")
    if not uid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
    try:
        data = get_user_details_from_firestore(uid)
        return UserDetailsResponse(
            uid=uid,
            email=data.get("email", email),
            display_name=data.get("display_name") or None,
            updated_at=data.get("created_at", datetime.utcnow().isoformat() + "Z"),
        )
    except Exception as e:
        print(f"[Firestore] get_user_details error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to read user details")
