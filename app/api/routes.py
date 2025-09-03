# app/api/routes.py
import random, asyncio
from fastapi import APIRouter, HTTPException, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.core.deps import firebase_enabled, gemini_enabled
from app.core.settings import settings
from app.core.constants import TOPICS, ARGUMENT_STYLES
from app.models.schemas import MessageRequest, ChatResponse, ErrorResponse
from app.services.nlp import extract_topic_from_seed, is_on_topic, ground_reply
from app.services.llm import generate_gemini_response_async

# seleccionar storage
if settings.redis_url:
    from app.storage.redis_store import save_conversation, load_conversation
elif firebase_enabled:
    from app.storage.firestore import save_conversation, load_conversation
else:
    from app.storage.memory import save_conversation, load_conversation

router = APIRouter()

@router.get("/", tags=["meta"], summary="Root")
def root():
    return {
        "name": "Kopi Debate API",
        "version": "1.2.0",
        "ready": True,
        "gemini": gemini_enabled,
        "firebase": firebase_enabled,
    }

@router.get("/healthz", tags=["meta"], summary="Health")
def health():
    return {"status": "ok"}

@router.post(
    "/chat",
    tags=["chat"],
    response_model=ChatResponse,
    responses={
        408: {"model": ErrorResponse, "description": "Generation timeout (≥30s)."},
        422: {"description": "Payload validation error."},
        500: {"model": ErrorResponse, "description": "Internal server error."},
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
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Response time exceeded 30 seconds"
        )

    history.append({"role": "bot", "message": bot_msg})
    save_conversation(cid, history)

    payload = {"conversation_id": cid, "message": history[-5:]}
    resp = JSONResponse(payload)
    resp.headers["X-Conversation-Id"] = cid
    resp.headers["X-Service"] = "kopi-debate"
    return resp

# Swagger custom (se registra en app.main)
def swagger_ui():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Kopi Debate API – Docs",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        swagger_ui_parameters={
            "displayRequestDuration": True,
            "defaultModelsExpandDepth": 0,
            "filter": True,
            "syntaxHighlight.theme": "obsidian",
            "persistAuthorization": True,
        },
    )

def build_openapi(app):
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
