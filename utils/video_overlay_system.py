#!/usr/bin/env python3
"""
Video Overlay System (German)
=============================

Provides real-time German overlay functionality for the bat detection system:
- Frame progress and FastEngine status
- Bat detection events with timestamps
- Polygon visualization with active/inactive states
- Performance-optimized for 30+ FPS processing

Replaces console [STATUS] logging with clean video window overlays.
"""

import cv2
import numpy as np
import time
from typing import List, Tuple, Optional, Dict, Any


class GermanVideoOverlay:
    """
    German video overlay system for real-time bat detection feedback.
    
    Features:
    - Frame progress: "Analyse des Frames 540/1065 (50.7%) - FastEngine"
    - Bat events: "🦇 Fledermaus erkannt in Polygon #1 bei 364.49s"
    - Polygon visualization with green (active) and gray (inactive) boxes
    - Clean, performance-optimized overlay rendering
    """
    
    def __init__(self):
        # Font configuration for optimal readability
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.6
        self.font_thickness = 2
        self.shadow_thickness = 4
        
        # Color scheme (BGR format)
        self.colors = {
            'text': (255, 255, 255),           # White text
            'text_shadow': (0, 0, 0),          # Black shadow
            'progress_bg': (0, 0, 0),          # Black background
            'detection_text': (0, 255, 0),     # Green for detections
            'polygon_active': (0, 255, 0),     # Green for active polygons
            'polygon_inactive': (128, 128, 128), # Gray for inactive polygons
            'bat_highlight': (0, 255, 255),    # Yellow for bat center
            'event_bg': (0, 50, 0),            # Dark green background
        }
        
        # Layout configuration
        self.margin = 15
        self.line_height = 25
        self.overlay_alpha = 0.8
        
        # Event display management
        self.recent_events: List[Dict[str, Any]] = []
        self.max_events_display = 3
        self.event_display_duration = 5.0  # seconds
        
        # Performance tracking
        self.overlay_render_times = []
        
    def create_progress_overlay(self, frame: np.ndarray, frame_idx: int, total_frames: int, 
                              fast_engine_active: bool, fps: float = 30.0) -> np.ndarray:
        """
        Create frame progress overlay in German.
        
        Args:
            frame: Current video frame
            frame_idx: Current frame number (1-based)
            total_frames: Total number of frames
            fast_engine_active: Whether FastPolygonEngine is active
            fps: Video frame rate for time calculation
            
        Returns:
            Frame with progress overlay
        """
        overlay_start = time.time()
        
        # Calculate progress
        progress_percent = (frame_idx / total_frames) * 100 if total_frames > 0 else 0
        current_time = frame_idx / fps if fps > 0 else 0
        engine_status = "FastEngine" if fast_engine_active else "Standard"
        
        # Create main progress text
        progress_text = f"Analyse des Frames {frame_idx}/{total_frames} ({progress_percent:.1f}%) - {engine_status}"
        time_text = f"Zeit: {self._format_time(current_time)}"
        
        # Create overlay frame
        overlay_frame = frame.copy()
        
        # Draw background rectangle for progress info
        bg_height = 60
        cv2.rectangle(overlay_frame, (0, 0), (overlay_frame.shape[1], bg_height), 
                     self.colors['progress_bg'], -1)
        
        # Apply transparency
        cv2.addWeighted(overlay_frame, self.overlay_alpha, frame, 1 - self.overlay_alpha, 0, overlay_frame)
        
        # Draw progress text with shadow
        self._draw_text_with_shadow(overlay_frame, progress_text, 
                                   (self.margin, self.margin + 20), 
                                   self.colors['text'], self.colors['text_shadow'])
        
        # Draw time text
        self._draw_text_with_shadow(overlay_frame, time_text, 
                                   (self.margin, self.margin + 45), 
                                   self.colors['text'], self.colors['text_shadow'])
        
        # Track performance
        render_time = time.time() - overlay_start
        self.overlay_render_times.append(render_time)
        if len(self.overlay_render_times) > 100:
            self.overlay_render_times.pop(0)
            
        return overlay_frame
    
    def add_detection_event(self, event_type: str, polygon_idx: int, timestamp: float, 
                          event_data: Optional[Dict[str, Any]] = None):
        """
        Add a bat detection event for overlay display.
        
        Args:
            event_type: 'entry' or 'exit'
            polygon_idx: Index of the polygon where event occurred
            timestamp: Event timestamp in seconds
            event_data: Additional event information
        """
        if event_type == 'entry':
            text = f"🦇 Fledermaus erkannt in Polygon #{polygon_idx + 1} bei {timestamp:.2f}s"
        elif event_type == 'exit':
            text = f"🦇 Fledermaus verlassen bei {timestamp:.2f}s"
        else:
            text = f"🦇 Ereignis in Polygon #{polygon_idx + 1} bei {timestamp:.2f}s"
        
        event = {
            'text': text,
            'timestamp': time.time(),
            'event_time': timestamp,
            'polygon_idx': polygon_idx,
            'type': event_type,
            'data': event_data or {}
        }
        
        self.recent_events.append(event)
        
        # Keep only recent events
        current_time = time.time()
        self.recent_events = [e for e in self.recent_events 
                            if current_time - e['timestamp'] < self.event_display_duration]
        
        # Limit number of displayed events
        if len(self.recent_events) > self.max_events_display:
            self.recent_events = self.recent_events[-self.max_events_display:]
    
    def create_detection_overlay(self, frame: np.ndarray) -> np.ndarray:
        """
        Add detection events overlay to the frame.
        
        Args:
            frame: Current video frame
            
        Returns:
            Frame with detection events overlay
        """
        if not self.recent_events:
            return frame
        
        overlay_frame = frame.copy()
        
        # Calculate overlay position (bottom-left corner)
        start_y = frame.shape[0] - (len(self.recent_events) * self.line_height) - self.margin
        bg_width = min(600, frame.shape[1] - 2 * self.margin)
        bg_height = len(self.recent_events) * self.line_height + self.margin
        
        # Draw semi-transparent background
        bg_start_x = self.margin
        bg_start_y = start_y - self.margin
        
        # Create background overlay
        bg_overlay = overlay_frame.copy()
        cv2.rectangle(bg_overlay, (bg_start_x, bg_start_y), 
                     (bg_start_x + bg_width, bg_start_y + bg_height), 
                     self.colors['event_bg'], -1)
        
        # Apply transparency
        cv2.addWeighted(bg_overlay, 0.7, overlay_frame, 0.3, 0, overlay_frame)
        
        # Draw event texts
        for i, event in enumerate(self.recent_events):
            y_pos = start_y + (i * self.line_height)
            self._draw_text_with_shadow(overlay_frame, event['text'], 
                                       (self.margin + 10, y_pos), 
                                       self.colors['detection_text'], 
                                       self.colors['text_shadow'])
        
        return overlay_frame
    
    def create_polygon_overlay(self, frame: np.ndarray, polygon_areas: List[List[Tuple[int, int]]], 
                             active_polygons: Optional[List[int]] = None, 
                             bat_centers: Optional[List[Tuple[int, int]]] = None) -> np.ndarray:
        """
        Add polygon visualization overlay with active/inactive states.
        
        Args:
            frame: Current video frame
            polygon_areas: List of polygon coordinates
            active_polygons: List of polygon indices with recent detections
            bat_centers: List of detected bat center coordinates
            
        Returns:
            Frame with polygon overlay
        """
        if not polygon_areas:
            return frame
        
        overlay_frame = frame.copy()
        active_set = set(active_polygons or [])
        
        # Draw polygons
        for i, polygon in enumerate(polygon_areas):
            if len(polygon) < 3:
                continue
                
            # Choose color based on active state
            color = self.colors['polygon_active'] if i in active_set else self.colors['polygon_inactive']
            
            # Convert to numpy array
            poly_array = np.array(polygon, dtype=np.int32)
            
            # Draw polygon outline
            cv2.polylines(overlay_frame, [poly_array], True, color, 2)
            
            # Draw polygon number
            if len(polygon) > 0:
                center_x = int(sum(p[0] for p in polygon) / len(polygon))
                center_y = int(sum(p[1] for p in polygon) / len(polygon))
                
                label = f"#{i + 1}"
                self._draw_text_with_shadow(overlay_frame, label, 
                                           (center_x - 10, center_y), 
                                           color, self.colors['text_shadow'])
        
        # Draw bat centers if provided
        if bat_centers:
            for center in bat_centers:
                cv2.circle(overlay_frame, center, 8, self.colors['bat_highlight'], -1)
                cv2.circle(overlay_frame, center, 12, self.colors['bat_highlight'], 2)
        
        return overlay_frame
    
    def create_complete_overlay(self, frame: np.ndarray, frame_idx: int, total_frames: int,
                               fast_engine_active: bool, polygon_areas: List[List[Tuple[int, int]]],
                               active_polygons: Optional[List[int]] = None,
                               bat_centers: Optional[List[Tuple[int, int]]] = None,
                               fps: float = 30.0) -> np.ndarray:
        """
        Create complete overlay with all components.
        
        Args:
            frame: Current video frame
            frame_idx: Current frame number
            total_frames: Total number of frames
            fast_engine_active: Whether FastPolygonEngine is active
            polygon_areas: List of polygon coordinates
            active_polygons: List of active polygon indices
            bat_centers: List of detected bat centers
            fps: Video frame rate
            
        Returns:
            Frame with complete overlay system
        """
        # Start with progress overlay
        overlay_frame = self.create_progress_overlay(frame, frame_idx, total_frames, 
                                                   fast_engine_active, fps)
        
        # Add polygon visualization
        overlay_frame = self.create_polygon_overlay(overlay_frame, polygon_areas, 
                                                  active_polygons, bat_centers)
        
        # Add detection events
        overlay_frame = self.create_detection_overlay(overlay_frame)
        
        return overlay_frame
    
    def _draw_text_with_shadow(self, frame: np.ndarray, text: str, position: Tuple[int, int], 
                              text_color: Tuple[int, int, int], shadow_color: Tuple[int, int, int]):
        """Draw text with shadow for better readability."""
        x, y = position
        
        # Draw shadow (offset by 1 pixel)
        cv2.putText(frame, text, (x + 1, y + 1), self.font, self.font_scale, 
                   shadow_color, self.shadow_thickness)
        
        # Draw main text
        cv2.putText(frame, text, (x, y), self.font, self.font_scale, 
                   text_color, self.font_thickness)
    
    def _format_time(self, seconds: float) -> str:
        """Format time in MM:SS.ss format."""
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes:02d}:{remaining_seconds:05.2f}"
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get overlay rendering performance statistics."""
        if not self.overlay_render_times:
            return {'avg_render_time': 0.0, 'max_render_time': 0.0}
        
        avg_time = sum(self.overlay_render_times) / len(self.overlay_render_times)
        max_time = max(self.overlay_render_times)
        
        return {
            'avg_render_time': avg_time * 1000,  # Convert to milliseconds
            'max_render_time': max_time * 1000,
            'samples': len(self.overlay_render_times)
        }
    
    def clear_events(self):
        """Clear all displayed events."""
        self.recent_events.clear()


class VideoDisplayManager:
    """
    Manages video display window for real-time overlay visualization.
    """
    
    def __init__(self, window_name: str = "Fledermaus-Erkennung"):
        self.window_name = window_name
        self.overlay_system = GermanVideoOverlay()
        self.window_created = False
        
    def create_window(self):
        """Create the video display window."""
        if not self.window_created:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_name, 1280, 720)
            self.window_created = True
    
    def display_frame(self, frame: np.ndarray, frame_idx: int, total_frames: int,
                     fast_engine_active: bool, polygon_areas: List[List[Tuple[int, int]]],
                     active_polygons: Optional[List[int]] = None,
                     bat_centers: Optional[List[Tuple[int, int]]] = None,
                     fps: float = 30.0, show_window: bool = True):
        """
        Display frame with complete overlay system.
        
        Args:
            frame: Current video frame
            frame_idx: Current frame number
            total_frames: Total number of frames
            fast_engine_active: Whether FastPolygonEngine is active
            polygon_areas: List of polygon coordinates
            active_polygons: List of active polygon indices
            bat_centers: List of detected bat centers
            fps: Video frame rate
            show_window: Whether to actually show the window
            
        Returns:
            bool: True if window should continue displaying, False if user requested close
                 (via X button, 'q' key, ESC key, or window error occurred)
        """
        if not show_window:
            return True  # Window not shown, continue processing
            
        self.create_window()
        
        # Create complete overlay
        display_frame = self.overlay_system.create_complete_overlay(
            frame, frame_idx, total_frames, fast_engine_active, 
            polygon_areas, active_polygons, bat_centers, fps
        )
        
        # Display the frame with comprehensive error handling
        try:
            cv2.imshow(self.window_name, display_frame)
            # Process any pending window events
            key = cv2.waitKey(1) & 0xFF
            
            # Check if window was closed by X button
            try:
                window_property = cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE)
                if window_property < 1:  # Window was closed
                    try:
                        cv2.destroyAllWindows()
                    except:
                        pass
                    return False
            except:
                # getWindowProperty failed, assume window was closed
                try:
                    cv2.destroyAllWindows()
                except:
                    pass
                return False
            
            # Return False if 'q' or ESC is pressed for graceful shutdown
            if key == ord('q') or key == 27:  # ESC key
                try:
                    cv2.destroyAllWindows()
                except:
                    pass
                return False
                
            return True  # Window is still active
            
        except cv2.error:
            # Window was closed or other OpenCV error occurred
            try:
                cv2.destroyAllWindows()
            except:
                pass
            return False  # Window closed or error occurred
        except Exception:
            # Any other exception - treat as window closed
            try:
                cv2.destroyAllWindows()
            except:
                pass
            return False
    
    def add_detection_event(self, event_type: str, polygon_idx: int, timestamp: float,
                          event_data: Optional[Dict[str, Any]] = None):
        """Add detection event to overlay system."""
        self.overlay_system.add_detection_event(event_type, polygon_idx, timestamp, event_data)
    
    def close_window(self):
        """Close the video display window."""
        if self.window_created:
            try:
                cv2.destroyWindow(self.window_name)
                cv2.waitKey(1)
            except cv2.error:
                pass
            self.window_created = False
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get overlay performance statistics."""
        return self.overlay_system.get_performance_stats()