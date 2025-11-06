# utils/firebase.py
import firebase_admin
from firebase_admin import credentials, firestore, auth
from dotenv import load_dotenv
import os

load_dotenv()

cred_path = os.getenv("FIREBASE_CREDENTIALS")
if not cred_path or not os.path.exists(cred_path):
    raise ValueError("Firebase credentials not found! Check .env")

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

db = firestore.client()