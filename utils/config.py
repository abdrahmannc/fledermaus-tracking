"""
Configuration management for fledermaus tracking application.
"""
import os
from typing import Dict, Any
from pydantic import BaseSettings, Field
import logging

logger = logging.getLogger(__name__)


class VideoProcessingConfig(BaseSettings):
    """Configuration for video processing parameters."""
    
    # FPS handling
    default_fps: float = Field(default=30.0, description="Default FPS when video FPS is invalid")
    min_fps: float = Field(default=1.0, description="Minimum acceptable FPS")
    max_fps: float = Field(default=120.0, description="Maximum acceptable FPS")
    
    # Contour processing
    min_contour_area: float = Field(default=50.0, description="Minimum contour area for detection")
    max_contour_area: float = Field(default=10000.0, description="Maximum contour area for detection")
    
    # Video validation
    min_video_width: int = Field(default=100, description="Minimum video width")
    min_video_height: int = Field(default=100, description="Minimum video height")
    max_video_width: int = Field(default=4096, description="Maximum video width")
    max_video_height: int = Field(default=4096, description="Maximum video height")
    
    # Processing parameters
    background_subtractor_threshold: float = Field(default=16.0, description="Background subtraction threshold")
    gaussian_blur_kernel: int = Field(default=5, description="Gaussian blur kernel size")
    morphology_kernel_size: int = Field(default=3, description="Morphology operation kernel size")
    
    # Error handling
    max_processing_errors: int = Field(default=10, description="Maximum processing errors before stopping")
    error_recovery_enabled: bool = Field(default=True, description="Enable error recovery mechanisms")
    
    class Config:
        env_prefix = "FLEDERMAUS_"
        case_sensitive = False


class AppConfig(BaseSettings):
    """Main application configuration."""
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="fledermaus.log", description="Log file path")
    
    # Upload settings
    max_file_size: int = Field(default=100 * 1024 * 1024, description="Maximum file size in bytes (100MB)")
    allowed_extensions: list = Field(default=[".mp4", ".avi", ".mov", ".mkv"], description="Allowed video extensions")
    upload_dir: str = Field(default="uploads", description="Upload directory")
    
    # Video processing
    video_config: VideoProcessingConfig = Field(default_factory=VideoProcessingConfig)
    
    class Config:
        env_prefix = "FLEDERMAUS_"
        case_sensitive = False


def get_config() -> AppConfig:
    """Get application configuration."""
    return AppConfig()


def setup_logging(config: AppConfig) -> None:
    """Setup logging configuration."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(config.log_file)
        ]
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)


def validate_config(config: AppConfig) -> bool:
    """
    Validate configuration parameters.
    
    Args:
        config: Application configuration
        
    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        # Validate upload directory
        os.makedirs(config.upload_dir, exist_ok=True)
        
        # Validate video processing parameters
        video_config = config.video_config
        
        if video_config.default_fps <= 0:
            logger.error("Default FPS must be positive")
            return False
            
        if video_config.min_contour_area < 0:
            logger.error("Minimum contour area must be non-negative")
            return False
            
        if video_config.min_video_width <= 0 or video_config.min_video_height <= 0:
            logger.error("Minimum video dimensions must be positive")
            return False
            
        logger.info("Configuration validation successful")
        return True
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False


# Global configuration instance
config = get_config()