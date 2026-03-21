"""
FastAPI REST API for Grammar Scoring Engine
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import (
    API_HOST, API_PORT, CORS_ORIGINS, MODELS_DIR,
    BASE_DIR, SAMPLE_RATE
)
from preprocessing import validate_audio, preprocess_audio, get_audio_duration
from transcription import get_transcription_service
from model import get_scorer, GrammarScorer
from correction import get_corrector
from database import (
    authenticate_user,
    create_user,
    get_analysis_history,
    is_db_available,
    save_analysis,
)


# Initialize FastAPI app
app = FastAPI(
    title="Grammar Scoring Engine API",
    description="API for evaluating grammatical quality of spoken English audio",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary upload directory
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Global instances (lazy loaded)
_transcription_service = None
_scorer = None
_corrector = None


def get_services():
    """Get or initialize global services"""
    global _transcription_service, _scorer, _corrector
    if _transcription_service is None:
        _transcription_service = get_transcription_service()
    if _scorer is None:
        model_path = MODELS_DIR / "deberta_classifier.pt"
        _scorer = GrammarScorer(model_path if model_path.exists() else None)
    if _corrector is None:
        _corrector = get_corrector()
    return _transcription_service, _scorer, _corrector


# Response models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    model_loaded: bool


class ScoreResponse(BaseModel):
    success: bool
    filename: str
    duration: float
    transcript: str
    score: float
    predicted_class: float
    confidence: float
    processing_time: float


class ErrorResponse(BaseModel):
    success: bool
    error: str


class ModelInfoResponse(BaseModel):
    model_name: str
    num_labels: int
    score_range: list
    model_loaded: bool


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AnalysisSaveRequest(BaseModel):
    email: str
    analysis: Dict[str, Any]


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Check API health status"""
    _, scorer, corrector = get_services()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model_loaded": scorer.model is not None,
        "grammar_correction_available": getattr(corrector, "_is_available", False),
        "database_available": is_db_available(),
    }


@app.post("/api/auth/signup")
async def signup(payload: SignupRequest):
    result = create_user(payload.name, payload.email, payload.password)
    if not result["success"]:
        message = result.get("error", "Signup failed")
        if "MongoDB" in message:
            raise HTTPException(status_code=503, detail=message)
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "user": result["user"]}


@app.post("/api/auth/login")
async def login(payload: LoginRequest):
    result = authenticate_user(payload.email, payload.password)
    if not result["success"]:
        message = result.get("error", "Invalid credentials")
        if "MongoDB" in message:
            raise HTTPException(status_code=503, detail=message)
        raise HTTPException(status_code=401, detail=message)
    return {"success": True, "user": result["user"]}


@app.get("/api/analysis/history")
async def analysis_history(email: str = Query(..., min_length=3), limit: int = Query(100, ge=1, le=300)):
    if not is_db_available():
        raise HTTPException(status_code=503, detail="MongoDB is not configured or reachable.")
    history = get_analysis_history(email=email, limit=limit)
    return {"success": True, "history": history}


@app.post("/api/analysis/history")
async def store_analysis(payload: AnalysisSaveRequest):
    result = save_analysis(payload.email, payload.analysis)
    if not result["success"]:
        raise HTTPException(status_code=503, detail=result.get("error", "Failed to save analysis"))
    return {"success": True, "record": result["record"]}


@app.get("/api/models/info", response_model=ModelInfoResponse)
async def model_info():
    """Get model information"""
    _, scorer, corrector = get_services()
    return {
        "model_name": "microsoft/deberta-v3-base",
        "num_labels": 11,
        "score_range": [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5],
        "model_loaded": scorer.model is not None,
        "grammar_correction_available": getattr(corrector, "_is_available", False)
    }


@app.post("/api/predict")
async def predict_grammar_score(file: UploadFile = File(...)):
    """
    Upload an audio file and get its grammar score
    
    - **file**: Audio file in WAV format (45-60 seconds recommended)
    
    Returns grammar score (0-5) with confidence and transcript
    """
    import time
    start_time = time.time()
    
    # Validate file type
    if not file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.ogg', '.flac')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Supported formats: WAV, MP3, M4A, OGG, FLAC"
        )
    
    # Save uploaded file
    file_id = str(uuid.uuid4())[:8]
    temp_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    
    try:
        with open(temp_path, 'wb') as f:
            shutil.copyfileobj(file.file, f)
        
        print(f"\n{'='*60}")
        print(f"Processing new audio: {file.filename}")
        print(f"Temporary path: {temp_path}")
        print(f"File size: {temp_path.stat().st_size} bytes")
        print(f"{'='*60}\n")
        
        # Validate audio
        is_valid, message = validate_audio(temp_path)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)
        
        # Get services
        transcription_service, scorer, corrector = get_services()
        
        # Get audio duration
        duration = get_audio_duration(temp_path)
        print(f"Audio duration: {duration:.2f}s")
        
        # Transcribe audio
        print("Starting transcription...")
        transcript_result = transcription_service.transcribe(temp_path, use_cache=False)
        transcript = transcript_result['text']
        print(f"Transcript: {transcript[:100]}...")  # Print first 100 chars
        
        if not transcript.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not detect speech in audio. Please ensure the audio contains clear speech."
            )
        
        # Score transcript
        print("\nScoring transcript...")
        score_result = scorer.score_text(transcript)
        print(f"Score: {score_result['score']}, Confidence: {score_result['confidence']:.3f}")

        # Grammar correction
        print("Running grammar correction...")
        correction_result = corrector.correct_text(transcript)
        print(f"{'='*60}\n")
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "filename": file.filename,
            "duration": round(duration, 2),
            "transcript": transcript,
            "corrected_text": correction_result["corrected_text"],
            "correction_changed": correction_result["changed"],
            "correction_available": correction_result["available"],
            "correction_error": correction_result["error"],
            "score": score_result['score'],
            "predicted_class": score_result['predicted_class'],
            "confidence": score_result['confidence'],
            "class_probabilities": score_result.get('class_probabilities', {}),
            "processing_time": round(processing_time, 2)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"\n❌ ERROR: {error_msg}")
        print(f"Traceback:\n{error_trace}\n")
        raise HTTPException(status_code=500, detail=f"Processing error: {error_msg}")
    
    finally:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()


@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe audio file without scoring
    
    - **file**: Audio file in WAV format
    
    Returns transcript only
    """
    # Validate file type
    if not file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.ogg', '.flac')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Supported formats: WAV, MP3, M4A, OGG, FLAC"
        )
    
    # Save uploaded file
    file_id = str(uuid.uuid4())[:8]
    temp_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    
    try:
        with open(temp_path, 'wb') as f:
            shutil.copyfileobj(file.file, f)
        
        # Validate audio
        is_valid, message = validate_audio(temp_path)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)
        
        # Get transcription service
        transcription_service, _, _ = get_services()
        
        # Transcribe
        result = transcription_service.transcribe(temp_path, use_cache=False)
        
        return {
            "success": True,
            "filename": file.filename,
            "transcript": result['text'],
            "duration": result['duration'],
            "language": result['language'],
            "segments": result.get('segments', [])
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")
    
    finally:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()


@app.post("/api/score-text")
async def score_text(text: str):
    """
    Score text directly without transcription
    
    - **text**: Text to score for grammatical quality
    
    Returns grammar score (0-5) with confidence and error analysis
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    _, scorer, corrector = get_services()
    result = scorer.score_text(text)
    correction_result = corrector.correct_text(text)
    
    return {
        "success": True,
        "text": text,
        "corrected_text": correction_result["corrected_text"],
        "correction_changed": correction_result["changed"],
        "correction_available": correction_result["available"],
        "correction_error": correction_result["error"],
        "errors": correction_result.get("errors", []),
        "suggestions": correction_result.get("suggestions", []),
        "error_summary": correction_result.get("summary", {"total_errors": 0}),
        "score": result['score'],
        "predicted_class": result['predicted_class'],
        "confidence": result['confidence'],
        "class_probabilities": result.get('class_probabilities', {})
    }


@app.post("/api/correct-grammar")
async def correct_grammar(text: str):
    """
    Correct grammar in text without scoring.

    - **text**: Text to correct for grammar

    Returns corrected text with error analysis and correction metadata
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    _, _, corrector = get_services()
    result = corrector.correct_text(text)

    return {
        "success": True,
        "text": text,
        "corrected_text": result["corrected_text"],
        "correction_changed": result["changed"],
        "correction_available": result["available"],
        "correction_error": result["error"],
        "errors": result.get("errors", []),
        "suggestions": result.get("suggestions", []),
        "error_summary": result.get("summary", {"total_errors": 0}),
    }


# Serve frontend static files
frontend_path = BASE_DIR / "frontend" / "dist"
if frontend_path.exists():
    from fastapi.responses import FileResponse
    import mimetypes
    
    # Ensure common mimetypes are registered
    mimetypes.add_type('application/javascript', '.js')
    mimetypes.add_type('text/css', '.css')

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Don't handle API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
            
        # If no path specified, serve index.html
        if not full_path or full_path == "/":
            return FileResponse(str(frontend_path / "index.html"))
            
        # Check if the file exists in dist
        file_path = frontend_path / full_path
        if file_path.is_file():
            # Explicitly set media type for important assets
            media_type = None
            if full_path.endswith('.js'):
                media_type = 'application/javascript'
            elif full_path.endswith('.css'):
                media_type = 'text/css'
            
            return FileResponse(str(file_path), media_type=media_type)
        
        # If it's a path without an extension, serve index.html (SPA routing)
        if "." not in full_path:
            return FileResponse(str(frontend_path / "index.html"))
            
        # For missing files with extensions, 404
        raise HTTPException(status_code=404)
else:
    # Use fallback if dist isn't found
    source_path = BASE_DIR / "frontend"
    if source_path.exists():
        app.mount("/", StaticFiles(directory=str(source_path), html=True), name="frontend")


def run_server():
    """Run the API server"""
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)


if __name__ == "__main__":
    run_server()
