"""
FastAPI Backend for ANYTIME Contest (Render deployment)
Uses PostgreSQL (Supabase/Render) with a connection pool.
"""

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic.v1 import BaseModel, validator

import psycopg
from psycopg_pool import ConnectionPool


# Environment configuration
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
DEBUG_MODE = ENVIRONMENT == 'development'

# Logging
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL') or os.getenv('POSTGRES_URL_NON_POOLING')
if not DATABASE_URL:
    logger.warning("DATABASE_URL not set. Database operations will fail until configured.")

# Create a global connection pool (max_size 20 for 1M+ rows capacity usage)
pool: Optional[ConnectionPool] = None


def init_pool() -> None:
    global pool
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    if pool is None:
        # For Supabase/Render Postgres; tune as needed
        pool_kwargs = {
            "min_size": 1,
            "max_size": int(os.getenv("DB_POOL_MAX_SIZE", "20")),
            "max_idle": 300,
            "timeout": 30,
        }
        logger.info(f"Initializing PostgreSQL pool with max_size={pool_kwargs['max_size']}")
        pool = ConnectionPool(DATABASE_URL, **pool_kwargs)


def run_migrations() -> None:
    assert pool is not None
    with pool.connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                answer TEXT NOT NULL,
                timestamp TIMESTAMPTZ DEFAULT NOW()
            )
            """
        )


# Pydantic models
class ContestSubmission(BaseModel):
    name: str
    email: str
    answer: str
    timestamp: Optional[str] = None

    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return v.strip()

    @validator('email')
    def validate_email(cls, v):
        if not v or '@' not in v:
            raise ValueError('Valid email address required')
        return v.strip().lower()

    @validator('answer')
    def validate_answer(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError('Answer must be at least 5 characters long')
        return v.strip()


class SubmissionResponse(BaseModel):
    success: bool
    message: str
    submission_id: Optional[str] = None


# FastAPI app
app = FastAPI(
    title="ANYTIME Contest API",
    description="Backend API for storing contest submissions in Postgres",
    version="2.0.0"
)


# CORS configuration: allow only configured Vercel domain in production
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
allowed_origins = [FRONTEND_ORIGIN]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"]
)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info(f"Starting ANYTIME Contest API in {ENVIRONMENT} mode")
    init_pool()
    run_migrations()
    logger.info("Postgres pool initialized and migrations ensured")


@app.get("/")
async def root():
    return {
        "message": "ANYTIME Contest API is running",
        "status": "healthy",
        "version": "2.0.0"
    }


@app.get("/health")
async def health_check():
    db_status = "connected"
    try:
        init_pool()
        with pool.connection() as conn:  # type: ignore[arg-type]
            conn.execute("SELECT 1")
    except Exception as _:
        db_status = "disconnected"
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "database": db_status,
        "cors_origins": allowed_origins,
        "timestamp": datetime.now().isoformat()
    }


def insert_submission(data: ContestSubmission) -> str:
    assert pool is not None
    submission_id = f"sub_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}"
    ts_value = data.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO submissions (id, name, email, answer, timestamp) VALUES (%s, %s, %s, %s, %s)",
                (submission_id, data.name, data.email, data.answer, ts_value)
            )
    return submission_id


def count_submissions_db() -> int:
    assert pool is not None
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM submissions")
            row = cur.fetchone()
            return int(row[0]) if row and row[0] is not None else 0


def list_submissions_db(limit: int = 1000) -> List[Dict[str, Any]]:
    assert pool is not None
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, answer, to_char(timestamp, 'YYYY-MM-DD HH24:MI:SS') as timestamp FROM submissions ORDER BY timestamp DESC LIMIT %s",
                (limit,)
            )
            rows = cur.fetchall() or []
            submissions: List[Dict[str, Any]] = []
            for r in rows:
                submissions.append({
                    "id": r[0],
                    "name": r[1],
                    "email": r[2],
                    "answer": r[3],
                    "timestamp": r[4],
                    "submitted_at": r[4],
                    "storage_method": "postgres"
                })
            return submissions


@app.post("/submit", response_model=SubmissionResponse)
async def submit_contest_entry(submission: ContestSubmission):
    try:
        if not submission.timestamp:
            submission.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        submission_id = insert_submission(submission)
        logger.info(f"Stored submission for {submission.email} -> {submission_id}")
        return SubmissionResponse(
            success=True,
            message="Submission recorded successfully!",
            submission_id=submission_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in submit_contest_entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


@app.get("/submissions/count")
async def get_submission_count():
    try:
        count = count_submissions_db()
        return {
            "total_submissions": count,
            "storage_method": "postgres",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting submission count: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve submission count"
        )


@app.get("/submissions/backup")
async def get_backup_submissions():
    try:
        submissions = list_submissions_db()
        return {
            "total_submissions": len(submissions),
            "submissions": submissions,
            "storage_method": "postgres",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting submissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve submissions"
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("backend.main:app", host=host, port=port, log_level="debug" if DEBUG_MODE else "info")


