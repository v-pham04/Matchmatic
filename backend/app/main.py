from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import users, jobs, resume
from contextlib import asynccontextmanager
from app.tasks.scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app):
    # This runs when the server STARTS
    scheduler = start_scheduler()
    yield
    # This runs when the server STOPS
    scheduler.shutdown()

app = FastAPI(title="Matchmatic API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(jobs.router)
app.include_router(resume.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "matchmatic-api"}