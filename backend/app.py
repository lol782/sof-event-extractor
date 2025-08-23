"""
SoF Event Extractor Backend API
FastAPI application for processing maritime Statement of Facts documents with authentication
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends, Form, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import os
import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
from pathlib import Path

# Import our new integrated modules
try:
    from utils.sof_pipeline import (
        process_uploaded_files, 
        extract_events_and_summary,
        calculate_laytime,
        process_clicked_pdf_enhanced,
        LaytimeResult as SofLaytimeResult
    )
    print("✅ SoF Pipeline modules imported successfully")
except ImportError as e:
    print(f"⚠️ Warning: SoF Pipeline modules failed to import: {e}")
    process_uploaded_files = None
    extract_events_and_summary = None
    calculate_laytime = None
    process_clicked_pdf_enhanced = None
    SofLaytimeResult = None

# Import authentication modules
from utils.auth import (
    get_password_hash, verify_password, create_access_token, 
    get_current_user, validate_password_strength, validate_email,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from utils.user_models import (
    User, UserCreate, UserLogin, UserResponse, Token,
    user_db
)
from models.sof_models import (
    UploadRequest, EventData, VoyageSummary, LaytimeCalculation,
    LaytimeResult, ProcessingResult, JobStatus as JobStatusModel
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SoF Event Extractor API with Authentication",
    description="AI-powered maritime document processing for Statement of Facts with user authentication",
    version="2.0.0"
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
UPLOAD_DIR = Path("uploads")
RESULTS_DIR = Path("results")
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# No longer need these old processors - using integrated SoF pipeline
print("🚀 Using integrated SoF Pipeline for document processing")

# In-memory job storage (use database in production)
jobs = {}

class JobStatus:
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "SoF Event Extractor API is running", "status": "healthy"}

# Authentication endpoints
@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_create: UserCreate):
    """Register a new user"""
    try:
        # Validate email format
        if not validate_email(user_create.email):
            raise HTTPException(
                status_code=400,
                detail="Invalid email format"
            )
        
        # Validate password strength
        if not validate_password_strength(user_create.password):
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters long and contain uppercase, lowercase, and numeric characters"
            )
        
        # Hash password
        hashed_password = get_password_hash(user_create.password)
        
        # Create user
        user = user_db.create_user(user_create, hashed_password)
        
        # Return user response (without password)
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/api/auth/login", response_model=Token)
async def login(user_login: UserLogin):
    """Authenticate user and return JWT token"""
    try:
        # Get user from database
        user = user_db.get_user_by_username(user_login.username)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password"
            )
        
        # Verify password
        if not verify_password(user_login.password, user.hashed_password):
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, 
            expires_delta=access_token_expires
        )
        
        # Update last login
        user_db.update_last_login(user.username)
        
        # Get updated user info
        updated_user = user_db.get_user_by_username(user.username)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=updated_user.id,
                username=updated_user.username,
                email=updated_user.email,
                full_name=updated_user.full_name,
                is_active=updated_user.is_active,
                created_at=updated_user.created_at,
                last_login=updated_user.last_login
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: str = Depends(get_current_user)):
    """Get current user information"""
    user = user_db.get_user_by_username(current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )

@app.get("/api/auth/users", response_model=List[UserResponse])
async def list_users(current_user: str = Depends(get_current_user)):
    """List all users (admin endpoint)"""
    # In production, add admin role check here
    return user_db.get_all_users()

# Job status enumeration 
class JobStatus:
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"

# Create a simple file-like object from upload
class FileUpload:
    def __init__(self, content: bytes, name: str):
        self.content = content
        self.name = name
        
    def read(self):
        return self.content
    
    def getvalue(self):
        return self.content

async def process_document_with_sof_pipeline(job_id: str, file_path: Path, filename: str, use_enhanced_processing: bool = False):
    """
    Process document using the new integrated SoF pipeline
    """
    try:
        logger.info(f"🚀 Processing document {filename} with SoF Pipeline (enhanced: {use_enhanced_processing})")
        
        # Get API key for Gemini
        gemini_api_key = os.getenv("GOOGLE_API_KEY", "")
        if not gemini_api_key:
            logger.warning("⚠️ No Google API key found, processing will be limited")
        
        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Create file upload object
        file_upload = FileUpload(file_content, filename)
        
        # Determine file type and process accordingly
        file_extension = filename.lower().split('.')[-1]
        
        if use_enhanced_processing and file_extension == 'pdf':
            # Use specialized clicked PDF processing
            logger.info("🎯 Using enhanced clicked PDF processing")
            
            if not gemini_api_key:
                raise Exception("Enhanced processing requires Google API key")
            
            events_df, summary_data = process_clicked_pdf_enhanced(file_content, filename, gemini_api_key)
            
        else:
            # Use standard SoF pipeline processing
            logger.info("📄 Using standard SoF pipeline processing")
            
            # Process uploaded files
            docs = process_uploaded_files([file_upload])
            
            if not docs:
                raise Exception("No text could be extracted from the document")
            
            # Extract events and summary
            if gemini_api_key:
                events_df, summary_data = extract_events_and_summary(docs, gemini_api_key)
            else:
                # Fallback without Gemini
                logger.warning("⚠️ No Gemini API key - using text extraction only")
                events_df = pd.DataFrame()
                summary_data = {}
        
        # Convert DataFrame to list of dictionaries for JSON serialization
        if not events_df.empty:
            events_list = events_df.to_dict('records')
            # Convert any Timestamp objects to strings
            for event in events_list:
                for key, value in event.items():
                    if pd.isna(value):
                        event[key] = None
                    elif hasattr(value, 'isoformat'):
                        event[key] = value.isoformat()
                    else:
                        event[key] = str(value) if value is not None else None
        else:
            events_list = []
            logger.warning("No events extracted from document")
        
        # Save results
        result_data = {
            "events": events_list,
            "summary": summary_data,
            "has_laytime_data": len(events_list) > 0 and any(event.get('laytime_counts') for event in events_list)
        }
        
        result_file = RESULTS_DIR / f"{job_id}_results.json"
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2, default=str)
        
        # Update job status
        jobs[job_id].update({
            "status": JobStatus.COMPLETED,
            "events": events_list,
            "summary": summary_data,
            "has_laytime_data": result_data["has_laytime_data"],
            "processed_at": datetime.now().isoformat(),
            "result_file": str(result_file)
        })
        
        logger.info(f"✅ Document {filename} processed successfully: {len(events_list)} events, summary: {bool(summary_data)}")
        
    except Exception as e:
        logger.error(f"💥 Document processing failed for {filename}: {e}")
        jobs[job_id].update({
            "status": JobStatus.FAILED,
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        })

@app.post("/api/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    use_enhanced_processing: bool = False,
    current_user: str = Depends(get_current_user)
):
    """
    Upload and process a maritime document using the integrated SoF pipeline
    """
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.doc', '.txt', '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp'}
        file_extension = '.' + file.filename.lower().split('.')[-1]
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_extension}. Supported types: {', '.join(allowed_extensions)}"
            )
        
        # Validate file size (10MB limit)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        # Save uploaded file
        job_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Create job entry
        jobs[job_id] = {
            "job_id": job_id,
            "status": JobStatus.PROCESSING,
            "user": current_user,
            "filename": file.filename,
            "file_path": str(file_path),
            "use_enhanced_processing": use_enhanced_processing,
            "created_at": datetime.now().isoformat()
        }
        
        # Start background processing
        background_tasks.add_task(
            process_document_with_sof_pipeline, 
            job_id, 
            file_path, 
            file.filename,
            use_enhanced_processing
        )
        
        logger.info(f"📤 Document upload initiated: {file.filename} (enhanced: {use_enhanced_processing})")
        
        return {
            "message": "File uploaded successfully",
            "job_id": job_id,
            "filename": file.filename,
            "enhanced_processing": use_enhanced_processing
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/calculate-laytime")
async def calculate_laytime_endpoint(
    laytime_data: LaytimeCalculation,
    current_user: str = Depends(get_current_user)
):
    """
    Calculate laytime based on voyage summary and events data
    """
    try:
        # Convert events data to DataFrame format expected by the pipeline
        events_df = pd.DataFrame(laytime_data.events)
        
        if events_df.empty:
            raise HTTPException(status_code=400, detail="No events provided for calculation")
        
        # Perform laytime calculation using the SoF pipeline
        laytime_result = calculate_laytime(laytime_data.summary, events_df)
        
        # Convert result to API response format
        result = {
            "laytime_allowed_days": laytime_result.laytime_allowed_days,
            "laytime_consumed_days": laytime_result.laytime_consumed_days,
            "laytime_saved_days": laytime_result.laytime_saved_days,
            "demurrage_due": laytime_result.demurrage_due,
            "dispatch_due": laytime_result.dispatch_due,
            "calculation_log": laytime_result.calculation_log,
            "events_with_calculations": laytime_result.events_df.to_dict('records') if not laytime_result.events_df.empty else []
        }
        
        logger.info(f"💰 Laytime calculated: allowed={laytime_result.laytime_allowed_days:.4f}, consumed={laytime_result.laytime_consumed_days:.4f}")
        
        return result
        
    except Exception as e:
        logger.error(f"Laytime calculation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Laytime calculation failed: {str(e)}")

@app.get("/api/result/{job_id}")
async def get_result(job_id: str, current_user: str = Depends(get_current_user)):
    """
    Get processing results for a specific job (user can only access their own jobs)
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    # Check if user owns this job
    if job.get("user") != current_user:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if job["status"] == JobStatus.PROCESSING:
        return {
            "job_id": job_id,
            "status": JobStatus.PROCESSING,
            "message": "Document is still being processed"
        }
    elif job["status"] == JobStatus.FAILED:
        return {
            "job_id": job_id,
            "status": JobStatus.FAILED,
            "error": job["error"]
        }
    else:
        return {
            "job_id": job_id,
            "status": JobStatus.COMPLETED,
            "filename": job["filename"],
            "events": job["events"],
            "summary": job.get("summary", {}),
            "has_laytime_data": job.get("has_laytime_data", False),
            "processed_at": job["processed_at"]
        }

@app.get("/api/status/{job_id}")
async def get_status(job_id: str, current_user: str = Depends(get_current_user)):
    """
    Get processing status for a specific job (user can only access their own jobs)
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    # Check if user owns this job
    if job.get("user") != current_user:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "filename": job["filename"],
        "created_at": job["created_at"]
    }

@app.post("/api/export/{job_id}")
async def export_data(
    job_id: str, 
    export_format: str = Query("csv", alias="type", description="Export format: csv or json"),
    current_user: str = Depends(get_current_user)
):
    """
    Export processed events as CSV or JSON
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    # Check if user owns this job
    if job.get("user") != current_user:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    events = job["events"]
    if not events:
        raise HTTPException(status_code=404, detail="No events found")
    
    # Additional debugging to understand the exact structure
    logger.info(f"🔍 DETAILED DEBUG - Raw events data:")
    logger.info(f"🔍 Type: {type(events)}")
    logger.info(f"🔍 Length: {len(events) if events else 0}")
    if events and len(events) > 0:
        logger.info(f"🔍 First element type: {type(events[0])}")
        logger.info(f"🔍 First element: {events[0]}")
        if isinstance(events[0], dict):
            logger.info(f"🔍 First element keys: {list(events[0].keys())}")
        elif isinstance(events[0], str):
            logger.info(f"🔍 First element is STRING - this is the problem!")
            logger.info(f"🔍 String content: {events[0][:200]}...")

    try:
        # Debug: Print the structure of events data
        logger.info(f"🔍 Debug - Events type: {type(events)}")
        logger.info(f"🔍 Debug - Events length: {len(events) if events else 0}")
        if events and len(events) > 0:
            logger.info(f"🔍 Debug - First event type: {type(events[0])}")
            logger.info(f"🔍 Debug - First event keys: {list(events[0].keys()) if isinstance(events[0], dict) else 'Not a dict'}")
            logger.info(f"🔍 Debug - First event sample: {str(events[0])[:200]}...")
        
        if export_format.lower() == "csv":
            # Convert to DataFrame and export as CSV
            df = pd.DataFrame(events)
            csv_file = RESULTS_DIR / f"{job_id}_export.csv"
            df.to_csv(csv_file, index=False)
            
            return FileResponse(
                csv_file,
                media_type='text/csv',
                filename=f"sof_events_{job_id[:8]}.csv"
            )
        
        elif export_format.lower() == "json":
            # Export as JSON with proper datetime handling
            import json
            
            class DateTimeEncoder(json.JSONEncoder):
                def default(self, obj):
                    if pd.isna(obj):
                        return None
                    if hasattr(obj, 'isoformat'):
                        return obj.isoformat()
                    return super().default(obj)
            
            # Clean the events data for JSON export
            logger.info(f"📄 Creating JSON export for {len(events)} events")
            logger.info(f"🔍 Debug - Events type: {type(events)}")
            
            if events and len(events) > 0:
                logger.info(f"🔍 Debug - First event type: {type(events[0])}")
                logger.info(f"🔍 Debug - First event sample: {str(events[0])[:200]}...")
            
            clean_events = []
            for event in events:
                clean_event = {}
                for key, value in event.items():
                    if pd.isna(value) or value is None or value == '':
                        clean_event[key] = None
                    elif isinstance(value, pd.Timestamp):
                        clean_event[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                    elif isinstance(value, datetime):
                        clean_event[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                    elif hasattr(value, 'isoformat'):
                        clean_event[key] = value.isoformat()
                    else:
                        clean_event[key] = str(value)
                clean_events.append(clean_event)
            
            logger.info(f"🔍 Debug - Clean events length: {len(clean_events)}")
            if clean_events:
                logger.info(f"🔍 Debug - First clean event: {str(clean_events[0])[:300]}...")
            
            json_file = RESULTS_DIR / f"{job_id}_export.json"
            logger.info(f"🔍 Debug - Writing to file: {json_file}")
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(clean_events, f, indent=2, cls=DateTimeEncoder, ensure_ascii=False)
            
            # Debug: Verify file content
            logger.info(f"🔍 Debug - File size: {json_file.stat().st_size} bytes")
            with open(json_file, 'r', encoding='utf-8') as f:
                file_content = f.read(500)
                logger.info(f"🔍 Debug - File content start: {file_content}")
            
            return FileResponse(
                json_file,
                media_type='application/json',
                filename=f"sof_events_{job_id[:8]}.json"
            )
        
        else:
            raise HTTPException(status_code=400, detail="Invalid export format. Use 'csv' or 'json'")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/api/jobs")
async def list_jobs(current_user: str = Depends(get_current_user)):
    """
    List all processing jobs for the current user
    """
    user_jobs = []
    for job_id, job in jobs.items():
        if job.get("user") == current_user:
            user_jobs.append({
                "job_id": job_id,
                "status": job["status"],
                "filename": job["filename"],
                "created_at": job["created_at"]
            })
    
    return {"jobs": user_jobs}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
