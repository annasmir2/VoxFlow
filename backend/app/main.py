from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.ai import router as ai_router
from app.api.routes.health import router as health_router
from app.api.routes.reminders import router as reminders_router
from app.api.routes.tasks import router as tasks_router
from app.core.config import settings
from app.core.database import init_db

app = FastAPI(
    title=settings.project_name,
    description="Premium voice-first productivity assistant API foundation.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.include_router(health_router)
app.include_router(tasks_router, prefix=settings.api_v1_prefix)
app.include_router(reminders_router, prefix=settings.api_v1_prefix)
app.include_router(ai_router, prefix=settings.api_v1_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Welcome to VoxFlow AI API"}
