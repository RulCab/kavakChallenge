import os
import time
import random
import asyncio
from typing import Optional, Dict, List
from pathlib import Path

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

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, constr

# -----------------------------
# Settings (desde environment)
# -----------------------------
class Settings(BaseModel):
    gemini_key: Optional[str] = Field(None, alias="GEMINI_API_KEY")
    firebase_creds_path: Optional[str] = Field(None, alias="FIREBASE_CREDENTIALS")
    model_name: str = Field("gemini-2.0-flash", alias="GEMINI_MODEL")
    max_reply_secs: int = Field(30, alias="MAX_REPLY_SECS")
    history_soft_limit: int = Field(200, alias="HISTORY_SOFT_LIMIT")


def load_settings() -> Settings:
    data = {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "FIREBASE_CREDENTIALS": os.getenv("FIREBASE_CREDENTIALS"),
        "GEMINI_MODEL": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        "MAX_REPLY_SECS": int(os.getenv("MAX_REPLY_SECS", "30")),
        "HISTORY_SOFT_LIMIT": int(os.getenv("HISTORY_SOFT_LIMIT", "200")),
    }
    return Settings(**data)


settings = load_settings()

# -----------------------------
# Firebase & Gemini init (NO-op si faltan)
# -----------------------------
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
            print("[INFO] Firebase inicializado.")
        except Exception as e:
            print(f"[WARN] No se pudo inicializar Firebase: {e}. Persistencia en memoria.")
    else:
        print(f"[WARN] FIREBASE_CREDENTIALS '{settings.firebase_creds_path}' no encontrado o SDK no disponible. Persistencia en memoria.")
else:
    print("[INFO] FIREBASE_CREDENTIALS vacío. Persistencia en memoria.")

gemini_enabled = bool(settings.gemini_key) and genai is not None
if gemini_enabled:
    try:
        genai.configure(api_key=settings.gemini_key)
        print("[INFO] Gemini configurado.")
    except Exception as e:
        print(f"[WARN] No se pudo configurar Gemini: {e}. Usando respuestas mock.")
        gemini_enabled = False
else:
    print("[INFO] GEMINI_API_KEY vacío o SDK no disponible. Usando respuestas mock.")

# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(title="Kopi Debate API", version="1.0.0")

# -----------------------------
# Datos / prompts base
# -----------------------------
TOPICS = [
    "Expensive perfumes are always better than cheap ones",
    "Sweet fragrances are masculine, and fresh ones are feminine",
    "Dior Sauvage is the only perfume you should wear",
    "Niche fragrances are just an unnecessary trend",
    "A perfume can change your life",
    "Vintage fragrances are the only real option",
    "Clones should be illegal",
    "Longevity is everything",
    "You can't wear fresh perfumes in winter",
    "Clothing and style don’t matter, only perfume does",
    "Designer perfumes are just overpriced marketing, niche is the only true art",
    "Only vintage batches smell authentic; reformulations ruin perfumes",
    "Real men should never wear sweet perfumes",
    "Perfume should only be worn at night, not during the day",
    "Projection is more important than longevity",
    "If you can't smell your own perfume, it's not worth wearing",
    "Wearing perfume every day is a waste of money",
    "Perfume should be banned in public spaces",
    "Unisex perfumes are a myth; every scent has a gender",
    "Seasonal restrictions are nonsense; any perfume can be worn year-round",
]

ARGUMENT_STYLES = [
    "Historical: Throughout history, civilizations have valued high-quality perfumes...",
    "Scientific: Studies have shown that luxury fragrances contain more refined ingredients...",
    "Emotional: An expensive perfume is not just a scent, it's a bottled memory...",
    "Sarcastic: Sure, go ahead and use a cheap perfume if you want to smell like a car air freshener...",
    "Practical: From a practical perspective, certain perfumes simply don't work in specific contexts...",
    "Philosophical: Perfume is a reflection of identity and existence; choosing wrongly betrays your essence...",
    "Economic: The fragrance industry thrives on trends, but real value comes from performance and longevity...",
    "Cultural: Across cultures, scents have been tied to rituals, status, and belonging...",
    "Humorous: Imagine walking into a party smelling like cleaning spray—hilarious, but hardly persuasive...",
    "Romantic: A perfume is like a love story; mismatched notes are like broken promises...",
]

# -----------------------------
# Esquemas
# -----------------------------
class MessageRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: constr(strip_whitespace=True, min_length=1, max_length=2000)

# -----------------------------
# Persistencia: Firestore ó memoria
# -----------------------------
_memory_store: Dict[str, List[dict]] = {}

def _truncate(msgs: List[dict]) -> List[dict]:
    if len(msgs) > settings.history_soft_limit:
        return msgs[-settings.history_soft_limit :]
    return msgs

def save_conversation(cid: str, msgs: List[dict]):
    msgs = _truncate(msgs)
    if firebase_enabled and db is not None:
        db.collection("conversations").document(cid).set({"messages": msgs})
    else:
        _memory_store[cid] = msgs

def load_conversation(cid: str) -> List[dict]:
    if firebase_enabled and db is not None:
        doc = db.collection("conversations").document(cid).get()
        return (doc.to_dict() or {}).get("messages", []) if getattr(doc, "exists", False) else []
    return _memory_store.get(cid, [])

# -----------------------------
# Utils
# -----------------------------
def extract_topic_from_seed(seed: str) -> str:
    out = seed
    if out.startswith("I will prove that "):
        out = out[len("I will prove that ") :]
    return out.rstrip("!")

def is_on_topic(user_msg: str, topic: str) -> bool:
    topic_kw = {w.lower() for w in topic.split() if len(w) > 3}
    msg_kw = {w.lower() for w in user_msg.split() if len(w) > 3}
    return len(topic_kw & msg_kw) >= max(1, len(topic_kw) // 6)

def ground_reply(topic: str) -> str:
    return (
        f"Let's stay on our topic: **{topic}**. "
        "I’ll address your point strictly in relation to this claim."
    )

def build_prompt(topic: str, user_message: str, style: str) -> str:
    return f"""You must defend "**{topic}**" at all costs.

Guidelines:
- Stand your ground: never change your stance.
- Be persuasive: logical reasoning, examples, rhetorical techniques.
- Stay on topic: relate everything to the original claim.
- Extend the discussion: invite follow-ups.
- Keep responses concise (must complete in <30s).
- Your argument style is: **{style}**.

Conversation:
User: {user_message}
AI:"""

# -----------------------------
# Modelo (con fallback mock)
# -----------------------------
def call_model_sync(prompt: str) -> str:
    model = genai.GenerativeModel(model_name=settings.model_name)
    resp = model.generate_content(prompt)
    return (getattr(resp, "text", "") or "").strip()

async def generate_gemini_response_async(topic: str, user_message: str, style: str) -> str:
    # Si no hay Gemini, responder modo mock
    if not gemini_enabled:
        return (
            f"**{topic}** — (mock)\n"
            f"Style: {style}\n"
            f"You said: *{user_message}*.\n"
            f"My stance remains firm. Which part do you disagree with the most?"
        )

    prompt = build_prompt(topic, user_message, style)
    try:
        return await asyncio.to_thread(call_model_sync, prompt)
    except Exception:
        # Fallback minimalista
        short = f"Defend: {topic}. Style: {style}. User: {user_message}\nAI:"
        try:
            return await asyncio.to_thread(call_model_sync, short)
        except Exception:
            return (
                f"I will keep defending my original claim (**{topic}**) despite technical issues. "
                "Which part do you disagree with the most?"
            )

# -----------------------------
# Endpoints
# -----------------------------
@app.get("/")
def root():
    return {
        "name": "Kopi Debate API",
        "version": "1.0.0",
        "ready": True,
        "gemini": gemini_enabled,
        "firebase": firebase_enabled,
    }

@app.get("/healthz")
def health():
    return {"status": "ok"}

@app.post("/chat")
async def chat(req: MessageRequest):
    cid = req.conversation_id or f"conv_{random.randint(1000, 9999)}"
    history = load_conversation(cid)

    if not history:
        topic = random.choice(TOPICS)
        seed = f"I will prove that {topic}!"
        history.append({"role": "bot", "message": seed})
    else:
        topic = extract_topic_from_seed(history[0]["message"])

    history.append({"role": "user", "message": req.message})

    if not is_on_topic(req.message, topic):
        history.append({"role": "bot", "message": ground_reply(topic)})

    style = random.choice(ARGUMENT_STYLES)

    try:
        bot_msg = await asyncio.wait_for(
            generate_gemini_response_async(topic, req.message, style),
            timeout=max(1, settings.max_reply_secs - 2),
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Response time exceeded 30 seconds")

    history.append({"role": "bot", "message": bot_msg})
    save_conversation(cid, history)

    return {"conversation_id": cid, "message": history[-5:]}

