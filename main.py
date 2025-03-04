from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def read_root():
    return {"message": "API is running!"}

@app.post("/chat")
def chat(request: ChatRequest):
    return {"response": f"You said: {request.message}"}
