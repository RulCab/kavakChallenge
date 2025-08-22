import os, time, random, json
import firebase_admin
from firebase_admin import credentials, firestore
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FIREBASE_PATH = os.getenv("FIREBASE_CREDENTIALS", "")

if not firebase_admin._apps:
    if not (FIREBASE_PATH and os.path.exists(FIREBASE_PATH)):
        raise RuntimeError(f"FIREBASE_CREDENTIALS no encontrado: {FIREBASE_PATH}")
    cred = credentials.Certificate(FIREBASE_PATH)
    firebase_admin.initialize_app(cred)
db = firestore.client()

genai.configure(api_key=GEMINI_API_KEY)
app = FastAPI()

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
    "Clothing and style don’t matter, only perfume does"
]
ARGUMENT_STYLES = [
    "Historical: Throughout history, civilizations have valued high-quality perfumes...",
    "Scientific: Studies have shown that luxury fragrances contain more refined ingredients...",
    "Emotional: An expensive perfume is not just a scent, it's a bottled memory...",
    "Sarcastic: Sure, go ahead and use a cheap perfume if you want to smell like a car air freshener..."
]

class MessageRequest(BaseModel):
    conversation_id: Optional[str]
    message: str

def save_conversation(cid, msgs):
    db.collection("conversations").document(cid).set({"messages": msgs})

def load_conversation(cid):
    doc = db.collection("conversations").document(cid).get()
    return doc.to_dict().get("messages", []) if doc.exists else []

def generate_gemini_response(topic, user_message, argument_style):
    try:
        prompt = f"""You must defend "**{topic}**" at all costs.
- Stand your ground, be persuasive, stay on topic, extend discussion.
- Respond in <30s. Argument style: **{argument_style}**.

User: {user_message}
AI:"""
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        start = time.time()
        resp = model.generate_content(prompt)
        if time.time() - start > 30:
            raise HTTPException(status_code=408, detail="Response time exceeded 30 seconds")
        return (resp.text or "").strip()
    except Exception as e:
        print("Gemini error:", e)
        return "I am convinced that my position is correct, despite technical difficulties!"

@app.get("/healthz")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(req: MessageRequest):
    cid = req.conversation_id or f"conv_{random.randint(1000, 9999)}"
    history = load_conversation(cid)

    if not history:
        topic = random.choice(TOPICS)
        history.append({"role": "bot", "message": f"I will prove that {topic}!"})

    history.append({"role": "user", "message": req.message})
    topic = history[0]["message"].replace("I will prove that ", "").replace("!", "")
    style = random.choice(ARGUMENT_STYLES)
    bot_msg = generate_gemini_response(topic, req.message, style)
    history.append({"role": "bot", "message": bot_msg})

    save_conversation(cid, history)
    return {"conversation_id": cid, "message": history[-5:]}

