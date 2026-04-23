"""CampaignPilot FastAPI application."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger(__name__)

_services_status: dict[str, bool] = {"postgres": False, "chromadb": False}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle — startup and shutdown."""
    # Startup
    logger.info("CampaignPilot API starting up...")

    # Test PostgreSQL connection
    try:
        import psycopg2
        conn = psycopg2.connect(os.environ.get("DATABASE_URL", ""))
        conn.close()
        _services_status["postgres"] = True
        logger.info("PostgreSQL connection: OK")
    except Exception as e:
        logger.warning(f"PostgreSQL connection failed: {e}")

    # Test ChromaDB connection
    try:
        import chromadb
        from chromadb.config import Settings
        client = chromadb.HttpClient(
            host=os.environ.get("CHROMA_HOST", "localhost"),
            port=int(os.environ.get("CHROMA_PORT", "8000")),
            settings=Settings(anonymized_telemetry=False),
        )
        client.heartbeat()
        collections = client.list_collections()
        _services_status["chromadb"] = True
        logger.info(f"ChromaDB connection: OK ({len(collections)} collections)")
    except Exception as e:
        logger.warning(f"ChromaDB connection failed: {e}")

    # Store status in app state so routes can read it
    app.state.services = _services_status

    yield

    # Shutdown
    logger.info("CampaignPilot API shutting down.")


app = FastAPI(
    title="CampaignPilot API",
    description="Production-grade multi-agent marketing campaign automation for Lumen Analytics.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — permissive for local dev; tighten for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
from api.routes import agents as agents_router  # noqa: E402
from api.routes import campaigns as campaigns_router  # noqa: E402
from api.routes import evals as evals_router  # noqa: E402

app.include_router(agents_router.router)
app.include_router(campaigns_router.router)
app.include_router(evals_router.router)


@app.get("/", tags=["meta"])
async def root() -> dict:
    """Root endpoint — basic API info."""
    return {"message": "CampaignPilot API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health", tags=["meta"])
async def health() -> dict:
    """Health check — returns service connectivity status."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "services": _services_status,
    }
