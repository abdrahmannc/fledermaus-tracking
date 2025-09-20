"""
Professional Error Handling and Logging System for Bat Detection Application

Provides structured logging, error tracking, and user-friendly error reporting
for robust production-ready operation.
"""

import logging
import sys
import os
import traceback
import time
from datetime import datetime
from pathlib import Path
import threading
from typing import Optional, Dict, Any, Callable


class BatDetectionLogger:
    """Professional logging system for bat detection application"""
    
    def __init__(self, log_dir: str = "logs"):
        """Initialize logging system with file and console handlers"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger("BatDetection")
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
        
        # Error tracking
        self.error_count = 0
        self.warning_count = 0
        self.last_error_time = None
        self.error_history = []
        
    def _setup_handlers(self):
        """Setup file and console logging handlers"""
        # File handler with rotation
        log_file = self.log_dir / f"bat_detection_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(thread)d] - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        file_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(simple_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **kwargs)
        
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.warning_count += 1
        self.logger.warning(message, **kwargs)
        
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception details"""
        self.error_count += 1
        self.last_error_time = time.time()
        
        error_info = {
            'message': message,
            'timestamp': time.time(),
            'thread': threading.current_thread().name
        }
        
        if exception:
            error_info['exception'] = str(exception)
            error_info['traceback'] = traceback.format_exc()
            message = f"{message} | Exception: {str(exception)}"
            
        self.error_history.append(error_info)
        
        # Keep only last 50 errors
        if len(self.error_history) > 50:
            self.error_history = self.error_history[-50:]
            
        self.logger.error(message, **kwargs)
        
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log critical error"""
        self.error(f"CRITICAL: {message}", exception, **kwargs)
        
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **kwargs)
        
    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        return {
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'last_error_time': self.last_error_time,
            'recent_errors': len(self.error_history),
            'log_dir': str(self.log_dir)
        }


class ErrorHandler:
    """Professional error handling with user feedback and recovery strategies"""
    
    def __init__(self, logger: BatDetectionLogger, gui_callback: Optional[Callable] = None):
        """Initialize error handler with logger and optional GUI callback"""
        self.logger = logger
        self.gui_callback = gui_callback
        self.recovery_strategies = {}
        
    def register_recovery_strategy(self, error_type: str, strategy: Callable):
        """Register a recovery strategy for specific error types"""
        self.recovery_strategies[error_type] = strategy
        
    def handle_error(self, 
                    error: Exception, 
                    context: str = "Unknown", 
                    user_message: Optional[str] = None,
                    recoverable: bool = False) -> bool:
        """
        Handle error with logging, user notification, and optional recovery
        
        Returns:
            bool: True if error was handled successfully, False if critical
        """
        error_type = type(error).__name__
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Log the error
        self.logger.error(f"[{context}] {error_type}", exception=error)
        
        # Prepare user-friendly message
        if user_message is None:
            user_message = self._generate_user_message(error, context)
            
        # Notify GUI if callback available
        if self.gui_callback:
            try:
                self.gui_callback(f"[{timestamp}] {user_message}")
            except Exception as gui_error:
                self.logger.error("Failed to update GUI", exception=gui_error)
                
        # Attempt recovery if strategy exists
        if recoverable and error_type in self.recovery_strategies:
            try:
                recovery_result = self.recovery_strategies[error_type](error, context)
                if recovery_result:
                    self.logger.info(f"Successfully recovered from {error_type} in {context}")
                    return True
            except Exception as recovery_error:
                self.logger.error(f"Recovery strategy failed for {error_type}", 
                                exception=recovery_error)
                
        return not self._is_critical_error(error)
        
    def _generate_user_message(self, error: Exception, context: str) -> str:
        """Generate user-friendly error message"""
        error_type = type(error).__name__
        
        messages = {
            'FileNotFoundError': 'Video file could not be found. Please check the file path.',
            'PermissionError': 'Permission denied. Please check file permissions.',
            'MemoryError': 'Insufficient memory. Try closing other applications.',
            'cv2.error': 'Video processing error. The video file may be corrupted.',
            'AttributeError': 'Internal component error. Please restart the application.',
            'ValueError': 'Invalid parameter detected. Please check your settings.',
            'ConnectionError': 'Network connection error during processing.',
            'TimeoutError': 'Operation timed out. The video may be too large.'
        }
        
        return messages.get(error_type, f"An unexpected error occurred during {context}")
        
    def _is_critical_error(self, error: Exception) -> bool:
        """Determine if error is critical and requires application shutdown"""
        critical_errors = [
            MemoryError,
            SystemError,
            KeyboardInterrupt,
            SystemExit
        ]
        return type(error) in critical_errors
        
    def safe_execute(self, 
                    func: Callable, 
                    context: str, 
                    fallback_result=None,
                    suppress_errors: bool = False) -> Any:
        """
        Safely execute a function with error handling
        
        Args:
            func: Function to execute
            context: Context description for logging
            fallback_result: Value to return if function fails
            suppress_errors: If True, don't show user messages for errors
            
        Returns:
            Function result or fallback_result if error occurred
        """
        try:
            return func()
        except Exception as e:
            if not suppress_errors:
                self.handle_error(e, context, recoverable=True)
            else:
                self.logger.debug(f"Suppressed error in {context}: {e}")
            return fallback_result


# Global logger instance
_logger = None

def get_logger() -> BatDetectionLogger:
    """Get or create global logger instance"""
    global _logger
    if _logger is None:
        _logger = BatDetectionLogger()
        _logger.info("Bat Detection Application Logger Initialized")
    return _logger


def setup_error_handling(gui_update_callback: Optional[Callable] = None) -> ErrorHandler:
    """Setup global error handling system"""
    logger = get_logger()
    error_handler = ErrorHandler(logger, gui_update_callback)
    
    # Register common recovery strategies
    def memory_recovery(error, context):
        """Recovery strategy for memory errors"""
        import gc
        gc.collect()
        logger.info("Performed garbage collection for memory recovery")
        return True
        
    def video_recovery(error, context):
        """Recovery strategy for video errors"""
        logger.info("Attempting video stream recovery")
        # Could implement video stream reset logic here
        return False
        
    error_handler.register_recovery_strategy('MemoryError', memory_recovery)
    error_handler.register_recovery_strategy('cv2.error', video_recovery)
    
    return error_handler


class PerformanceMonitor:
    """Monitor application performance and resource usage"""
    
    def __init__(self, logger: BatDetectionLogger):
        self.logger = logger
        self.metrics = {
            'frame_processing_times': [],
            'memory_usage': [],
            'cpu_usage': [],
            'start_time': time.time(),
            'frames_processed': 0,
            'errors_encountered': 0
        }
        
    def record_frame_time(self, processing_time: float):
        """Record frame processing time"""
        self.metrics['frame_processing_times'].append(processing_time)
        self.metrics['frames_processed'] += 1
        
        # Keep only last 1000 measurements
        if len(self.metrics['frame_processing_times']) > 1000:
            self.metrics['frame_processing_times'] = self.metrics['frame_processing_times'][-1000:]
            
    def record_error(self):
        """Record an error occurrence"""
        self.metrics['errors_encountered'] += 1
        
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        frame_times = self.metrics['frame_processing_times']
        total_time = time.time() - self.metrics['start_time']
        
        if frame_times:
            avg_frame_time = sum(frame_times) / len(frame_times)
            max_frame_time = max(frame_times)
            fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        else:
            avg_frame_time = 0
            max_frame_time = 0
            fps = 0
            
        return {
            'total_runtime': total_time,
            'frames_processed': self.metrics['frames_processed'],
            'average_frame_time': avg_frame_time,
            'max_frame_time': max_frame_time,
            'effective_fps': fps,
            'errors_encountered': self.metrics['errors_encountered'],
            'error_rate': self.metrics['errors_encountered'] / max(1, self.metrics['frames_processed'])
        }
        
    def log_performance_summary(self):
        """Log current performance statistics"""
        summary = self.get_performance_summary()
        self.logger.info(
            f"Performance Summary: "
            f"{summary['frames_processed']} frames in {summary['total_runtime']:.1f}s, "
            f"avg: {summary['average_frame_time']*1000:.1f}ms/frame, "
            f"fps: {summary['effective_fps']:.1f}, "
            f"errors: {summary['errors_encountered']}"
        )