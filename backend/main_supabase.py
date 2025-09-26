"""
FastAPI Backend for ANYTIME Contest (Supabase deployment)
Uses Supabase as the data storage backend - more reliable than direct PostgreSQL.
"""

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic.v1 import BaseModel, validator, ValidationError

from supabase import create_client, Client


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


# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.warning("SUPABASE_URL or SUPABASE_ANON_KEY not set. Database operations will fail until configured.")

# Initialize Supabase client
supabase: Optional[Client] = None

def init_supabase() -> None:
    global supabase
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Supabase credentials are not configured")
    if supabase is None:
        logger.info("Initializing Supabase client")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def ensure_table_exists() -> None:
    """Ensure the submissions table exists in Supabase"""
    # Supabase handles table creation through the dashboard or SQL editor
    # This is just a placeholder for any initialization logic
    logger.info("Supabase table initialization (handled via dashboard)")


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
    description="Backend API for storing contest submissions in Supabase",
    version="3.0.0"
)


# CORS configuration: allow configured origins and Vercel preview domains via regex
cors_origins_env = os.getenv("FRONTEND_ORIGINS") or os.getenv("FRONTEND_ORIGIN", "")
allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

# Sensible defaults for local development when no env provided
if not allowed_origins:
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost",
        "http://127.0.0.1",
    ]

# Allow Vercel preview/prod domains via regex (can be overridden by env)
allow_origin_regex = os.getenv("CORS_ALLOW_ORIGIN_REGEX", r"https://.*\.vercel\.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"]
)

# Log CORS configuration for debugging
logger.info(f"CORS allowed_origins: {allowed_origins}")
logger.info(f"CORS allow_origin_regex: {allow_origin_regex}")


@app.on_event("startup")
async def on_startup() -> None:
    logger.info(f"Starting ANYTIME Contest API in {ENVIRONMENT} mode")
    init_supabase()
    ensure_table_exists()
    logger.info("Supabase client initialized")


@app.get("/")
async def root():
    return {
        "message": "ANYTIME Contest API is running",
        "status": "healthy",
        "version": "3.0.0",
        "storage": "supabase"
    }


@app.get("/health")
async def health_check():
    db_status = "connected"
    try:
        init_supabase()
        # Test connection by trying to count records
        result = supabase.table('submissions').select('id', count='exact').limit(1).execute()
        if result.count is None:
            db_status = "disconnected"
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "database": db_status,
        "storage_method": "supabase",
        "cors_origins": allowed_origins,
        "timestamp": datetime.now().isoformat()
    }


def insert_submission(data: ContestSubmission) -> str:
    assert supabase is not None
    submission_id = f"sub_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}"
    
    # Prepare data for Supabase
    submission_data = {
        "id": submission_id,
        "name": data.name,
        "email": data.email,
        "answer": data.answer,
        "timestamp": data.timestamp or datetime.now().isoformat()
    }
    
    try:
        result = supabase.table('submissions').insert(submission_data).execute()
        if result.data:
            logger.info(f"Stored submission for {data.email} -> {submission_id}")
            return submission_id
        else:
            raise Exception("No data returned from insert")
    except Exception as e:
        logger.error(f"Failed to insert submission: {e}")
        raise


def count_submissions_db() -> int:
    assert supabase is not None
    try:
        result = supabase.table('submissions').select('id', count='exact').execute()
        return result.count or 0
    except Exception as e:
        logger.error(f"Failed to count submissions: {e}")
        return 0


def list_submissions_db(limit: int = 1000) -> List[Dict[str, Any]]:
    assert supabase is not None
    try:
        result = supabase.table('submissions').select('*').order('timestamp', desc=True).limit(limit).execute()
        submissions: List[Dict[str, Any]] = []
        
        for row in result.data or []:
            submissions.append({
                "id": row.get("id"),
                "name": row.get("name"),
                "email": row.get("email"),
                "answer": row.get("answer"),
                "timestamp": row.get("timestamp"),
                "submitted_at": row.get("timestamp"),
                "storage_method": "supabase"
            })
        
        return submissions
    except Exception as e:
        logger.error(f"Failed to list submissions: {e}")
        return []


@app.post("/submit", response_model=SubmissionResponse)
async def submit_contest_entry(request: Request):
    try:
        payload: Dict[str, Any] = {}
        # Try JSON first
        try:
            payload = await request.json()
        except Exception:
            # Fallback: try form data
            try:
                form = await request.form()
                payload = {k: (v if isinstance(v, str) else str(v)) for k, v in form.items()}
            except Exception:
                # Last resort: try raw text -> json
                try:
                    raw_text = await request.body()
                    if raw_text:
                        import json as _json
                        payload = _json.loads(raw_text.decode("utf-8"))
                    else:
                        payload = {}
                except Exception:
                    payload = {}

        if not isinstance(payload, dict):
            payload = {}

        # Log only the keys received (avoid sensitive data in logs)
        try:
            logger.debug(f"/submit received keys: {list(payload.keys())}")
        except Exception:
            pass

        # Validate using Pydantic model
        try:
            submission = ContestSubmission(**payload)
        except ValidationError as ve:
            # Return a structured 422 with combined messages
            details = [
                {"loc": e.get('loc'), "msg": e.get('msg'), "type": e.get('type')}
                for e in ve.errors()
            ]
            raise HTTPException(status_code=422, detail=details)

        if not submission.timestamp:
            submission.timestamp = datetime.now().isoformat()

        submission_id = insert_submission(submission)
        return SubmissionResponse(
            success=True,
            message="Submission recorded successfully!",
            submission_id=submission_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in submit_contest_entry")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )


@app.get("/submissions/count")
async def get_submission_count():
    try:
        count = count_submissions_db()
        return {
            "total_submissions": count,
            "storage_method": "supabase",
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
            "storage_method": "supabase",
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
    uvicorn.run("backend.main_supabase:app", host=host, port=port, log_level="debug" if DEBUG_MODE else "info")
