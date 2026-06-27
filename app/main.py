from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.db.session import get_db
from app.utils.redis_client import get_redis

configure_logging()
logger = get_logger("startup")

app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def readiness():
    from sqlalchemy import text
    checks: dict[str, str] = {}
    db = next(get_db())
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
    finally:
        db.close()

    try:
        redis = get_redis()
        redis.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}


app.include_router(auth_router, prefix="/api/v1")
logger.info("flux_auth_started", port=settings.port)
