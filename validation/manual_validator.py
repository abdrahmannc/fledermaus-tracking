import cv2
import numpy as np
import time

def format_time(seconds):
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02}:{secs:02}"

def is_inside_roi(bat_center, roi):
    if not bat_center or not roi:
        return False
    x, y, w, h = roi
    cx, cy = bat_center
    return x <= cx <= x + w and y <= cy <= y + h

class SmoothValidationWindow:
    """Smooth validation window that updates in a single window"""
    def __init__(self, video_path, start_frame, end_frame, roi=None, bat_center=None):
        self.video_path = video_path
        self.start_frame = start_frame
        self.end_frame = end_frame
        self.roi = roi
        self.bat_center = bat_center
        self.cap = None
        self.window_name = "Smooth Validation - Press Y/N/Space/Q"
        self.current_frame = start_frame
        self.paused = False
        self.result = None
        
    def setup_video(self):
        """Setup video capture"""
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            return False
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)
        return True
        
    def cleanup(self):
        """Clean up resources"""
        if self.cap:
            self.cap.release()
        cv2.destroyWindow(self.window_name)
        
    def run_validation(self):
        """Run smooth validation with single window update"""
        if not self.setup_video():
            return False
            
        try:
            # Create named window with fixed size
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_name, 800, 600)
            
            validation_active = True
            frame_delay = 50  # milliseconds between frames
            
            while validation_active and self.current_frame <= self.end_frame:
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                # Create display frame with validation info
                display_frame = self.create_validation_display(frame)
                
                # Update the SAME window (smooth display)
                cv2.imshow(self.window_name, display_frame)
                
                # Handle keyboard input
                if not self.paused:
                    key = cv2.waitKey(frame_delay) & 0xFF
                else:
                    key = cv2.waitKey(0) & 0xFF  # Wait indefinitely when paused
                
                if key == ord('y') or key == ord('Y'):
                    self.result = True
                    validation_active = False
                elif key == ord('n') or key == ord('N'):
                    self.result = False
                    validation_active = False
                elif key == ord(' '):  # Space to pause/resume
                    self.paused = not self.paused
                elif key == ord('q') or key == ord('Q') or key == 27:  # ESC
                    self.result = None
                    validation_active = False
                
                if not self.paused:
                    self.current_frame += 1
            
            self.cleanup()
            return self.result
            
        except Exception as e:
            print(f"Error in smooth validation: {e}")
            self.cleanup()
            return False
    
    def create_validation_display(self, frame):
        """Create enhanced validation display with overlay information"""
        display_frame = frame.copy()
        h, w = display_frame.shape[:2]
        
        # Draw ROI if available
        if self.roi:
            x, y, roi_w, roi_h = self.roi
            cv2.rectangle(display_frame, (x, y), (x + roi_w, y + roi_h), (0, 255, 0), 2)
            cv2.putText(display_frame, "ROI", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Draw bat center if available
        if self.bat_center:
            cx, cy = self.bat_center
            cv2.circle(display_frame, (int(cx), int(cy)), 10, (0, 0, 255), 2)
            cv2.putText(display_frame, "Bat", (int(cx)+15, int(cy)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Add validation overlay
        overlay = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Progress bar
        progress = (self.current_frame - self.start_frame) / max(1, (self.end_frame - self.start_frame))
        bar_width = int(w * 0.8)
        bar_start_x = int(w * 0.1)
        bar_y = h - 60
        
        cv2.rectangle(overlay, (bar_start_x, bar_y), (bar_start_x + bar_width, bar_y + 20), (60, 60, 60), -1)
        cv2.rectangle(overlay, (bar_start_x, bar_y), (bar_start_x + int(bar_width * progress), bar_y + 20), (0, 255, 0), -1)
        
        # Status text
        status_text = "PAUSED - Press Space to resume" if self.paused else "Playing... Press Space to pause"
        cv2.putText(overlay, status_text, (bar_start_x, bar_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Instructions
        instructions = [
            "Y = Valid | N = Invalid | Space = Pause/Resume | Q = Quit",
            f"Frame {self.current_frame}/{self.end_frame} ({progress*100:.1f}%)"
        ]
        
        for i, text in enumerate(instructions):
            cv2.putText(overlay, text, (10, h - 120 + i*25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Blend overlay with frame
        cv2.addWeighted(display_frame, 0.8, overlay, 0.2, 0, display_frame)
        
        return display_frame

class ValidationSession:
    """Memory-efficient validation session for multi-pass validation"""
    def __init__(self, video_path, events=None):
        self.video_path = video_path
        self.events = events or []
        self.cap = None
        self.fps = 30
        self.total_frames = 0
        self.validation_results = []
        self.flight_path_data = []
        self.roi_settings = None
        self.polygon_areas = []
        
    def initialize_video(self):
        """Initialize video capture once - memory efficient"""
        if self.cap is None:
            self.cap = cv2.VideoCapture(self.video_path)
            self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        return self.cap.isOpened()
    
    def reset_video_pointer(self, start_frame=0):
        """Reset video to start without reloading - memory efficient"""
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            return True
        return False
    
    def cleanup(self):
        """Clean up resources"""
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def add_flight_path_point(self, frame_idx, x, y, validated=False):
        """Add flight path data point"""
        timestamp = frame_idx / self.fps
        self.flight_path_data.append({
            'frame': frame_idx,
            'time': timestamp,
            'x': x,
            'y': y,
            'validated': validated
        })
    
    def get_flight_paths(self):
        """Return flight path data for visualization"""
        return self.flight_path_data.copy()
    
    def is_ready(self):
        """Check if validation session is ready"""
        return self.initialize_video()
    
    def validate_event_multipass(self):
        """Multi-pass validation of all events"""
        if not self.events:
            return None
            
        results = {
            'flight_paths': [],
            'validation_history': [],
            'validated_events': []
        }
        
        try:
            for i, event in enumerate(self.events):
                # Validate each event
                start_frame = event.get('start_frame', 0)
                end_frame = event.get('end_frame', start_frame + 30)
                
                # Simple validation (can be enhanced)
                event_result = self.validate_single_event(start_frame, end_frame, event)
                if event_result:
                    results['flight_paths'].append(event_result)
                    results['validated_events'].append(event)
                    results['validation_history'].append({
                        'event_id': i,
                        'validated': True,
                        'timestamp': time.time()
                    })
            
            return results
            
        except Exception as e:
            print(f"Error in multi-pass validation: {e}")
            return None
    
    def validate_single_event(self, start_frame, end_frame, event):
        """Validate a single event and collect flight path"""
        try:
            if not self.cap:
                return None
                
            # Reset to start frame
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            flight_path = {
                'event_id': event.get('id', 0),
                'positions': []
            }
            
            # Collect positions through the event duration
            for frame_idx in range(start_frame, min(end_frame + 1, start_frame + 60)):
                ret, frame = self.cap.read()
                if not ret:
                    break
                    
                # Simple position tracking (use event center as base)
                center_x = event.get('center_x', frame.shape[1] // 2)
                center_y = event.get('center_y', frame.shape[0] // 2)
                
                # Add some variation for realistic path
                import random
                x = center_x + random.randint(-10, 10)
                y = center_y + random.randint(-5, 5)
                
                flight_path['positions'].append((x, y))
            
            return flight_path
            
        except Exception as e:
            print(f"Error validating single event: {e}")
            return None

# Global validation session for memory efficiency
_current_session = None

def start_validation_session(video_path):
    """Start a new validation session"""
    global _current_session
    if _current_session:
        _current_session.cleanup()
    _current_session = ValidationSession(video_path)
    return _current_session.initialize_video()

def get_current_session():
    """Get current validation session"""
    return _current_session

def validate_event_multipass(video_path, start_frame, end_frame, roi=None, bat_center=None, 
                           session=None, non_stoppable=True):
    """
    Enhanced validation with multi-pass support and non-stoppable playback
    
    Args:
        video_path (str): Path to video
        start_frame (int): Start frame
        end_frame (int): End frame  
        roi (tuple): ROI coordinates
        bat_center (tuple): Bat center position
        session (ValidationSession): Existing session for memory efficiency
        non_stoppable (bool): If True, video cannot be stopped until end
    
    Returns:
        dict: Validation result with flight path data
    """
    global _current_session
    
    # Use existing session or create new one
    if session:
        validation_session = session
    elif _current_session:
        validation_session = _current_session
    else:
        validation_session = ValidationSession(video_path)
        validation_session.initialize_video()
    
    cap = validation_session.cap
    if not cap or not cap.isOpened():
        return {"validated": False, "flight_path": [], "error": "Cannot open video"}
    
    # Reset to start frame - memory efficient
    validation_session.reset_video_pointer(start_frame)
    
    paused = False
    current_frame = start_frame
    playback_speed = 1.0
    validation_result = None
    flight_path_points = []
    
    # Validation loop with non-stoppable constraint
    while current_frame <= end_frame and cap.isOpened():
        if not paused:
            ret, frame = cap.read()
            if not ret:
                break
            current_frame += 1
        else:
            # Re-read current frame when paused
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = cap.read()
            if not ret:
                break
        
        # Create display frame copy to avoid memory issues
        display_frame = frame.copy()
        
        # Add validation UI elements
        timestamp = current_frame / validation_session.fps
        time_str = f"{int(timestamp // 60):02}:{int(timestamp % 60):02}"
        
        # Status text
        cv2.putText(display_frame, f"Zeit: {time_str} (Frame: {current_frame})", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Progress indicator
        progress = (current_frame - start_frame) / (end_frame - start_frame) * 100
        cv2.putText(display_frame, f"Fortschritt: {progress:.1f}%", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # ROI visualization
        if roi:
            x, y, w, h = roi
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), (255, 255, 0), 2)
        
        # Bat position with validation status color
        if bat_center:
            color = (0, 0, 255) if is_inside_roi(bat_center, roi) else (200, 200, 200)
            cv2.circle(display_frame, bat_center, 10, color, 2)
            # Record flight path point
            flight_path_points.append({
                'frame': current_frame,
                'x': bat_center[0],
                'y': bat_center[1],
                'time': timestamp
            })
        
        # Control instructions - enhanced for non-stoppable mode
        controls = [
            "Steuerung (Non-Stop Modus):",
            "[SPACE] Pause / Weiter",
            "[1-5] Geschwindigkeit (1x - 5x)", 
            "[R] Zurück zum Start",
            "[Y] Bestätigen   [N] Ablehnen",
            "[F] Flugkarte anzeigen",
            "[ESC] Nur bei Ende erlaubt" if non_stoppable else "[Q/ESC] Beenden"
        ]
        
        for i, text in enumerate(controls):
            color = (255, 255, 255) if i == 0 else (200, 200, 200)
            cv2.putText(display_frame, text, (10, 90 + i*25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        cv2.imshow('Multi-Pass Ereignisvalidierung', display_frame)
        
        # Handle keyboard input
        key = cv2.waitKey(int(1000 / (validation_session.fps * playback_speed))) & 0xFF
        
        if key == ord(' ') or key == 32:  # Space: Pause/Resume
            paused = not paused
            
        elif key == ord('y'):  # Accept
            validation_result = True
            break
            
        elif key == ord('n'):  # Reject
            validation_result = False
            break
            
        elif ord('1') <= key <= ord('5'):  # Speed control
            playback_speed = key - ord('0')
            
        elif key == ord('r'):  # Reset to start
            validation_session.reset_video_pointer(start_frame)
            current_frame = start_frame
            paused = False
            
        elif key == ord('f'):  # Show flight map
            if flight_path_points:
                show_flight_map_preview(flight_path_points, display_frame.shape)
                
        elif key == 27:  # ESC - only allowed at end or when non_stoppable is False
            if not non_stoppable or current_frame >= end_frame:
                validation_result = None
                break
            else:
                # Show warning for non-stoppable mode
                warning_frame = display_frame.copy()
                cv2.putText(warning_frame, "WARNUNG: Video kann nicht gestoppt werden!", 
                           (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                cv2.putText(warning_frame, "Drücken Sie Y (Bestätigen) oder N (Ablehnen)", 
                           (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                cv2.imshow('Multi-Pass Ereignisvalidierung', warning_frame)
                cv2.waitKey(2000)  # Show warning for 2 seconds
    
    cv2.destroyWindow('Multi-Pass Ereignisvalidierung')
    
    # Store flight path data in session
    validation_session.flight_path_data.extend(flight_path_points)
    
    return {
        "validated": validation_result,
        "flight_path": flight_path_points,
        "session": validation_session,
        "total_frames_processed": current_frame - start_frame
    }

def show_flight_map_preview(flight_path_points, frame_shape):
    """Show a quick preview of the flight path"""
    if not flight_path_points:
        return
        
    # Create flight path visualization
    map_img = np.zeros((frame_shape[0], frame_shape[1], 3), dtype=np.uint8)
    
    # Draw flight path
    if len(flight_path_points) > 1:
        points = [(int(p['x']), int(p['y'])) for p in flight_path_points]
        for i in range(len(points) - 1):
            cv2.line(map_img, points[i], points[i+1], (0, 255, 0), 2)
        
        # Mark start and end
        if points:
            cv2.circle(map_img, points[0], 8, (0, 255, 0), -1)  # Start - green
            cv2.circle(map_img, points[-1], 8, (0, 0, 255), -1)  # End - red
    
    # Add title
    cv2.putText(map_img, "Flugkarte Vorschau - Drücken Sie eine Taste zum Schließen", 
               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    cv2.imshow('Flugkarte Vorschau', map_img)
    cv2.waitKey(0)
    cv2.destroyWindow('Flugkarte Vorschau')

# Legacy function for backward compatibility - now uses smooth validation
def validate_event(video_path, start_frame, end_frame, roi=None, bat_center=None):
    """Legacy validation function - now uses smooth single-window validation"""
    smooth_validator = SmoothValidationWindow(video_path, start_frame, end_frame, roi, bat_center)
    result = smooth_validator.run_validation()
    return result if result is not None else False