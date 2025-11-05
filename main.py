# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # ← ADD THIS
from routers import user, project, chat

app = FastAPI(
    title="SYNTHIOT API",
    description="Synthetic IoT Data Generator",
    version="1.0"
)

# === FIX CORS IN 3 LINES ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(project.router)
app.include_router(chat.router)

@app.get("/")
def home():
    return {"message": "SYNTHIOT API Running 🟢"}