import time
from fastapi import APIRouter, HTTPException
from loguru import logger
from src.database import get_connection  # Assuming you have a function to get DB connection
import os

router = APIRouter()

# Track service start time
SERVICE_START_TIME = time.time()

def get_service_uptime():
    """Calculate service uptime in seconds."""
    return round(time.time() - SERVICE_START_TIME, 2)

def check_database():
    """Check if the database is reachable."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

@router.get("/health", summary="Health Check", tags=["Health"])
async def health_check():
    """
    Health check endpoint that verifies:
    - API status
    - Database connectivity
    - Uptime

    Returns:
        A JSON object with system health details.
    """
    try:
        logger.info("Health check endpoint called.")

        db_status = check_database()
        uptime = get_service_uptime()

        health_status = {
            "status": "ok" if db_status else "degraded",
            "database": "ok" if db_status else "down",
            "uptime_seconds": uptime,
            "version": os.getenv("APP_VERSION", "1.0.0")  # Retrieve from env if set
        }

        if not db_status:
            logger.warning("Health check returned degraded status.")
            raise HTTPException(status_code=503, detail=health_status)

        return health_status

    except Exception as e:
        logger.exception("Health check failed")
        raise HTTPException(status_code=500, detail="Health check failed")