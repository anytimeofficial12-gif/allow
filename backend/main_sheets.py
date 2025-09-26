"""
FastAPI Backend for ANYTIME Contest (Google Sheets fallback)
Uses Google Sheets API as a reliable fallback storage solution.
"""

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic.v1 import BaseModel, validator, ValidationError

import httpx


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


# Google Sheets configuration
GOOGLE_SHEETS_API_KEY = os.getenv('GOOGLE_SHEETS_API_KEY')
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
GOOGLE_SHEET_RANGE = os.getenv('GOOGLE_SHEET_RANGE', 'Sheet1!A:E')

if not GOOGLE_SHEETS_API_KEY or not GOOGLE_SHEET_ID:
    logger.warning("Google Sheets credentials not set. Will use in-memory storage as fallback.")

# In-memory storage as ultimate fallback
in_memory_storage: List[Dict[str, Any]] = []


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
    description="Backend API for storing contest submissions in Google Sheets",
    version="4.0.0"
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


async def append_to_google_sheets(data: ContestSubmission) -> bool:
    """Append submission to Google Sheets"""
    if not GOOGLE_SHEETS_API_KEY or not GOOGLE_SHEET_ID:
        return False
    
    try:
        submission_id = f"sub_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}"
        timestamp = data.timestamp or datetime.now().isoformat()
        
        # Prepare row data
        row_data = [
            submission_id,
            data.name,
            data.email,
            data.answer,
            timestamp
        ]
        
        # Google Sheets API endpoint
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{GOOGLE_SHEET_ID}/values/{GOOGLE_SHEET_RANGE}:append"
        
        params = {
            'valueInputOption': 'RAW',
            'key': GOOGLE_SHEETS_API_KEY
        }
        
        payload = {
            'values': [row_data]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, params=params, json=payload)
            response.raise_for_status()
            
        logger.info(f"Successfully appended to Google Sheets: {submission_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to append to Google Sheets: {e}")
        return False


def store_in_memory(data: ContestSubmission) -> str:
    """Store submission in memory as fallback"""
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
    logger.info(f"Stored in memory: {submission_id}")
    return submission_id


@app.on_event("startup")
async def on_startup() -> None:
    logger.info(f"Starting ANYTIME Contest API in {ENVIRONMENT} mode")
    logger.info("Google Sheets API backend initialized")


@app.get("/")
async def root():
    return {
        "message": "ANYTIME Contest API is running",
        "status": "healthy",
        "version": "4.0.0",
        "storage": "google_sheets"
    }


@app.get("/health")
async def health_check():
    storage_status = "google_sheets"
    if not GOOGLE_SHEETS_API_KEY or not GOOGLE_SHEET_ID:
        storage_status = "memory_fallback"
    
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "storage_method": storage_status,
        "cors_origins": allowed_origins,
        "timestamp": datetime.now().isoformat()
    }


async def insert_submission(data: ContestSubmission) -> str:
    """Insert submission with fallback strategy"""
    # Try Google Sheets first
    if await append_to_google_sheets(data):
        return f"sub_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}"
    
    # Fallback to in-memory storage
    logger.warning("Google Sheets failed, using in-memory storage")
    return store_in_memory(data)


def count_submissions_db() -> int:
    """Count submissions from in-memory storage"""
    return len(in_memory_storage)


def list_submissions_db(limit: int = 1000) -> List[Dict[str, Any]]:
    """List submissions from in-memory storage"""
    return in_memory_storage[-limit:] if in_memory_storage else []


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
                        payload = json.loads(raw_text.decode("utf-8"))
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
            "storage_method": "google_sheets" if GOOGLE_SHEETS_API_KEY else "memory_fallback",
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
            "storage_method": "google_sheets" if GOOGLE_SHEETS_API_KEY else "memory_fallback",
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
    uvicorn.run("backend.main_sheets:app", host=host, port=port, log_level="debug" if DEBUG_MODE else "info")
