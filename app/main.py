from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routes import router


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered personalized comic generator",
    version="1.0.0",
)

app.mount(
    "/static",
    StaticFiles(directory=str(settings.STATIC_DIR)),
    name="static",
)

app.include_router(router)