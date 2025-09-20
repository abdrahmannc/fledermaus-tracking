
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import cv2

# Fix matplotlib font issues on Windows

# Import video quality analysis
from utils.video_quality import analyze_video_quality
from utils.result_organizer import analyze_existing_folder, get_video_name_from_path

# Check for 3D Stereo Extension availability
try:
    STEREO_3D_AVAILABLE = True
except ImportError:
    STEREO_3D_AVAILABLE = False






def load_video(self, event=None):
        """Enhanced video loading with structured workflow and analysis history check"""
        try:
            self.video_path = filedialog.askopenfilename(
                title="IR-Video auswählen",
                filetypes=[("Video-Dateien", "*.mp4 *.avi *.mov"), ("Alle Dateien", "*.*")]
            )
            if not self.video_path:
                return
                
        except KeyboardInterrupt:
            # User cancelled the dialog with Ctrl+C
            # Video selection cancelled - handled internally
            return
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Öffnen der Dateiauswahl: {str(e)}")
            return
            
        # Check if this video has been analyzed before
        analysis_info = self.check_existing_analysis(self.video_path)
        
        if analysis_info["exists"]:
            # Show analysis history dialog
            action = self.show_analysis_history_dialog(analysis_info)
            
            if action == "load_existing":
                # Load existing analysis instead of starting new
                self.load_existing_analysis(analysis_info)
                return
            elif action == "continue_new":
                # User wants to continue with new analysis - check folder strategy
                
                # Get clean video name and check folder situation
                video_name = get_video_name_from_path(os.path.basename(self.video_path))
                results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results')
                results_dir = os.path.abspath(results_dir)
                
                # Analyze existing folder for better user information
                existing_folder_info = analyze_existing_folder(os.path.join(results_dir, video_name))
                
                if existing_folder_info["exists"]:
                    # Show folder choice dialog
                    folder_choice = self.show_folder_choice_dialog(video_name, existing_folder_info)
                    
                    if folder_choice == "cancel":
                        return
                    
                    # Store the user's folder choice for later use
                    self.user_folder_choice = folder_choice
                else:
                    # No existing folder, can proceed normally
                    self.user_folder_choice = None
            else:
                # User cancelled
                return
        
        # Continue with normal video loading
        self.load_video_file()
        
        # Show video workflow status
        self.update_video_workflow_status("loaded")
        
        
        
        
        
        
def load_video_file(self, file_path=None):
        """Load video file and initialize basic properties"""
        if file_path:
            self.video_path = file_path
        self.cap = cv2.VideoCapture(self.video_path)
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.fps = fps if fps and fps > 0 else 30
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame_idx = 0

        ret, frame = self.cap.read()
        if ret:
            frame_small = cv2.resize(frame, None, fx=self.scale_factor, fy=self.scale_factor)
            green_frame = frame_small.copy()
            green_frame[:, :, 0] = 0
            green_frame[:, :, 2] = 0
            self.show_frame(green_frame)
        else:
            messagebox.showerror("Fehler", "Video konnte nicht gelesen werden.")
            return

        info = analyze_video_quality(self.video_path)
        if "error" in info:
            # Error loading video - status shown in GUI
            return

        self.video_quality_info = info
        if info["warnings"]:
            messagebox.showwarning("Video-Qualitätswarnung", "\n".join(info["warnings"]))

        high_motion_minutes = info.get("high_motion_minutes", [])
        if high_motion_minutes:
            motion_times = ", ".join(f"{t:.2f} min" for t in high_motion_minutes)
            messagebox.showinfo("Kamerabewegung", f"\u26a0\ufe0f Hohe Kamerabewegung in:\n\n{motion_times}")

        # Video information displayed in GUI - removed console output
        self.detector.video_path = self.video_path
        self.detector.btn_select_roi = self.btn_select_roi
        self.detector.scale_factor = self.scale_factor

        self.btn_play.config(state=tk.NORMAL)
        self.btn_pause.config(state=tk.NORMAL)
        self.btn_stop_video.config(state=tk.NORMAL)
        self.btn_select_roi.config(state=tk.NORMAL)
        self.btn_toggle_drawing.config(state=tk.NORMAL)
        self.btn_clear_polygons.config(state=tk.NORMAL)
        
        # Enable new video controls
        self.enable_video_controls()
        
        # Initialize timeline
        if hasattr(self, 'timeline_scale') and self.total_frames > 0:
            self.timeline_scale.config(to=100)  # Percentage-based
            self.timeline_var.set(0)
        
        # Initialize frame counter
        if hasattr(self, 'frame_var'):
            self.frame_var.set("0")
        
        # Initialize timeline and time display
        if hasattr(self, 'update_timeline_and_time'):
            self.update_timeline_and_time()
        
        # Enable 3D Analysis button (Teil 3) - works independently of 2D detection
        if STEREO_3D_AVAILABLE and hasattr(self, 'btn_3d_teil3'):
            self.btn_3d_teil3.config(state=tk.NORMAL)
        
        # Use centralized function to determine start button state
        self.update_start_button_state()
        self.update_time_label(0)





def update_start_button_state(self):
        """Centralized function to determine when detection can be started"""
        # Detection can be started if:
        # 1. Video is loaded, AND
        # 2. Either traditional ROI is selected OR polygon areas are defined OR neither (whole video detection)
        if self.video_path:
            # Video is loaded, enable detection
            # Detection works with: traditional ROI, polygon areas, or whole video
            self.btn_start.config(state=tk.NORMAL)
        else:
            # No video loaded, disable detection
            self.btn_start.config(state=tk.DISABLED)





def on_select_roi(self, event=None):
        try:
            roi = self.detector.select_roi()
        except RuntimeError as e:
            messagebox.showerror("Fehler", str(e))
            return
        if roi is not None:
            self.roi = roi
            # ROI selected - status shown in GUI
            # Use centralized state management
            self.update_start_button_state()
            cap = cv2.VideoCapture(self.detector.video_path)
            ret, frame = cap.read()
            cap.release()
            if ret:
                x, y, w, h = map(int, roi)
                frame_with_roi = frame.copy()
                cv2.rectangle(frame_with_roi, (x, y), (x + w, y + h), (0, 255, 0), 2)
                self.show_frame(frame_with_roi)
        else:
            # ROI selection cancelled - handled internally
            # Update button state even if ROI selection was cancelled
            self.update_start_button_state()