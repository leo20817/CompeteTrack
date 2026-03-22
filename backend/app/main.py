from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import health, brands, collect, menu, changes, scheduler_api
from app.config import settings
from app.schemas.response import APIResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from app.scheduler import start_scheduler
    start_scheduler()
    yield
    # Shutdown
    from app.scheduler import scheduler
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="CompeteTrack API",
    description="Vietnam F&B competitive intelligence platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router)
app.include_router(brands.router)
app.include_router(collect.router)
app.include_router(menu.router)
app.include_router(changes.router)
app.include_router(scheduler_api.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            success=False,
            error=f"Internal server error: {str(exc)}",
        ).model_dump(),
    )
