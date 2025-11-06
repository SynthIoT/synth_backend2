# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  
from routers import user, project, chat, ai_route, synth
from services.synth_service import ensure_model_loaded, get_model_path

app = FastAPI(
    title="SYNTHIOT API",
    description="Synthetic IoT Data Generator",
    version="1.0"
)

# === FIX CORS IN 3 LINES ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", 
                   "https://synthiot-frontend-cqpons0qy-dreammart1331-9605s-projects.vercel.app",
                   "https://synthiot-frontend.vercel.app"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def load_models():
    print(f"[synth] CTGAN path: {get_model_path() or '(not set)'}")
    try:
        ensure_model_loaded()
        print("[synth] CTGAN loaded ✅")
    except Exception as e:
        print(f"[synth] CTGAN not loaded: {e}")

app.include_router(user.router)
app.include_router(project.router)
app.include_router(chat.router)
app.include_router(ai_route.router)
app.include_router(synth.router) 

@app.get("/")
def home():
    return {"message": "SYNTHIOT API Running 🟢"}