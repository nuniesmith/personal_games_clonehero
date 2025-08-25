import os
import psycopg2
from psycopg2 import pool, OperationalError, errors
from loguru import logger
from contextlib import contextmanager
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Database Configuration
DB_URL = os.getenv("DB_URL")  # Use full connection string if available
DB_HOST = os.getenv("DB_HOST", "clonehero_db")
DB_NAME = os.getenv("DB_NAME", "clonehero")
DB_USER = os.getenv("DB_USER", "clonehero")
DB_PASSWORD = os.getenv("DB_PASSWORD", "clonehero")
DB_PORT = os.getenv("DB_PORT", "5432")

# Database connection pool
db_pool = None

def create_db_pool(retries=5, delay=5):
    """Creates a database connection pool with retry logic."""
    global db_pool
    for attempt in range(retries):
        try:
            if DB_URL:
                logger.info("🔗 Using DB_URL for connection.")
                db_pool = pool.SimpleConnectionPool(minconn=1, maxconn=10, dsn=DB_URL)
            else:
                logger.info("🔗 Using individual DB settings for connection.")
                db_pool = pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    host=DB_HOST,
                    database=DB_NAME,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    port=DB_PORT,
                )
            logger.success("✅ Database connection pool initialized successfully.")
            return
        except Exception as e:
            logger.warning(f"⚠️ Database connection attempt {attempt + 1}/{retries} failed: {e}")
            time.sleep(delay)
    
    logger.critical("❌ Failed to initialize database pool after retries!")
    db_pool = None  # Prevent errors when calling get_connection()

create_db_pool()

@contextmanager
def get_connection():
    """Context manager for safely acquiring and releasing a database connection."""
    if db_pool is None:
        logger.error("❌ Database pool is not initialized.")
        raise RuntimeError("Database pool is unavailable.")
    
    conn = None
    try:
        conn = db_pool.getconn()
        logger.debug("🔗 Database connection acquired.")
        yield conn
    except OperationalError as e:
        logger.error(f"⚠️ Database connection error: {e}")
        raise
    finally:
        if conn:
            db_pool.putconn(conn)
            logger.debug("🔓 Database connection released.")

def execute_sql_file(sql_file: str):
    """Executes an SQL file with better error handling."""
    try:
        with open(sql_file, "r", encoding="utf-8") as f:
            sql_commands = f.read().strip()
            if not sql_commands:
                logger.warning(f"⚠️ Skipping empty SQL file: {sql_file}")
                return
        
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_commands)
            conn.commit()
            logger.info(f"✅ Successfully executed SQL file: {sql_file}")
    except (OperationalError, errors.DatabaseError) as e:
        logger.error(f"❌ Error executing SQL file {sql_file}: {e}")

def init_db():
    """Initializes the database schema and triggers."""
    logger.info("🚀 Initializing database...")
    execute_sql_file("/app/src/sql/schema.sql")
    logger.success("🎉 Database initialization completed successfully.")

if __name__ == "__main__":
    init_db()