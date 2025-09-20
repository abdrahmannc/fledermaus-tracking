"""
Fast Mode Processing Window
Creates a compact window for fast video processing without frame display
"""

import tkinter as tk
from tkinter import ttk
import threading
import time

class FastModeProgressWindow:
    """
    Compact window for Fast Mode processing showing:
    - Progress bar
    - Detection count
    - Processing time
    - Cancel button
    """
    
    def __init__(self, parent, total_frames, video_name="Video"):
        self.parent = parent
        self.total_frames = total_frames
        self.video_name = video_name
        self.window = None
        self.cancelled = False
        self.start_time = time.time()
        
        # Progress tracking
        self.current_frame = 0
        self.detection_count = 0
        self.last_update_time = time.time()
        
        # UI elements
        self.progress_var = tk.DoubleVar()
        self.progress_label_var = tk.StringVar()
        self.detection_label_var = tk.StringVar()
        self.time_label_var = tk.StringVar()
        
        self.create_window()
        
    def create_window(self):
        """Create the compact progress window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Bat Detection Processing...")
        self.window.geometry("400x200")
        self.window.resizable(False, False)
        
        # Center the window
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="⚡ Schnell-Modus Verarbeitung", 
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Video name
        video_label = ttk.Label(main_frame, text=f"Video: {self.video_name}", 
                               font=("Arial", 9))
        video_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress_label_var.set("Initialisierung...")
        progress_label = ttk.Label(main_frame, textvariable=self.progress_label_var)
        progress_label.pack(pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                          maximum=100, length=350)
        self.progress_bar.pack(pady=(0, 15))
        
        # Statistics frame
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Detection count
        self.detection_label_var.set("Erkennungen: 0")
        detection_label = ttk.Label(stats_frame, textvariable=self.detection_label_var,
                                   font=("Arial", 9, "bold"))
        detection_label.pack(side=tk.LEFT)
        
        # Processing time
        self.time_label_var.set("Zeit: 00:00")
        time_label = ttk.Label(stats_frame, textvariable=self.time_label_var,
                              font=("Arial", 9))
        time_label.pack(side=tk.RIGHT)
        
        # Cancel button
        cancel_frame = ttk.Frame(main_frame)
        cancel_frame.pack(fill=tk.X)
        
        self.cancel_button = ttk.Button(cancel_frame, text="⏹ Abbrechen", 
                                       command=self.cancel_processing)
        self.cancel_button.pack(side=tk.RIGHT)
        
        # Handle window closing
        self.window.protocol("WM_DELETE_WINDOW", self.cancel_processing)
        
        # Start update thread
        self.update_thread = threading.Thread(target=self.update_display, daemon=True)
        self.update_thread.start()
        
    def update_progress(self, frame_number, detections_in_frame=0):
        """Update progress from video processing thread"""
        if self.cancelled:
            return False
            
        self.current_frame = frame_number
        self.detection_count += detections_in_frame
        
        # Throttle updates to avoid GUI lag
        current_time = time.time()
        if current_time - self.last_update_time > 0.1:  # Update every 100ms max
            self.last_update_time = current_time
            
            # Calculate progress percentage
            progress_percent = (frame_number / self.total_frames) * 100 if self.total_frames > 0 else 0
            
            # Thread-safe GUI updates
            if self.window and self.window.winfo_exists():
                self.window.after_idle(self._update_gui, progress_percent, frame_number)
        
        return not self.cancelled
        
    def _update_gui(self, progress_percent, frame_number):
        """Update GUI elements (called from main thread)"""
        try:
            if not self.window or not self.window.winfo_exists():
                return
                
            # Update progress bar
            self.progress_var.set(progress_percent)
            
            # Update progress label
            self.progress_label_var.set(f"Frame {frame_number:,} / {self.total_frames:,} "
                                       f"({progress_percent:.1f}%)")
            
            # Update detection count
            self.detection_label_var.set(f"Erkennungen: {self.detection_count:,}")
            
            # Update processing time
            elapsed = time.time() - self.start_time
            minutes, seconds = divmod(int(elapsed), 60)
            self.time_label_var.set(f"Zeit: {minutes:02d}:{seconds:02d}")
            
            # Estimate remaining time
            if frame_number > 0:
                frames_per_second = frame_number / elapsed
                remaining_frames = self.total_frames - frame_number
                if frames_per_second > 0:
                    eta_seconds = remaining_frames / frames_per_second
                    eta_minutes, eta_seconds = divmod(int(eta_seconds), 60)
                    if eta_minutes > 0:
                        eta_text = f" (ETA: {eta_minutes:02d}:{eta_seconds:02d})"
                        current_time = self.time_label_var.get()
                        if "ETA" not in current_time:
                            self.time_label_var.set(current_time + eta_text)
                            
        except Exception as e:
            # Ignore GUI update errors during shutdown
            pass
    
    def update_display(self):
        """Background thread for smooth GUI updates"""
        while not self.cancelled and self.window and self.window.winfo_exists():
            try:
                # Update display every 200ms
                time.sleep(0.2)
                
                # Update time display
                if self.window and self.window.winfo_exists():
                    elapsed = time.time() - self.start_time
                    minutes, seconds = divmod(int(elapsed), 60)
                    time_text = f"Zeit: {minutes:02d}:{seconds:02d}"
                    
                    # Add ETA if available
                    if self.current_frame > 0:
                        frames_per_second = self.current_frame / elapsed
                        remaining_frames = self.total_frames - self.current_frame
                        if frames_per_second > 0:
                            eta_seconds = remaining_frames / frames_per_second
                            eta_minutes, eta_seconds = divmod(int(eta_seconds), 60)
                            if eta_minutes > 0 or eta_seconds > 0:
                                time_text += f" (ETA: {eta_minutes:02d}:{eta_seconds:02d})"
                    
                    self.window.after_idle(lambda: self.time_label_var.set(time_text))
                    
            except Exception:
                break
    
    def cancel_processing(self):
        """Cancel the processing"""
        self.cancelled = True
        if self.window:
            self.window.destroy()
            
    def is_cancelled(self):
        """Check if processing was cancelled"""
        return self.cancelled
        
    def close(self):
        """Close the window (processing completed)"""
        self.cancelled = True
        if self.window:
            try:
                self.window.destroy()
            except:
                pass
                
    def show_completion_message(self, total_detections, processing_time):
        """Show completion message and close window"""
        if not self.cancelled and self.window and self.window.winfo_exists():
            try:
                # Update final stats
                self.progress_var.set(100)
                self.progress_label_var.set("Verarbeitung abgeschlossen!")
                self.detection_label_var.set(f"Erkennungen: {total_detections:,}")
                
                minutes, seconds = divmod(int(processing_time), 60)
                self.time_label_var.set(f"Gesamtzeit: {minutes:02d}:{seconds:02d}")
                
                # Change cancel button to close
                self.cancel_button.config(text="✓ Schließen")
                
                # Auto-close after 2 seconds
                self.window.after(2000, self.close)
                
            except Exception:
                self.close()