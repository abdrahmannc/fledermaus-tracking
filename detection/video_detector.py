"""
Video detector for fledermaus tracking with robust error handling.
Prevents division by zero errors and handles edge cases gracefully.
"""
import cv2
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from utils.safe_math import (
    safe_divide, safe_fps_calculation, safe_contour_center, 
    validate_numeric_range
)
from utils.config import VideoProcessingConfig

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """Result of bat detection in a frame."""
    frame_number: int
    timestamp: float
    center_x: float
    center_y: float
    width: float
    height: float
    area: float
    confidence: float = 1.0


@dataclass
class VideoAnalysisResult:
    """Complete video analysis result."""
    total_frames: int
    bat_detected: bool
    detection_count: int
    start_point: Optional[Tuple[float, float]]
    end_point: Optional[Tuple[float, float]]
    analysis_time: str
    positions: List[DetectionResult]
    movements_per_frame: List[Dict[str, Any]]
    fps: float
    video_duration: float
    errors_encountered: List[str]


class VideoDetector:
    """
    Robust video detector for bat tracking with comprehensive error handling.
    """
    
    def __init__(self, config: VideoProcessingConfig):
        self.config = config
        self.background_subtractor = None
        self.error_count = 0
        self.max_errors = config.max_processing_errors
        self.errors_log = []
        
    def validate_video_file(self, video_path: str) -> Tuple[bool, str]:
        """
        Validate video file integrity and properties.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not Path(video_path).exists():
                return False, f"Video file does not exist: {video_path}"
                
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False, f"Cannot open video file: {video_path}"
                
            # Check basic video properties
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            cap.release()
            
            # Validate dimensions
            if width < self.config.min_video_width or height < self.config.min_video_height:
                return False, f"Video dimensions too small: {width}x{height}"
                
            if width > self.config.max_video_width or height > self.config.max_video_height:
                return False, f"Video dimensions too large: {width}x{height}"
                
            # Validate frame count
            if frame_count <= 0:
                return False, "Video has no frames or invalid frame count"
                
            logger.info(f"Video validation successful: {width}x{height}, {frame_count} frames, {fps} FPS")
            return True, ""
            
        except Exception as e:
            error_msg = f"Video validation error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_safe_video_properties(self, cap: cv2.VideoCapture) -> Dict[str, float]:
        """
        Safely extract video properties with fallback values.
        
        Args:
            cap: OpenCV VideoCapture object
            
        Returns:
            Dictionary of video properties with safe values
        """
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            
            # Validate and fix FPS
            fps = validate_numeric_range(
                fps, self.config.min_fps, self.config.max_fps, 
                self.config.default_fps, "FPS"
            )
            
            # Validate frame count
            frame_count = max(1, int(frame_count)) if frame_count > 0 else 1
            
            # Calculate duration safely
            duration = safe_divide(frame_count, fps, default=0.0)
            
            properties = {
                'fps': fps,
                'frame_count': frame_count,
                'width': int(width),
                'height': int(height),
                'duration': duration
            }
            
            logger.info(f"Video properties: {properties}")
            return properties
            
        except Exception as e:
            logger.error(f"Error extracting video properties: {e}")
            return {
                'fps': self.config.default_fps,
                'frame_count': 1,
                'width': self.config.min_video_width,
                'height': self.config.min_video_height,
                'duration': 0.0
            }
    
    def setup_background_subtractor(self) -> None:
        """Setup background subtractor with error handling."""
        try:
            self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
                detectShadows=True,
                varThreshold=self.config.background_subtractor_threshold
            )
            logger.info("Background subtractor initialized successfully")
        except Exception as e:
            logger.error(f"Error setting up background subtractor: {e}")
            self.background_subtractor = None
    
    def process_frame_safely(self, frame: np.ndarray, frame_idx: int, fps: float) -> Optional[DetectionResult]:
        """
        Process a single frame with comprehensive error handling.
        
        Args:
            frame: Input frame
            frame_idx: Frame index
            fps: Video FPS
            
        Returns:
            DetectionResult if bat detected, None otherwise
        """
        try:
            if frame is None or frame.size == 0:
                logger.warning(f"Frame {frame_idx} is empty or invalid")
                return None
                
            # Apply background subtraction safely
            if self.background_subtractor is None:
                logger.warning("Background subtractor not available, skipping frame")
                return None
                
            fg_mask = self.background_subtractor.apply(frame)
            
            # Apply morphological operations safely
            try:
                kernel = cv2.getStructuringElement(
                    cv2.MORPH_ELLIPSE, 
                    (self.config.morphology_kernel_size, self.config.morphology_kernel_size)
                )
                fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
                fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
            except Exception as e:
                logger.warning(f"Morphological operations failed for frame {frame_idx}: {e}")
                # Continue with original mask
            
            # Find contours safely
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return None
                
            # Process contours with safe calculations
            best_contour = None
            best_area = 0
            
            for contour in contours:
                try:
                    area = cv2.contourArea(contour)
                    
                    # Validate contour area
                    if (self.config.min_contour_area <= area <= self.config.max_contour_area and 
                        area > best_area):
                        best_contour = contour
                        best_area = area
                        
                except Exception as e:
                    logger.warning(f"Error processing contour in frame {frame_idx}: {e}")
                    continue
            
            if best_contour is None:
                return None
                
            # Calculate contour properties safely
            try:
                moments = cv2.moments(best_contour)
                center_x, center_y = safe_contour_center(moments)
                
                # Get bounding rectangle safely
                x, y, w, h = cv2.boundingRect(best_contour)
                
                # Calculate timestamp safely
                timestamp = safe_fps_calculation(frame_idx, fps, self.config.default_fps)
                
                return DetectionResult(
                    frame_number=frame_idx,
                    timestamp=timestamp,
                    center_x=center_x,
                    center_y=center_y,
                    width=float(w),
                    height=float(h),
                    area=best_area
                )
                
            except Exception as e:
                logger.error(f"Error calculating contour properties for frame {frame_idx}: {e}")
                return None
                
        except Exception as e:
            self._handle_processing_error(f"Frame {frame_idx} processing error: {e}")
            return None
    
    def _handle_processing_error(self, error_msg: str) -> None:
        """Handle processing errors with counting and logging."""
        self.error_count += 1
        self.errors_log.append(error_msg)
        logger.error(error_msg)
        
        if self.error_count >= self.max_errors:
            raise RuntimeError(f"Too many processing errors ({self.error_count}). Last error: {error_msg}")
    
    def analyze_video(self, video_path: str, start_time: float = 0, 
                     end_time: Optional[float] = None) -> VideoAnalysisResult:
        """
        Analyze video for bat detection with comprehensive error handling.
        
        Args:
            video_path: Path to video file
            start_time: Start time in seconds
            end_time: End time in seconds (None for full video)
            
        Returns:
            VideoAnalysisResult with detection results
        """
        import time
        start_analysis_time = time.time()
        
        # Reset error tracking
        self.error_count = 0
        self.errors_log = []
        
        # Validate video file
        is_valid, error_msg = self.validate_video_file(video_path)
        if not is_valid:
            logger.error(f"Video validation failed: {error_msg}")
            return VideoAnalysisResult(
                total_frames=0,
                bat_detected=False,
                detection_count=0,
                start_point=None,
                end_point=None,
                analysis_time="00:00:00",
                positions=[],
                movements_per_frame=[],
                fps=self.config.default_fps,
                video_duration=0.0,
                errors_encountered=[error_msg]
            )
        
        cap = None
        try:
            # Open video capture
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise RuntimeError(f"Cannot open video: {video_path}")
            
            # Get video properties safely
            properties = self.get_safe_video_properties(cap)
            fps = properties['fps']
            total_frames = int(properties['frame_count'])
            duration = properties['duration']
            
            # Setup background subtractor
            self.setup_background_subtractor()
            
            # Calculate frame range
            start_frame = int(start_time * fps) if start_time > 0 else 0
            end_frame = int(end_time * fps) if end_time else total_frames
            
            start_frame = max(0, min(start_frame, total_frames - 1))
            end_frame = max(start_frame + 1, min(end_frame, total_frames))
            
            logger.info(f"Processing frames {start_frame} to {end_frame} (FPS: {fps})")
            
            # Process video frames
            detections = []
            movements_per_frame = []
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            for frame_idx in range(start_frame, end_frame):
                try:
                    ret, frame = cap.read()
                    if not ret:
                        logger.warning(f"Could not read frame {frame_idx}")
                        break
                    
                    detection = self.process_frame_safely(frame, frame_idx, fps)
                    
                    if detection:
                        detections.append(detection)
                    
                    # Track movements per frame
                    movements_per_frame.append({
                        'frame': frame_idx,
                        'count': 1 if detection else 0
                    })
                    
                except Exception as e:
                    self._handle_processing_error(f"Error processing frame {frame_idx}: {e}")
                    continue
            
            # Calculate results
            bat_detected = len(detections) > 0
            start_point = None
            end_point = None
            
            if detections:
                first_detection = detections[0]
                last_detection = detections[-1]
                start_point = (first_detection.center_x, first_detection.center_y)
                end_point = (last_detection.center_x, last_detection.center_y)
            
            # Calculate analysis time
            elapsed_time = time.time() - start_analysis_time
            analysis_time = f"{int(elapsed_time // 60):02d}:{int(elapsed_time % 60):02d}"
            
            result = VideoAnalysisResult(
                total_frames=end_frame - start_frame,
                bat_detected=bat_detected,
                detection_count=len(detections),
                start_point=start_point,
                end_point=end_point,
                analysis_time=analysis_time,
                positions=detections,
                movements_per_frame=movements_per_frame,
                fps=fps,
                video_duration=duration,
                errors_encountered=self.errors_log.copy()
            )
            
            logger.info(f"Video analysis completed: {len(detections)} detections in {analysis_time}")
            return result
            
        except Exception as e:
            error_msg = f"Video analysis failed: {str(e)}"
            logger.error(error_msg)
            self.errors_log.append(error_msg)
            
            # Return error result
            elapsed_time = time.time() - start_analysis_time
            analysis_time = f"{int(elapsed_time // 60):02d}:{int(elapsed_time % 60):02d}"
            
            return VideoAnalysisResult(
                total_frames=0,
                bat_detected=False,
                detection_count=0,
                start_point=None,
                end_point=None,
                analysis_time=analysis_time,
                positions=[],
                movements_per_frame=[],
                fps=self.config.default_fps,
                video_duration=0.0,
                errors_encountered=self.errors_log.copy()
            )
            
        finally:
            if cap is not None:
                cap.release()
                cv2.destroyAllWindows()