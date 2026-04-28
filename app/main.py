from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.leads import router as leads_router

app = FastAPI(title="DoorIQ Chatbot API")

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(leads_router)
