import os
import sys
import asyncio
import random
import time
from pathlib import Path
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from loguru import logger
from psycopg2 import OperationalError, errors
from dotenv import load_dotenv  # Load environment variables from .env

# Load environment variables
load_dotenv()

# Ensure the module can be found by adding its root directory to `sys.path`
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import DB init function
from src.database import init_db

# Import routers
from src.routes.content_manager import router as content_manager_router
from src.routes.song_generator import router as song_processing_router
from src.routes.health import router as health_router
from src.routes.database_explorer import router as database_explorer_router

# Read environment variables
LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
LOG_FILE_SIZE = os.getenv("LOG_FILE_SIZE", "10MB")
LOG_RETENTION = os.getenv("LOG_RETENTION", "7 days")

DB_URL = os.getenv("DB_URL")
DB_RETRY_ATTEMPTS = int(os.getenv("DB_RETRY_ATTEMPTS", 10))
DB_RETRY_DELAY = int(os.getenv("DB_RETRY_DELAY", 5))

APP_ENV = os.getenv("APP_ENV", "development")
APP_PORT = int(os.getenv("APP_PORT", 8000))
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")

# Ensure logs directory exists before setting up logging
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configure Loguru logging (logging to file and console)
LOG_FILE = LOG_DIR / "app.log"
logger.add(LOG_FILE, rotation=LOG_FILE_SIZE, retention=LOG_RETENTION, level=LOG_LEVEL)
logger.add(sys.stdout, level="INFO")

async def wait_for_db(max_retries=DB_RETRY_ATTEMPTS, base_delay=DB_RETRY_DELAY):
    """Wait for the database to be ready before initializing."""
    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 Attempting DB connection ({attempt + 1}/{max_retries})...")
            init_db()
            logger.success("✅ Database initialized successfully.")
            return
        except (OperationalError, errors.DatabaseError) as e:
            delay_time = min(base_delay * (2 ** attempt) + random.uniform(0, 1), 60)
            logger.warning(f"⚠️ Database not ready. Retrying in {delay_time:.2f}s - {e}")
            await asyncio.sleep(delay_time)
        except Exception as e:
            logger.critical(f"❌ Unexpected error while connecting to DB: {e}")
            raise e
    
    logger.error("❌ Database connection failed after multiple attempts.")
    raise RuntimeError("Database connection failed after multiple retries.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensures database is initialized before the app starts and handles cleanup on shutdown."""
    await wait_for_db()
    yield  # Application runs here
    logger.info("🛑 FastAPI application is shutting down...")

def create_app() -> FastAPI:
    """Creates the FastAPI application with middleware and routes."""
    app = FastAPI(lifespan=lifespan)

    # Middleware for logging requests
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Middleware to log incoming API requests and their responses."""
        start_time = time.time()
        response = None  # Ensure response is always defined
        
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"❌ Unhandled error in request {request.method} {request.url}: {e}")
            response = None  # Ensure response is defined in case of an error
            raise e  # Re-raise the exception after logging
        finally:
            duration = round(time.time() - start_time, 3)
            status_code = response.status_code if response else 500  # Default to 500 if response is None
            logger.info(f"📤 {request.method} {request.url} - {status_code} [{duration}s]")

        return response

    # Register API routes
    routers = [
        content_manager_router,
        health_router,
        database_explorer_router,
        song_processing_router,
    ]
    for router in routers:
        app.include_router(router, prefix="")

    return app

# Create and run the FastAPI application
app = create_app()