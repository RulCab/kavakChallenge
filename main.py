import os
import time
import random
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Literal

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

from fastapi import FastAPI, HTTPException, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
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
# FastAPI app con Swagger Pro
# -----------------------------
openapi_tags = [
    {"name": "meta", "description": "Endpoints de salud y metainformación."},
    {"name": "chat", "description": "Conversación con el bot: defiende su postura y mantiene el tema."},
]

app = FastAPI(
    title="Kopi Debate API",
    version="1.2.0",
    description=(
        "API de debate.\n\n"
        "- El bot **elige/recuerda** un tema y **defiende su postura** (stand your ground).\n"
        "- Mantiene la conversación enfocada en el tema inicial.\n"
        "- Tiempo máximo de respuesta: **≤ 30s**.\n"
        "- Devuelve el **histórico reciente (últimos 5 mensajes)**, con el más nuevo al final."
    ),
    contact={
        "name": "RulCab",
        "url": "https://github.com/RulCab/kavakChallenge",
    },
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    openapi_tags=openapi_tags,
    docs_url=None,     # deshabilitamos el /docs por defecto para inyectar uno custom
    redoc_url="/redoc"
)

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
]

ARGUMENT_STYLES = [
    "Historical: Throughout history, civilizations have valued high-quality perfumes...",
    "Scientific: Studies have shown that luxury fragrances contain more refined ingredients...",
    "Emotional: An expensive perfume is not just a scent, it's a bottled memory...",
    "Sarcastic: Sure, go ahead and use a cheap perfume if you want to smell like a car air freshener...",
]

# -----------------------------
# Esquemas (para Swagger bonito)
# -----------------------------
class ChatMessage(BaseModel):
    role: Literal["user", "bot"]
    message: constr(strip_whitespace=True, min_length=1) = Field(
        ...,
        examples=["I will prove that Expensive perfumes are always better than cheap ones!"]
    )

class MessageRequest(BaseModel):
    conversation_id: Optional[str] = Field(
        None,
        description="ID de conversación. Si es null/omitido, se inicia una conversación nueva.",
        examples=[None, "conv_6585"],
    )
    message: constr(strip_whitespace=True, min_length=1, max_length=2000) = Field(
        ...,
        description="Mensaje del usuario.",
        examples=["hola", "What is the best perfume?"]
    )

class ChatResponse(BaseModel):
    conversation_id: str = Field(..., examples=["conv_6585"])
    message: List[ChatMessage] = Field(
        ...,
        description="Histórico reciente (máx. 5). Último mensaje al final.",
        examples=[[
            {"role": "bot",  "message": "I will prove that Expensive perfumes are always better than cheap ones!"},
            {"role": "user", "message": "hola"},
            {"role": "bot",  "message": "Hola! Scientifically speaking..."}
        ]]
    )

class ErrorResponse(BaseModel):
    detail: str = Field(..., examples=["Response time exceeded 30 seconds"])

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
    if not gemini_enabled:
        return (
            f"**{topic}** — (mock)\n"
            f"Style: {style}\n"
            f"You said: *{user_message}*.\n"
            f"My stance remains firm. Which part do you disagree with the most?"
        )
    prompt = build_prompt(topic, user_message, style)
    return await asyncio.to_thread(call_model_sync, prompt)

# -----------------------------
# Endpoints
# -----------------------------
@app.get("/", tags=["meta"], summary="Root", description="Información del servicio y flags de dependencias.")
def root():
    return {
        "name": "Kopi Debate API",
        "version": "1.2.0",
        "ready": True,
        "gemini": gemini_enabled,
        "firebase": firebase_enabled,
    }

@app.get("/healthz", tags=["meta"], summary="Health", description="Comprobación simple de salud.")
def health():
    return {"status": "ok"}

@app.post(
    "/chat",
    tags=["chat"],
    summary="Enviar mensaje al bot",
    description=(
        "Inicia o continúa una conversación.\n\n"
        "- Si **no** envías `conversation_id`, el bot inicia un tema y su postura.\n"
        "- Si lo envías, continúa el hilo y **se mantiene en el tema** (‘stand your ground’).\n"
        "- Respuesta máxima: **≤ 30s**.\n"
        "- Devuelve **últimos 5 mensajes** (más reciente al final)."
    ),
    response_model=ChatResponse,
    responses={
        408: {"model": ErrorResponse, "description": "Timeout de generación (≥30s)."},
        422: {"description": "Validación de payload."},
        500: {"model": ErrorResponse, "description": "Error interno."},
    },
)
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
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="Response time exceeded 30 seconds")

    history.append({"role": "bot", "message": bot_msg})
    save_conversation(cid, history)

    payload = {"conversation_id": cid, "message": history[-5:]}
    resp = JSONResponse(payload)
    resp.headers["X-Conversation-Id"] = cid
    resp.headers["X-Service"] = "kopi-debate"
    return resp

# -----------------------------
# Swagger UI personalizado
# -----------------------------
@app.get("/docs", include_in_schema=False)
def custom_swagger_ui():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} – Docs",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        swagger_ui_parameters={
            "displayRequestDuration": True,
            "defaultModelsExpandDepth": 0,
            "filter": True,
            "syntaxHighlight.theme": "obsidian",
            "persistAuthorization": True,
        },
    )

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["servers"] = [
        {"url": "https://kopichallenge.onrender.com"},
        {"url": "http://localhost:8000"},
    ]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi  # type: ignore

