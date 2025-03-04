from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "API is running!"}

@app.post("/chat")
def chat(message: str):
    return {"response": f"You said: {message}"}
