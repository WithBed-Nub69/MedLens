"""
FastAPI application entry point.
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api import patients, reports, tests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="MedLens API",
    description="AI-Powered Clinical Information Intelligence",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow local development and Vercel deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global error handler ───────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "An internal error occurred. Please try again."},
    )


# ── Routes ─────────────────────────────────────────────────────────────────────

app.include_router(patients.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(tests.router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "MedLens API"}


@app.get("/")
async def root():
    return {"message": "MedLens API", "docs": "/docs"}
