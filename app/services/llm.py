import asyncio
from app.core.settings import settings
from app.core.deps import gemini_enabled, genai  # genai se importa desde deps
from .nlp import build_prompt

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
