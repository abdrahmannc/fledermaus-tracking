"""
Background Video Processing Module
Provides background processing capabilities for video detection and export operations
"""

import threading
import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np

class ProgressInfo:
    """Container for progress information"""
    def __init__(self, percentage, message):
        self.percentage = percentage
        self.message = message
    
    def get_percentage(self):
        """Get the progress percentage"""
        return self.percentage
    
    def get_status_text(self):
        """Get the status message"""
        return self.message

class ProgressDialog:
    """Simple progress dialog for background operations"""
    def __init__(self, parent, title="Processing...", cancelable=True):
        self.parent = parent  # Store parent reference for cancel functionality
        self.background_processor = None  # Will be set by the calling code
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x120")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Create widgets
        self.message_label = tk.Label(self.dialog, text="Starting...")
        self.message_label.pack(pady=10)
        
        self.progress_bar = ttk.Progressbar(self.dialog, length=350, mode='determinate')
        self.progress_bar.pack(pady=5)
        
        # Only show cancel button if cancelable is True
        if cancelable:
            self.cancel_button = tk.Button(self.dialog, text="Cancel", command=self.cancel)
            self.cancel_button.pack(pady=10)
        
        self.cancelled = False
        
        # Handle window close event
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
    def update_progress(self, progress_or_percentage, status_text=None):
        """Update progress display - supports both single ProgressInfo object and separate parameters"""
        # Check if dialog is still valid before updating
        if self.cancelled:
            return
            
        try:
            if status_text is not None:
                # Called with separate parameters (percentage, status_text)
                self.progress_bar['value'] = progress_or_percentage
                self.message_label.config(text=status_text)
            else:
                # Called with ProgressInfo object
                progress_info = progress_or_percentage
                if hasattr(progress_info, 'percentage'):
                    self.progress_bar['value'] = progress_info.percentage
                if hasattr(progress_info, 'message'):
                    self.message_label.config(text=progress_info.message)
        except:
            # Ignore errors if dialog has been closed
            pass
        
    def cancel(self):
        """Cancel the operation and close any open windows"""
        self.cancelled = True
        
        # Directly cancel the background processor if available
        if hasattr(self, 'background_processor') and self.background_processor:
            self.background_processor.cancel_processing()
        
        # If there's a parent GUI with a detector, stop it properly
        if hasattr(self.parent, 'detector'):
            self.parent.detector.stop_detection()
        
        # Also check for background_processor in parent
        if hasattr(self.parent, 'background_processor'):
            self.parent.background_processor.cancel_processing()
        
        # Force close any OpenCV windows
        try:
            import cv2
            cv2.destroyAllWindows()
        except:
            pass
        
        # Close the dialog
        self.close()
        
    def is_cancelled(self):
        """Check if the operation was cancelled"""
        return self.cancelled
        
    def close(self):
        """Close the dialog"""
        self.dialog.destroy()

class BackgroundVideoProcessor:
    """Handles background video processing operations"""
    
    def __init__(self, gui):
        self.gui = gui
        self.processing = False
        self.cancelled = False
        self.current_thread = None
        
    def cancel_processing(self):
        """Cancel any ongoing processing and close all windows"""
        # Cancel processing - removed debug statements for cleaner output
        self.cancelled = True
        
        # Stop the detector if available
        if hasattr(self.gui, 'detector'):
            self.gui.detector.stop_detection()
        
        # Force close any OpenCV windows
        try:
            import cv2
            cv2.destroyAllWindows()
        except:
            pass
        
        if self.processing and self.current_thread:
            # Give thread time to notice cancellation
            self.current_thread.join(timeout=3.0)
            if self.current_thread.is_alive():
                # Processing thread didn't finish, forcing cleanup
                pass
        
        self.processing = False
        
    def start_detection_background(self, detector, progress_callback=None):
        """Start video detection in background with progress updates"""
        if self.processing:
            return False
        
        self.processing = True
        self.cancelled = False
        
        def detection_worker():
            try:
                # Ensure detector is properly initialized
                if not detector.video_path:
                    self.gui.root.after(0, lambda: self.gui.update_status("Video not loaded"))
                    return
 
                # Initialize video capture
                detector.cap = cv2.VideoCapture(detector.video_path)
                if not detector.cap.isOpened():
                    self.gui.root.after(0, lambda: self.gui.update_status("Error: Could not open video"))
                    return
                
                # Get video properties
                detector.total_frames = int(detector.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                detector.fps = detector.cap.get(cv2.CAP_PROP_FPS)
                
                # Initialize detection state
                detector.processing = True
                detector.motion_history = []
                detector.events = []
                detector.marked_frames = []
                detector.event_frames = {}
                detector.bat_centers = []
                detector.cooldown_counter = 0
                detector.bat_inside = False
                
                # Set up ROI if none exists
                if detector.roi is None:
                    ret, frame = detector.cap.read()
                    if ret:
                        h, w = frame.shape[:2]
                        detector.roi = (0, 0, w, h)
                        detector.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    else:
                        self.gui.root.after(0, lambda: self.gui.update_status("Failed to read video"))
                        return
                
                # Use the original detector's logic with progress tracking
                self._run_original_detection_with_progress(detector, progress_callback)
                
                # Final update - ensure completion is properly signaled
                if progress_callback and not self.cancelled:
                    final_progress = ProgressInfo(100, "Detection completed")
                    self.gui.root.after(0, lambda: progress_callback(final_progress))
                    
                    # Additional completion signal after a short delay to ensure GUI update
                    def delayed_completion():
                        if progress_callback:
                            completion_progress = ProgressInfo(100, "Analysis finished")
                            progress_callback(completion_progress)
                    
                    self.gui.root.after(100, delayed_completion)  # 100ms delay
                
                # Update GUI in main thread
                self.gui.root.after(0, self._on_detection_complete)
                
            except Exception as e:
                error_msg = f"Detection error: {str(e)}"
                self.gui.root.after(0, lambda: self.gui.update_status(error_msg))
            finally:
                self.processing = False
                if hasattr(detector, 'cap') and detector.cap:
                    detector.cap.release()
        
        # Start worker thread
        self.current_thread = threading.Thread(target=detection_worker)
        self.current_thread.daemon = True
        self.current_thread.start()
        
        return True
    
    def _run_original_detection_with_progress(self, detector, progress_callback):
        """Run the original video detector logic with progress tracking"""
        try:
            # Store the original update_status method
            original_update_status = detector.gui.update_status
            
            def thread_safe_update_status(message):
                # Thread-safe status updates
                self.gui.root.after(0, lambda msg=message: original_update_status(msg))
                
                # Update progress during processing
                if progress_callback and "at" in message and "s" in message:
                    try:
                        # Extract time from status messages like "Bat entered at 5.23s"
                        import re
                        time_match = re.search(r'(\d+\.\d+)s', message)
                        if time_match:
                            current_time = float(time_match.group(1))
                            total_duration = detector.total_frames / detector.fps if detector.fps > 0 else 1
                            percentage = min(100, (current_time / total_duration) * 100)
                            progress_info = ProgressInfo(percentage, f"Processing... {message}")
                            self.gui.root.after(0, lambda p=progress_info: progress_callback(p))
                    except:
                        pass
            
            # Temporarily replace the update_status method
            detector.gui.update_status = thread_safe_update_status
            
            # Also temporarily remove the problematic GUI callback at the end
            original_gui_callback = None
            if hasattr(detector.gui, 'on_detection_finished'):
                original_gui_callback = detector.gui.on_detection_finished
                detector.gui.on_detection_finished = lambda: None  # Disable callback temporarily
            
            try:
                # CRITICAL FIX: Use proper detection method selection based on configured areas
                # Priority: ROI first, then polygons, then whole video (same as detection_and_analysis.py)
                # CRITICAL: Use user_roi to distinguish actual user-drawn ROI from calculated polygon bounding ROI
                has_roi = hasattr(detector, 'user_roi') and detector.user_roi is not None
                has_polygons = (hasattr(detector, 'polygon_areas') and detector.polygon_areas and 
                               len(detector.polygon_areas) > 0)
                
                # Pass background processor reference for cancellation checking
                detector.background_processor = self
                
                # Detection method selection (debug logging removed)
                
                if has_roi and not has_polygons:
                    # ROI only - use standard processing
                    detector._process_video()
                elif has_polygons and not has_roi:
                    # Polygons only - use polygon-masked processing
                    detector._process_video_with_polygon_mask()
                elif has_roi and has_polygons:
                    # Both exist - ROI has priority (same as detection_and_analysis.py)
                    detector._process_video()
                else:
                    # Neither - whole video processing
                    # Using _process_video() [Whole video mode] - removed debug statement
                    detector._process_video()
            finally:
                # Restore original methods
                detector.gui.update_status = original_update_status
                if original_gui_callback:
                    detector.gui.on_detection_finished = original_gui_callback
                
        except Exception as e:
            error_msg = f"Detection error: {str(e)}"
            self.gui.root.after(0, lambda: self.gui.update_status(error_msg))
        finally:
            # Finalize any incomplete events
            if hasattr(detector, 'events') and detector.events:
                # Get the last processed frame index from the detector
                last_frame = detector.total_frames if detector.total_frames > 0 else 0
                self._finalize_incomplete_events(detector, last_frame)
            detector.processing = False
    
    # OLD METHOD - No longer used, replaced with _run_original_detection_with_progress
    # def _run_detection_with_progress(self, detector, progress_callback):
    #     """Run detection loop with progress updates"""
    #     ... (commented out - now using original detector logic)
    
    def _process_bat_events(self, detector, stabilized_motion, bat_center, frame_idx):
        """Process bat entry and exit events"""
        # Import constants
        try:
            from utils.config import COOLDOWN_FRAMES
        except ImportError:
            COOLDOWN_FRAMES = 30
        
        # Check for bat entry
        if stabilized_motion and not detector.bat_inside and detector.cooldown_counter == 0:
            # Check polygon filtering if polygons exist
            polygon_entry_valid = True
            polygon_area = -1
            
            if detector.polygon_areas and bat_center:
                polygon_entry_valid = False
                for poly_idx, polygon in enumerate(detector.polygon_areas):
                    if len(polygon) >= 3 and self._point_in_polygon(bat_center, polygon):
                        polygon_area = poly_idx
                        polygon_entry_valid = True
                        break
            
            if polygon_entry_valid:
                detector.bat_inside = True
                entry_time = frame_idx / detector.fps
                
                event_data = {
                    "entry": entry_time,
                    "einflugzeit": entry_time,
                    "exit": None,
                    "ausflugzeit": None,
                    "duration": None,
                    "dauer": None,
                    "frame_idx": frame_idx,
                    "entry_frame": frame_idx,
                    "exit_frame": None,
                    "roi": detector.roi,
                    "bat_center": bat_center,
                    "event_id": len(detector.events)
                }
                
                if polygon_area >= 0:
                    event_data["polygon_area"] = polygon_area
                    status_msg = f"Fledermaus im Polygon #{polygon_area + 1} um {entry_time:.2f}s"
                else:
                    status_msg = f"Bat entered at {entry_time:.2f}s"
                
                detector.events.append(event_data)
                detector.cooldown_counter = COOLDOWN_FRAMES
                self.gui.root.after(0, lambda msg=status_msg: self.gui.update_status(msg))
        
        # Check for bat exit
        elif not stabilized_motion and detector.bat_inside and detector.cooldown_counter == 0:
            detector.bat_inside = False
            exit_time = frame_idx / detector.fps
            
            if detector.events:
                last_event = detector.events[-1]
                last_event["exit"] = exit_time
                last_event["ausflugzeit"] = exit_time
                last_event["exit_frame"] = frame_idx
                
                entry_time = last_event.get("entry", 0)
                duration = max(0.0, exit_time - entry_time)
                last_event["duration"] = duration
                last_event["dauer"] = duration
            
            detector.cooldown_counter = COOLDOWN_FRAMES
            self.gui.root.after(0, lambda: self.gui.update_status(f"Fledermaus aus Polygon um {exit_time:.2f}s"))
    
    def _draw_polygons(self, frame, polygon_areas):
        """Draw polygon areas on frame"""
        if not polygon_areas:
            return
            
        for poly_idx, polygon in enumerate(polygon_areas):
            if len(polygon) >= 3:
                pts = np.array(polygon, np.int32)
                cv2.fillPoly(frame, [pts], (0, 255, 0, 64))
                cv2.polylines(frame, [pts], True, (0, 255, 0), 2)
                
                # Add polygon number
                if len(polygon) > 0:
                    center_x = int(sum(p[0] for p in polygon) / len(polygon))
                    center_y = int(sum(p[1] for p in polygon) / len(polygon))
                    cv2.putText(frame, f"#{poly_idx + 1}", (center_x, center_y),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    def _point_in_polygon(self, point, polygon):
        """Check if point is inside polygon using ray casting algorithm"""
        x, y = point
        n = len(polygon)
        inside = False
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside
    
    def _finalize_incomplete_events(self, detector, final_frame_idx):
        """Handle any incomplete events at the end of the video"""
        if detector.events and detector.bat_inside:
            last_event = detector.events[-1]
            if last_event.get("exit") is None:
                exit_time = final_frame_idx / detector.fps
                last_event["exit"] = exit_time
                last_event["ausflugzeit"] = exit_time
                last_event["exit_frame"] = final_frame_idx
                
                entry_time = last_event.get("entry", 0)
                duration = max(0.0, exit_time - entry_time)
                last_event["duration"] = duration
                last_event["dauer"] = duration
    
    def _on_detection_complete(self):
        """Called when detection is complete"""
        # Ensure progress dialog is closed
        if hasattr(self.gui, 'hide_progress_dialog'):
            self.gui.hide_progress_dialog()
        
        # Call the original completion handler
        if hasattr(self.gui, 'on_detection_finished'):
            self.gui.on_detection_finished()
    
    def start_csv_export_background(self, export_func, filename, progress_callback=None):
        """Export CSV in background"""
        if self.processing:
            return False
            
        self.processing = True
        self.cancelled = False
        
        def export_worker():
            try:
                if progress_callback:
                    progress = ProgressInfo(50, "Exporting CSV...")
                    self.gui.root.after(0, lambda: progress_callback(progress))
                
                # Run export
                export_func(filename)
                
                if progress_callback and not self.cancelled:
                    progress = ProgressInfo(100, "CSV export completed")
                    self.gui.root.after(0, lambda: progress_callback(progress))
                
                self.gui.root.after(0, lambda: self.gui.update_status(f"CSV exported: {filename}"))
                
            except Exception as e:
                error_msg = f"CSV export error: {str(e)}"
                self.gui.root.after(0, lambda: self.gui.update_status(error_msg))
            finally:
                self.processing = False
        
        self.current_thread = threading.Thread(target=export_worker)
        self.current_thread.daemon = True
        self.current_thread.start()
        
        return True
    
    def start_pdf_export_background(self, export_func, filename, progress_callback=None):
        """Export PDF in background"""
        if self.processing:
            return False
            
        self.processing = True
        self.cancelled = False
        
        def export_worker():
            try:
                if progress_callback:
                    progress = ProgressInfo(30, "Generating PDF...")
                    self.gui.root.after(0, lambda: progress_callback(progress))
                
                # Run export
                export_func(filename)
                
                if progress_callback and not self.cancelled:
                    progress = ProgressInfo(100, "PDF export completed")
                    self.gui.root.after(0, lambda: progress_callback(progress))
                
                self.gui.root.after(0, lambda: self.gui.update_status(f"PDF exported: {filename}"))
                
            except Exception as e:
                error_msg = f"PDF export error: {str(e)}"
                self.gui.root.after(0, lambda: self.gui.update_status(error_msg))
            finally:
                self.processing = False
        
        self.current_thread = threading.Thread(target=export_worker)
        self.current_thread.daemon = True
        self.current_thread.start()
        
        return True
    
    def start_marked_video_export_background(self, export_func, filename, progress_callback=None):
        """Export marked video in background"""
        if self.processing:
            return False
            
        self.processing = True
        self.cancelled = False
        
        def export_worker():
            try:
                if progress_callback:
                    progress = ProgressInfo(10, "Starting video export...")
                    self.gui.root.after(0, lambda: progress_callback(progress))
                
                # Run export with progress updates
                export_func(filename, progress_callback)
                
                if progress_callback and not self.cancelled:
                    progress = ProgressInfo(100, "Video export completed")
                    self.gui.root.after(0, lambda: progress_callback(progress))
                
                self.gui.root.after(0, lambda: self.gui.update_status(f"Marked video exported: {filename}"))
                
            except Exception as e:
                error_msg = f"Video export error: {str(e)}"
                self.gui.root.after(0, lambda: self.gui.update_status(error_msg))
            finally:
                self.processing = False
        
        self.current_thread = threading.Thread(target=export_worker)
        self.current_thread.daemon = True
        self.current_thread.start()
        
        return True
    
    def start_export_background(self, export_func, marked_frames, fps, video_path, username, progress_callback=None, user_choice=None):
        """Export marked video in background with all parameters from GUI"""
        if self.processing:
            return False
            
        self.processing = True
        self.cancelled = False
        
        def export_worker():
            try:
                if progress_callback:
                    progress_info = ProgressInfo(10, "Starting video export...")
                    self.gui.root.after(0, lambda: progress_callback(progress_info))
                
                # Create a wrapper progress callback that updates our progress info
                def wrapped_progress_callback(progress_obj):
                    if progress_callback and not self.cancelled:
                        # Convert progress object to our ProgressInfo format
                        if hasattr(progress_obj, 'get_percentage') and hasattr(progress_obj, 'get_status_text'):
                            percentage = progress_obj.get_percentage()
                            message = progress_obj.get_status_text()
                        else:
                            # Fallback if progress object has different interface
                            percentage = getattr(progress_obj, 'percentage', 50)
                            message = getattr(progress_obj, 'message', "Exporting video...")
                        
                        progress_info = ProgressInfo(percentage, message)
                        self.gui.root.after(0, lambda p=progress_info: progress_callback(p))
                
                # Call the export function with correct parameters
                # export_video expects: frames, fps, original_video_path, username=None, user_choice=None
                export_func(
                    marked_frames,      # frames parameter
                    fps,               # fps parameter  
                    video_path,        # original_video_path parameter
                    username=username,
                    user_choice=user_choice
                )
                
                if progress_callback and not self.cancelled:
                    progress_info = ProgressInfo(100, "Video export completed")
                    self.gui.root.after(0, lambda: progress_callback(progress_info))
                
                self.gui.root.after(0, lambda: self.gui.update_status("Marked video export completed"))
                
            except Exception as e:
                error_msg = f"Video export error: {str(e)}"
                self.gui.root.after(0, lambda: self.gui.update_status(error_msg))
            finally:
                self.processing = False
        
        self.current_thread = threading.Thread(target=export_worker)
        self.current_thread.daemon = True
        self.current_thread.start()
        
        return True
