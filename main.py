"""
Main FastAPI application for fledermaus tracking with robust error handling.
"""
import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import tempfile
import time

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from utils.config import get_config, setup_logging, validate_config
from detection.video_detector import VideoDetector
from utils.safe_math import validate_numeric_range

# Setup configuration and logging
config = get_config()
setup_logging(config)
logger = logging.getLogger(__name__)

# Validate configuration
if not validate_config(config):
    logger.error("Configuration validation failed")
    exit(1)

# Create FastAPI app
app = FastAPI(
    title="Fledermaus Tracking API",
    description="Video analysis API for bat detection and tracking",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize video detector
detector = VideoDetector(config.video_config)


class AnalysisRequest(BaseModel):
    """Request model for video analysis."""
    start_time: Optional[float] = 0
    end_time: Optional[float] = None
    upload_sensitivity: Optional[float] = 1.0


class AnalysisResponse(BaseModel):
    """Response model for video analysis."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[list] = None


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler to prevent crashes."""
    error_msg = f"Unexpected error: {str(exc)}"
    logger.error(f"Unhandled exception: {error_msg}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error occurred",
            "error": error_msg if config.debug else "An unexpected error occurred"
        }
    )


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "Fledermaus Tracking API",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Perform basic system checks
        checks = {
            "api": True,
            "config": validate_config(config),
            "upload_dir": Path(config.upload_dir).exists(),
            "detector": detector is not None
        }
        
        all_healthy = all(checks.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "checks": checks,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )


def validate_video_file(file: UploadFile) -> tuple[bool, str]:
    """
    Validate uploaded video file.
    
    Args:
        file: Uploaded file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check file size
        if file.size and file.size > config.max_file_size:
            return False, f"File size {file.size} exceeds maximum {config.max_file_size} bytes"
        
        # Check file extension
        if file.filename:
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in config.allowed_extensions:
                return False, f"File extension {file_ext} not allowed. Allowed: {config.allowed_extensions}"
        else:
            return False, "Filename is required"
        
        # Check content type
        if not file.content_type or not file.content_type.startswith('video/'):
            logger.warning(f"Unexpected content type: {file.content_type}")
            # Don't fail here as content type might be incorrect but file might be valid
        
        return True, ""
        
    except Exception as e:
        error_msg = f"File validation error: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def save_uploaded_file(file: UploadFile) -> tuple[bool, str, Optional[str]]:
    """
    Safely save uploaded file to disk.
    
    Args:
        file: Uploaded file
        
    Returns:
        Tuple of (success, message, file_path)
    """
    temp_path = None
    try:
        # Create upload directory
        os.makedirs(config.upload_dir, exist_ok=True)
        
        # Create temporary file
        file_ext = Path(file.filename).suffix.lower()
        temp_fd, temp_path = tempfile.mkstemp(suffix=file_ext, dir=config.upload_dir)
        
        try:
            # Write file content
            with os.fdopen(temp_fd, 'wb') as temp_file:
                shutil.copyfileobj(file.file, temp_file)
            
            logger.info(f"File saved successfully: {temp_path}")
            return True, "File saved successfully", temp_path
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e
            
    except Exception as e:
        error_msg = f"Error saving file: {str(e)}"
        logger.error(error_msg)
        return False, error_msg, None


def cleanup_file(file_path: str) -> None:
    """Safely clean up temporary file."""
    try:
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.warning(f"Could not clean up file {file_path}: {e}")


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_video(
    file: UploadFile = File(...),
    start_time: float = Form(default=0),
    end_time: Optional[float] = Form(default=None),
    upload_sensitivity: float = Form(default=1.0)
):
    """
    Analyze uploaded video for bat detection.
    
    Args:
        file: Video file to analyze
        start_time: Start time in seconds
        end_time: End time in seconds (optional)
        upload_sensitivity: Detection sensitivity (currently unused)
        
    Returns:
        Analysis results or error response
    """
    temp_file_path = None
    
    try:
        logger.info(f"Starting video analysis for file: {file.filename}")
        
        # Validate input parameters
        start_time = validate_numeric_range(start_time, 0, 86400, 0, "start_time")  # Max 24 hours
        if end_time is not None:
            end_time = validate_numeric_range(end_time, start_time, 86400, None, "end_time")
        upload_sensitivity = validate_numeric_range(upload_sensitivity, 0.1, 10.0, 1.0, "upload_sensitivity")
        
        # Validate uploaded file
        is_valid, validation_error = validate_video_file(file)
        if not is_valid:
            logger.warning(f"File validation failed: {validation_error}")
            return AnalysisResponse(
                success=False,
                message=f"File validation failed: {validation_error}",
                errors=[validation_error]
            )
        
        # Save uploaded file
        save_success, save_message, temp_file_path = save_uploaded_file(file)
        if not save_success:
            logger.error(f"File save failed: {save_message}")
            return AnalysisResponse(
                success=False,
                message=f"File save failed: {save_message}",
                errors=[save_message]
            )
        
        # Analyze video
        try:
            analysis_result = detector.analyze_video(temp_file_path, start_time, end_time)
            
            # Convert analysis result to response format
            response_data = {
                "totalFrames": analysis_result.total_frames,
                "batDetected": analysis_result.bat_detected,
                "detectionCount": analysis_result.detection_count,
                "startPoint": {
                    "x": analysis_result.start_point[0] if analysis_result.start_point else 0,
                    "y": analysis_result.start_point[1] if analysis_result.start_point else 0
                } if analysis_result.start_point else None,
                "endPoint": {
                    "x": analysis_result.end_point[0] if analysis_result.end_point else 0,
                    "y": analysis_result.end_point[1] if analysis_result.end_point else 0
                } if analysis_result.end_point else None,
                "analysisTime": analysis_result.analysis_time,
                "fps": analysis_result.fps,
                "videoDuration": analysis_result.video_duration,
                "positions": [
                    {
                        "frame": pos.frame_number,
                        "x": pos.center_x,
                        "y": pos.center_y,
                        "width": pos.width,
                        "height": pos.height,
                        "timestamp": f"00:{int(pos.timestamp // 60):02d}:{int(pos.timestamp % 60):02d}"
                    }
                    for pos in analysis_result.positions
                ],
                "movementsPerFrame": analysis_result.movements_per_frame
            }
            
            # Determine success based on errors
            has_critical_errors = len(analysis_result.errors_encountered) > 0
            success_message = (
                "Analysis completed successfully" if not has_critical_errors
                else f"Analysis completed with {len(analysis_result.errors_encountered)} warnings"
            )
            
            logger.info(f"Analysis completed: {analysis_result.detection_count} detections found")
            
            return AnalysisResponse(
                success=True,
                message=success_message,
                data=response_data,
                errors=analysis_result.errors_encountered if has_critical_errors else None
            )
            
        except Exception as analysis_error:
            error_msg = f"Video analysis failed: {str(analysis_error)}"
            logger.error(error_msg, exc_info=True)
            
            return AnalysisResponse(
                success=False,
                message="Video analysis failed",
                errors=[error_msg]
            )
        
    except Exception as e:
        error_msg = f"Request processing failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return AnalysisResponse(
            success=False,
            message="Request processing failed",
            errors=[error_msg]
        )
        
    finally:
        # Clean up temporary file
        if temp_file_path:
            cleanup_file(temp_file_path)


if __name__ == "__main__":
    try:
        logger.info("Starting Fledermaus Tracking API server...")
        logger.info(f"Configuration: Debug={config.debug}, Host={config.host}, Port={config.port}")
        
        uvicorn.run(
            app,
            host=config.host,
            port=config.port,
            log_level=config.log_level.lower(),
            reload=config.debug
        )
        
    except Exception as e:
        logger.critical(f"Failed to start server: {e}")
        exit(1)