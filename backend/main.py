"""
FastAPI Backend for ANYTIME Contest (Multi-storage backend)
Supports Supabase, Google Sheets, and PostgreSQL with automatic fallback.
"""
from __future__ import annotations

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic.v1 import BaseModel, validator, ValidationError

# Supabase storage backend
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


# Environment configuration
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
DEBUG_MODE = ENVIRONMENT == 'development'
STORAGE_BACKEND = 'supabase'

# Logging
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Storage configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

# Initialize storage clients
supabase: Optional[Client] = None
in_memory_storage: List[Dict[str, Any]] = []


def init_storage() -> str:
    """Initialize Supabase storage with fallback to memory"""
    global supabase
    if SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Initialized Supabase storage")
            return "supabase"
        except Exception as e:
            logger.warning(f"Supabase initialization failed: {e}")
    logger.warning("Using in-memory storage")
    return "memory"


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
    description="Backend API with multiple storage backends",
    version="5.0.0"
)


# CORS configuration
cors_origins_env = os.getenv("FRONTEND_ORIGINS") or os.getenv("FRONTEND_ORIGIN", "")
allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

if not allowed_origins:
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost",
        "http://127.0.0.1",
        "https://allow-khaki.vercel.app",
    ]

allow_origin_regex = os.getenv("CORS_ALLOW_ORIGIN_REGEX", r"https://.*\.vercel\.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"]
)

logger.info(f"CORS allowed_origins: {allowed_origins}")
logger.info(f"CORS allow_origin_regex: {allow_origin_regex}")


# Security headers middleware
from fastapi import Response

@app.middleware("http")
async def add_security_headers(request, call_next):
    response: Response = await call_next(request)
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    # Content Security Policy
    allowed_frame_ancestors = "'self' https://allow-khaki.vercel.app https://*.vercel.app"
    csp_directives = [
        "default-src 'self'",
        f"frame-ancestors {allowed_frame_ancestors}",
        "base-uri 'none'",
        "script-src 'self' 'unsafe-inline'",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com",
        "style-src-elem 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com",
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com data:",
        "img-src 'self' data: https:",
        "connect-src 'self' https://allow-4.onrender.com",
        "object-src 'none'",
        "frame-src 'self'",
        "upgrade-insecure-requests"
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
    # Caching: default no-store for dynamic endpoints
    if request.url.path.startswith("/submit") or request.url.path.startswith("/submissions") or request.url.path.startswith("/health"):
        response.headers["Cache-Control"] = "no-store"
    return response

@app.options("/submit")
async def options_submit():
    # Explicit preflight handler (CORS middleware will add headers)
    return Response(status_code=204)


# Storage functions
async def insert_submission_supabase(data: ContestSubmission) -> str:
    """Insert submission to Supabase"""
    if not supabase:
        raise Exception("Supabase not initialized")
    
    submission_id = f"sub_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}"
    submission_data = {
        "id": submission_id,
        "name": data.name,
        "email": data.email,
        "answer": data.answer,
        "timestamp": data.timestamp or datetime.now().isoformat()
    }
    
    result = supabase.table('submissions').insert(submission_data).execute()
    if not result.data:
        raise Exception("No data returned from Supabase insert")
    
    return submission_id


# Removed Google Sheets storage path


# Removed PostgreSQL storage path


def insert_submission_memory(data: ContestSubmission) -> str:
    """Insert submission to in-memory storage"""
    submission_id = f"sub_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}"
    timestamp = data.timestamp or datetime.now().isoformat()
    
    submission_data = {
        "id": submission_id,
        "name": data.name,
        "email": data.email,
        "answer": data.answer,
        "timestamp": timestamp,
        "storage_method": "memory"
    }
    
    in_memory_storage.append(submission_data)
    return submission_id


async def insert_submission(data: ContestSubmission) -> str:
    """Insert submission using the active storage backend"""
    current_storage = getattr(app.state, 'storage_backend', 'memory')
    
    try:
        if current_storage == 'supabase':
            return await insert_submission_supabase(data)
        else:
            return insert_submission_memory(data)
    except Exception as e:
        logger.error(f"Storage {current_storage} failed: {e}")
        # Fallback to memory storage
        logger.warning("Falling back to in-memory storage")
        return insert_submission_memory(data)


def count_submissions() -> int:
    """Count submissions from active storage"""
    current_storage = getattr(app.state, 'storage_backend', 'memory')
    
    try:
        if current_storage == 'supabase' and supabase:
            result = supabase.table('submissions').select('id', count='exact').execute()
            return result.count or 0
        else:
            return len(in_memory_storage)
    except Exception as e:
        logger.error(f"Count failed for {current_storage}: {e}")
        return len(in_memory_storage)


def list_submissions(limit: int = 1000) -> List[Dict[str, Any]]:
    """List submissions from active storage"""
    current_storage = getattr(app.state, 'storage_backend', 'memory')
    
    try:
        if current_storage == 'supabase' and supabase:
            result = supabase.table('submissions').select('*').order('timestamp', desc=True).limit(limit).execute()
            submissions = []
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
        else:
            return in_memory_storage[-limit:] if in_memory_storage else []
    except Exception as e:
        logger.error(f"List failed for {current_storage}: {e}")
        return in_memory_storage[-limit:] if in_memory_storage else []


@app.on_event("startup")
async def on_startup() -> None:
    logger.info(f"Starting ANYTIME Contest API in {ENVIRONMENT} mode")
    storage_backend = init_storage()
    app.state.storage_backend = storage_backend
    logger.info(f"Storage backend: {storage_backend}")


@app.get("/")
async def root():
    current_storage = getattr(app.state, 'storage_backend', 'memory')
    return {
        "message": "ANYTIME Contest API is running",
        "status": "healthy",
        "version": "5.0.0",
        "storage": current_storage
    }


@app.get("/health")
async def health_check():
    current_storage = getattr(app.state, 'storage_backend', 'memory')
    db_status = "connected"
    
    try:
        if current_storage == 'supabase' and supabase:
            result = supabase.table('submissions').select('id', count='exact').limit(1).execute()
            if result.count is None:
                db_status = "disconnected"
        elif current_storage == 'postgres' and postgres_pool:
            with postgres_pool.connection() as conn:
                conn.execute("SELECT 1")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "database": db_status,
        "storage_method": current_storage,
        "cors_origins": allowed_origins,
        "timestamp": datetime.now().isoformat()
    }


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

        # Log only the keys received
        try:
            logger.debug(f"/submit received keys: {list(payload.keys())}")
        except Exception:
            pass

        # Validate using Pydantic model
        try:
            submission = ContestSubmission(**payload)
        except ValidationError as ve:
            details = [
                {"loc": e.get('loc'), "msg": e.get('msg'), "type": e.get('type')}
                for e in ve.errors()
            ]
            raise HTTPException(status_code=422, detail=details)

        if not submission.timestamp:
            submission.timestamp = datetime.now().isoformat()

        submission_id = await insert_submission(submission)
        current_storage = getattr(app.state, 'storage_backend', 'memory')
        
        return SubmissionResponse(
            success=True,
            message=f"Submission recorded successfully using {current_storage}!",
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
        count = count_submissions()
        current_storage = getattr(app.state, 'storage_backend', 'memory')
        return {
            "total_submissions": count,
            "storage_method": current_storage,
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
        submissions = list_submissions()
        current_storage = getattr(app.state, 'storage_backend', 'memory')
        return {
            "total_submissions": len(submissions),
            "submissions": submissions,
            "storage_method": current_storage,
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
