import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database.session import init_db
from app.database.seed import seed_database
from app.api.routes import router as api_router
from app.api.vapi_routes import vapi_router
from app.services.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for database initialization and seeding on startup."""
    logger.info("Initializing database tables...")
    init_db()
    logger.info("Seeding demo banking database...")
    try:
        seed_database()
    except Exception as e:
        logger.warning(f"Seed step encountered note: {e}")
    logger.info("AI Voice Banking Assistant API is ready.")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Full-stack AI Voice Banking Assistant with Multi-Agent Coordinator, Tool Calling, and Vapi Voice Webhooks",
    lifespan=lifespan,
)

# Enable CORS for frontend / external voice platform integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(api_router, prefix="/api")
app.include_router(vapi_router, prefix="/api")


@app.get("/")
def serve_ui():
    """Serve the single-page voice calling UI."""
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {
        "message": "AI Voice Banking Assistant API",
        "docs_url": "/docs",
        "health_check": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
