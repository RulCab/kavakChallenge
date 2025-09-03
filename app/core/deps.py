import os
from pathlib import Path
from typing import Optional

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except Exception:
    firebase_admin = None
    credentials = None
    firestore = None

try:
    import google.generativeai as genai
except Exception:
    genai = None

from .settings import settings

# ---- Firebase ----
db = None
firebase_enabled = False
if settings.firebase_creds_path:
    p = Path(settings.firebase_creds_path)
    if firebase_admin and credentials and firestore and p.exists():
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(str(p))
                firebase_admin.initialize_app(cred)
            db = firestore.client()
            firebase_enabled = True
            print("[INFO] Firebase initialized.")
        except Exception as e:
            print(f"[WARN] Could not initialize Firebase: {e}. Using in-memory persistence.")
    else:
        print(f"[WARN] FIREBASE_CREDENTIALS '{settings.firebase_creds_path}' not found or SDK unavailable. Using in-memory persistence.")
else:
    print("[INFO] FIREBASE_CREDENTIALS not set. Using in-memory persistence.")

# ---- Gemini ----
gemini_enabled = bool(settings.gemini_key) and genai is not None
if gemini_enabled:
    try:
        genai.configure(api_key=settings.gemini_key)
        print("[INFO] Gemini configured.")
    except Exception as e:
        print(f"[WARN] Could not configure Gemini: {e}. Using mock responses.")
        gemini_enabled = False
else:
    print("[INFO] GEMINI_API_KEY not set or SDK unavailable. Using mock responses.")

# ---- Test overrides ----
if os.getenv("DISABLE_FIREBASE") == "1":
    firebase_enabled = False
    db = None

if os.getenv("DISABLE_GEMINI") == "1":
    gemini_enabled = False
