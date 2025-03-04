import os
import time
import random
import firebase_admin
from firebase_admin import credentials, firestore
import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

# Cargar variables de entorno
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")

# Inicializar Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Configurar Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

# Crear la API con FastAPI
app = FastAPI()

# Temas de debate
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

# Modelo de datos para la API
class MessageRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str

# Guardar conversación en Firestore
def save_conversation_to_firestore(conversation_id, messages):
    db.collection("conversations").document(conversation_id).set({"messages": messages})

# Cargar conversación desde Firestore
def load_conversation_from_firestore(conversation_id):
    doc = db.collection("conversations").document(conversation_id).get()
    return doc.to_dict()["messages"] if doc.exists else []

# Generar respuesta con Gemini AI
def generate_gemini_response(topic, user_message, argument_style):
    try:
        prompt = f"""
        You are an AI assistant participating in a debate challenge. Your goal is to defend the following statement at all costs: **{topic}**.

        **Guidelines for your responses:**
        - Stand your ground: Never change your stance, no matter what the user says.
        - Be persuasive: Use logical reasoning, examples, and rhetorical techniques to make your argument compelling.
        - Stay on topic: Keep the conversation focused on the original subject.
        - Extend the conversation: Encourage further discussion by asking questions or introducing new angles.
        - Respond quickly: Keep responses concise but meaningful, and ensure they fit within the 30-second API limit.
        - Your argument style is: **{argument_style}**. Stick to this tone throughout the conversation.
        - Avoid repeating the same arguments in consecutive responses**. Instead, introduce new supporting points or counter-arguments.
        - If the user asks for alternatives, provide at least two examples that align with the debate stance**.

        **Conversation so far:**
        User: {user_message}

        AI:
        """
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        start_time = time.time()
        response = model.generate_content(prompt)
        end_time = time.time()

        if end_time - start_time > 30:
            raise HTTPException(status_code=408, detail="Response time exceeded 30 seconds")

        return response.text.strip()
    except Exception as e:
        print(f"Gemini error: {e}")
        return "I am convinced that my position is correct, despite technical difficulties!"

# Generar respuesta completa
def generate_response(user_message: str, conversation_id: Optional[str]) -> str:
    if conversation_id is None:
        conversation_id = f"conv_{random.randint(1000, 9999)}"

    messages = load_conversation_from_firestore(conversation_id)

    if not messages:
        topic = random.choice(TOPICS)
        messages.append({"role": "bot", "message": f"I will prove that {topic}!"})
        save_conversation_to_firestore(conversation_id, messages)
    else:
        topic = messages[0]["message"].replace("I will prove that ", "").replace("!", "")

    if len(messages) >= 27:
        bot_response = "I believe we've covered all possible angles. This has been a great debate!"
    else:
        argument_style = random.choice(ARGUMENT_STYLES)
        bot_response = generate_gemini_response(topic, user_message, argument_style)

    messages.append({"role": "bot", "message": bot_response})
    save_conversation_to_firestore(conversation_id, messages)
    return bot_response

# Endpoint para chatear
@app.post("/chat")
def chat(request: MessageRequest):
    conversation_id = request.conversation_id or f"conv_{random.randint(1000, 9999)}"
    user_message = request.message

    bot_response = generate_response(user_message, conversation_id)
    messages = load_conversation_from_firestore(conversation_id)

    messages.append({"role": "user", "message": user_message})
    messages.append({"role": "bot", "message": bot_response})
    save_conversation_to_firestore(conversation_id, messages)

    return {"conversation_id": conversation_id, "messages": messages}

