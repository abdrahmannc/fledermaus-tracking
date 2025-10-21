
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
import threading

# Fix matplotlib font issues on Windows

def format_time(seconds):
    """Format seconds to HH:MM:SS format"""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"






def show_frame(self, frame):
        """Thread-safe frame display method"""
        # Ensure this runs in the main thread
        if threading.current_thread() is not threading.main_thread():
            self.root.after(0, lambda: self.show_frame(frame))
            return
            
        try:
            # Store original frame for drawing operations
            self.original_frame = frame.copy()
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            
            # Check if canvas is still valid
            if not hasattr(self, 'canvas') or not self.canvas.winfo_exists():
                return
                
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width > 0 and canvas_height > 0:
                # CRITICAL FIX: Calculate scaling factors using original video dimensions
                # NOT the displayed frame dimensions which may be scaled
                if hasattr(self, 'cap') and self.cap and self.cap.isOpened():
                    # Get original video dimensions from video capture
                    original_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    original_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    
                    # Debug coordinate scaling fix
                    frame_height, frame_width = frame.shape[:2]
                    if not hasattr(self, '_debug_scaling_logged'):
                        # Coordinate scaling debug info removed for cleaner output
                        self._debug_scaling_logged = True
                else:
                    # Fallback to frame dimensions if video cap not available
                    original_height, original_width = frame.shape[:2]
                
                # Initialize default offsets
                self.canvas_x_offset = 0
                self.canvas_y_offset = 0
                
                self.canvas_scale_x = canvas_width / original_width
                self.canvas_scale_y = canvas_height / original_height
                
                # Preserve aspect ratio while fitting in canvas
                scale = min(self.canvas_scale_x, self.canvas_scale_y)
                new_width = int(original_width * scale)
                new_height = int(original_height * scale)
                
                # Update scale factors to match actual displayed size
                self.canvas_scale_x = new_width / original_width
                self.canvas_scale_y = new_height / original_height
                
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Center the image in the canvas
                x_offset = (canvas_width - new_width) // 2
                y_offset = (canvas_height - new_height) // 2
                
                # Store offset values for coordinate calculations
                self.canvas_x_offset = x_offset
                self.canvas_y_offset = y_offset
            
            self.tk_image = ImageTk.PhotoImage(image=img)
            self.canvas.delete("all")  # Clear previous content
            self.canvas_image = self.canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.tk_image)
            
            # Redraw polygon areas if they exist
            self.redraw_polygons_on_canvas()
            
        except tk.TclError as e:
            if "invalid command name" in str(e):
                # Canvas was destroyed, stop video streaming
                self.playing = False
                # Canvas destroyed, stopping video - handled internally
            else:
                # Canvas error - handled internally
                pass
        except Exception as e:
            # Frame display error - handled internally
            pass




def play_video(self):
    if not hasattr(self, "cap") or not self.cap.isOpened():
        messagebox.showerror("Fehler", "Kein Video geladen oder Video kann nicht geöffnet werden.")
        return
    self.playing = True
    self._stream_video()

def pause_video(self):
    self.playing = False

def stop_video(self):
    self.playing = False
    if hasattr(self, "cap") and self.cap.isOpened():
        self.seek_to_frame(0)

def step_forward(self):
    """Step forward one frame"""
    if hasattr(self, "cap") and self.cap.isOpened():
        was_playing = self.playing
        self.playing = False
        
        current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        next_frame = min(current_frame + 1, self.total_frames - 1)
        self.seek_to_frame(next_frame)
        
        if was_playing:
            self.playing = True
            self._stream_video()

def step_backward(self):
    """Step backward one frame"""
    if hasattr(self, "cap") and self.cap.isOpened():
        was_playing = self.playing
        self.playing = False
        
        current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        prev_frame = max(current_frame - 1, 0)
        self.seek_to_frame(prev_frame)
        
        if was_playing:
            self.playing = True
            self._stream_video()

def jump_seconds(self, seconds):
    """Jump forward or backward by specified seconds"""
    if hasattr(self, "cap") and self.cap.isOpened():
        current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        frame_jump = int(seconds * self.fps)
        new_frame = max(0, min(current_frame + frame_jump, self.total_frames - 1))
        self.seek_to_frame(new_frame)

def seek_to_frame(self, frame_number):
    """Seek to specific frame number"""
    if hasattr(self, "cap") and self.cap.isOpened():
        frame_number = max(0, min(frame_number, self.total_frames - 1))
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        self.current_frame_idx = frame_number
        
        ret, frame = self.cap.read()
        if ret:
            frame_small = cv2.resize(frame, None, fx=self.scale_factor, fy=self.scale_factor)
            
            # Add ROI overlay if ROI is set
            if hasattr(self, 'roi') and self.roi is not None:
                frame_with_overlay = frame_small.copy()
                x, y, w, h = map(int, self.roi)
                # Scale ROI coordinates to match resized frame
                x_scaled = int(x * self.scale_factor)
                y_scaled = int(y * self.scale_factor)
                w_scaled = int(w * self.scale_factor)
                h_scaled = int(h * self.scale_factor)
                
                # Draw thick yellow ROI rectangle for better visibility
                cv2.rectangle(frame_with_overlay, (x_scaled, y_scaled), (x_scaled + w_scaled, y_scaled + h_scaled), (0, 255, 255), 3)
                # Add corner markers for extra visibility
                corner_size = int(10 * self.scale_factor)
                # Top-left corner
                cv2.line(frame_with_overlay, (x_scaled, y_scaled), (x_scaled + corner_size, y_scaled), (0, 255, 255), 5)
                cv2.line(frame_with_overlay, (x_scaled, y_scaled), (x_scaled, y_scaled + corner_size), (0, 255, 255), 5)
                # Top-right corner
                cv2.line(frame_with_overlay, (x_scaled + w_scaled, y_scaled), (x_scaled + w_scaled - corner_size, y_scaled), (0, 255, 255), 5)
                cv2.line(frame_with_overlay, (x_scaled + w_scaled, y_scaled), (x_scaled + w_scaled, y_scaled + corner_size), (0, 255, 255), 5)
                # Bottom-left corner
                cv2.line(frame_with_overlay, (x_scaled, y_scaled + h_scaled), (x_scaled + corner_size, y_scaled + h_scaled), (0, 255, 255), 5)
                cv2.line(frame_with_overlay, (x_scaled, y_scaled + h_scaled), (x_scaled, y_scaled + h_scaled - corner_size), (0, 255, 255), 5)
                # Bottom-right corner
                cv2.line(frame_with_overlay, (x_scaled + w_scaled, y_scaled + h_scaled), (x_scaled + w_scaled - corner_size, y_scaled + h_scaled), (0, 255, 255), 5)
                cv2.line(frame_with_overlay, (x_scaled + w_scaled, y_scaled + h_scaled), (x_scaled + w_scaled, y_scaled + h_scaled - corner_size), (0, 255, 255), 5)
                
                self.show_frame(frame_with_overlay)
            else:
                self.show_frame(frame_small)
            
        # Update UI elements
        self.update_timeline_and_time()
        self.frame_var.set(str(frame_number))

def seek_to_time(self, time_seconds):
    """Seek to specific time in seconds"""
    if hasattr(self, "cap") and self.cap.isOpened():
        frame_number = int(time_seconds * self.fps)
        self.seek_to_frame(frame_number)

def goto_frame(self, event=None):
    """Go to frame number entered by user"""
    try:
        frame_number = int(self.frame_var.get())
        self.seek_to_frame(frame_number)
    except ValueError:
        # Reset to current frame if invalid input
        self.frame_var.set(str(self.current_frame_idx))

def on_timeline_change(self, value):
    """Handle timeline scale changes (seeking)"""
    if self.seeking:  # Prevent recursive calls
        return
        
    if hasattr(self, "cap") and self.cap.isOpened() and self.total_frames > 0:
        # Convert percentage to frame number
        percentage = float(value)
        frame_number = int((percentage / 100.0) * self.total_frames)
        
        self.seeking = True
        was_playing = self.playing
        self.playing = False  # Pause during seeking
        
        self.seek_to_frame(frame_number)
        
        # Resume playing if it was playing before seeking
        if was_playing:
            self.root.after(100, lambda: self._resume_after_seek())
        
        self.seeking = False

def _resume_after_seek(self):
    """Resume playback after seeking"""
    self.playing = True
    self._stream_video()

def update_timeline_and_time(self):
    """Thread-safe timeline position and time display update"""
    # Ensure this runs in the main thread
    if threading.current_thread() is not threading.main_thread():
        self.root.after(0, self.update_timeline_and_time)
        return
        
    try:
        if hasattr(self, "cap") and self.cap.isOpened() and self.total_frames > 0:
            current_frame = self.current_frame_idx
            percentage = (current_frame / self.total_frames) * 100
            
            # Update timeline without triggering seek
            if hasattr(self, 'timeline_var') and hasattr(self, 'seeking'):
                self.seeking = True
                self.timeline_var.set(percentage)
                self.seeking = False
            
            # Update time display
            current_sec = current_frame / self.fps if self.fps else 0
            total_sec = self.total_frames / self.fps if self.fps else 0
            if hasattr(self, 'time_var'):
                self.time_var.set(f"{format_time(current_sec)} / {format_time(total_sec)}")
                
    except tk.TclError as e:
        # Timeline update error - handled internally
        pass
    except Exception as e:
        # Timeline update error - handled internally
        pass

def enable_video_controls(self):
    """Enable all video control buttons"""
    if hasattr(self, 'btn_play'):
        self.btn_play.config(state=tk.NORMAL)
    if hasattr(self, 'btn_pause'):
        self.btn_pause.config(state=tk.NORMAL)
    if hasattr(self, 'btn_stop_video'):
        self.btn_stop_video.config(state=tk.NORMAL)
    if hasattr(self, 'btn_step_forward'):
        self.btn_step_forward.config(state=tk.NORMAL)
    if hasattr(self, 'btn_step_back'):
        self.btn_step_back.config(state=tk.NORMAL)
    if hasattr(self, 'timeline_scale'):
        self.timeline_scale.config(state=tk.NORMAL)
    if hasattr(self, 'frame_entry'):
        self.frame_entry.config(state=tk.NORMAL)

def set_speed(self, event=None):
    try:
        self.playback_speed = float(self.speed_var.get().replace("x", ""))
    except ValueError:
        self.playback_speed = 1.0

def _stream_video(self):
    """Thread-safe video streaming method"""
    try:
        if not self.playing:
            return
            
        # Check if video capture is still valid
        if not hasattr(self, "cap") or not self.cap.isOpened():
            self.playing = False
            return
            
        ret, frame = self.cap.read()
        if not ret:
            self.playing = False
            return
            
        self.current_frame_idx = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        frame_small = cv2.resize(frame, None, fx=self.scale_factor, fy=self.scale_factor)
        
        # Add ROI overlay if ROI is set
        if hasattr(self, 'roi') and self.roi is not None:
            frame_with_overlay = frame_small.copy()
            x, y, w, h = map(int, self.roi)
            # Scale ROI coordinates to match resized frame
            x_scaled = int(x * self.scale_factor)
            y_scaled = int(y * self.scale_factor)
            w_scaled = int(w * self.scale_factor)
            h_scaled = int(h * self.scale_factor)
            
            # Draw thick yellow ROI rectangle for better visibility
            cv2.rectangle(frame_with_overlay, (x_scaled, y_scaled), (x_scaled + w_scaled, y_scaled + h_scaled), (0, 255, 255), 3)
            # Add corner markers for extra visibility
            corner_size = int(10 * self.scale_factor)
            # Top-left corner
            cv2.line(frame_with_overlay, (x_scaled, y_scaled), (x_scaled + corner_size, y_scaled), (0, 255, 255), 5)
            cv2.line(frame_with_overlay, (x_scaled, y_scaled), (x_scaled, y_scaled + corner_size), (0, 255, 255), 5)
            # Top-right corner
            cv2.line(frame_with_overlay, (x_scaled + w_scaled, y_scaled), (x_scaled + w_scaled - corner_size, y_scaled), (0, 255, 255), 5)
            cv2.line(frame_with_overlay, (x_scaled + w_scaled, y_scaled), (x_scaled + w_scaled, y_scaled + corner_size), (0, 255, 255), 5)
            # Bottom-left corner
            cv2.line(frame_with_overlay, (x_scaled, y_scaled + h_scaled), (x_scaled + corner_size, y_scaled + h_scaled), (0, 255, 255), 5)
            cv2.line(frame_with_overlay, (x_scaled, y_scaled + h_scaled), (x_scaled, y_scaled + h_scaled - corner_size), (0, 255, 255), 5)
            # Bottom-right corner
            cv2.line(frame_with_overlay, (x_scaled + w_scaled, y_scaled + h_scaled), (x_scaled + w_scaled - corner_size, y_scaled + h_scaled), (0, 255, 255), 5)
            cv2.line(frame_with_overlay, (x_scaled + w_scaled, y_scaled + h_scaled), (x_scaled + w_scaled, y_scaled + h_scaled - corner_size), (0, 255, 255), 5)
            
            # Show frame with ROI overlay
            self.show_frame(frame_with_overlay)
        else:
            # Show frame without overlay
            self.show_frame(frame_small)
        
        # Update time displays (thread-safe)
        current_sec = self.current_frame_idx / self.fps
        if hasattr(self, 'update_time_label'):
            self.update_time_label(current_sec)
        if hasattr(self, 'update_timeline_and_time'):
            self.update_timeline_and_time()
        
        # Schedule next frame
        delay = max(1, int(1000 / (self.fps * self.playback_speed)))
        self.root.after(delay, self._stream_video)
        
    except Exception as e:
        # Video streaming error - handled internally
        pass
        self.playing = False
    
def update_time_label(self, current_sec):
    total_sec = self.total_frames / self.fps if self.fps else 0
    self.time_var.set(f"{format_time(current_sec)} / {format_time(total_sec)}")

def enable_export_buttons(self):
    self.btn_export_csv.config(state=tk.NORMAL)
    self.btn_export_pdf.config(state=tk.NORMAL)
    # Note: btn_pdf_main was removed from Hauptaktionen section
    if hasattr(self, 'btn_pdf_main'):
        self.btn_pdf_main.config(state=tk.NORMAL)  # Enable the main PDF button if it exists
    self.btn_export_flightMap.config(state=tk.NORMAL)



