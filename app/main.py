# app/main.py
from fastapi import FastAPI
from app.api.routes import router as api_router, swagger_ui, build_openapi

openapi_tags = [
    {"name": "meta", "description": "Health and metadata endpoints."},
    {"name": "chat", "description": "Debate with the bot: it defends its stance and stays on topic."},
]

app = FastAPI(
    title="Kopi Debate API",
    version="1.2.0",
    description=(
        "Debate API.\n\n"
        "- The bot **chooses/remembers** a topic and **defends its stance** (stand your ground).\n"
        "- Keeps the conversation tied to the original claim.\n"
        "- Maximum response time: **≤ 30s**.\n"
        "- Returns the **last 5 messages** (latest last)."
    ),
    contact={"name": "RulCab", "url": "https://github.com/RulCab/kavakChallenge"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    openapi_tags=openapi_tags,
    docs_url=None,
    redoc_url="/redoc",
)

app.include_router(api_router)

@app.get("/docs", include_in_schema=False)
def custom_swagger_ui():
    return swagger_ui()

def custom_openapi():
    return build_openapi(app)

app.openapi = custom_openapi  # type: ignore
