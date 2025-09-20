import tkinter as tk
from tkinter import messagebox, ttk

# Fix matplotlib font issues on Windows

def _is_gui_status_message(message):
    """
    Determine if a status message is a GUI/video status that should be filtered out.
    
    Returns True for messages that should be HIDDEN (GUI/video operations)
    Returns False for messages that should be SHOWN (detection/analysis results)
    """
    if not message:
        return False
    
    # Convert to lowercase for case-insensitive checking
    msg_lower = message.lower()
    
    # GUI/Video status messages to HIDE
    gui_status_patterns = [
        # Video loading/file operations
        'loaded:', 'geladen:', 'video not loaded', 'failed to read video',
        'stereo videos loaded', 'stereo calibration loaded',
        
        # Mode activation messages
        'modus aktiviert', 'detection mode set to', 'aktiviert -',
        
        # Processing start/control messages
        'erkennung gestartet', 'detection already running', 'video gestartet',
        'stop gedrückt', 'processing', 'geöffnet',
        
        # Technical optimization messages
        'opencv optimized', 'optimization warning', 'threads, optimizations enabled',
        'background subtractor optimization',
        
        # Frame processing performance
        'fps (threading optimized)', 'frame ',
        
        # Loading/opening operations
        'öffne ', 'gui geöffnet', 'erstelle ',
        
        # Error messages for file operations (keep detection errors)
        'error loading', 'failed to read', 'calibration not loaded',
        'videos not loaded'
    ]
    
    # Check if message contains any GUI status patterns
    for pattern in gui_status_patterns:
        if pattern in msg_lower:
            return True
    
    # Detection/Analysis messages to KEEP (return False = show these)
    detection_patterns = [
        # Core detection events
        'bat entered', 'bat exited', 'polygon', 'inside', 'outside',
        
        # Analysis results
        'events detected', 'ereignisse gefunden', 'detection finished',
        'analyse abgeschlossen', 'detection completed', 'detection error',
        
        # Validation and results
        'validated', 'validierung', 'analyse', 'ereignisse',
        
        # Export completion (not start)
        'export completed', 'export finished', 'erstellt:'
    ]
    
    # If it's a detection message, always show it
    for pattern in detection_patterns:
        if pattern in msg_lower:
            return False
    
    # For ambiguous messages, default to hiding GUI-style messages
    # Show only if it's clearly important (contains detection keywords)
    return True

def update_status(self, message):
    """Update status - overlay replaces console logging"""
    # 🎥 OVERLAY SYSTEM: Console [STATUS] logging disabled
    # Video overlay system now handles progress feedback
    # Warning/error handling managed internally - removed console output
    if any(keyword in message.lower() for keyword in ['warning', 'error', 'failed', 'fehler']):
        # Warning handled internally - removed console output
        pass
    
    # GUI status section has been removed as requested
    # Keeping only console output for debugging purposes
    if hasattr(self, 'root'):
        self.root.update_idletasks()


def update_progress_bar(self, percentage):
        """Update progress bar if available"""
        if hasattr(self, 'current_progress_dialog') and self.current_progress_dialog:
            self.current_progress_dialog.update_progress(percentage)
  
  
  
  
  
  
  
  
  
  
  
  
  
  
def show_progress_dialog(self, title="Processing Video...", cancelable=True):
        """Show progress dialog for long operations"""
        if hasattr(self, 'current_progress_dialog') and self.current_progress_dialog:
            self.current_progress_dialog.close()
            
        from background_video_processor import ProgressDialog
        self.current_progress_dialog = ProgressDialog(self.root, title, cancelable)
        
        # Connect the progress dialog to the background processor for direct cancellation
        if hasattr(self, 'background_processor') and self.background_processor:
            self.current_progress_dialog.background_processor = self.background_processor
            
        return self.current_progress_dialog
    
    
    
    
    
def hide_progress_dialog(self):
        """Hide progress dialog"""
        if hasattr(self, 'current_progress_dialog') and self.current_progress_dialog:
            self.current_progress_dialog.close()
            self.current_progress_dialog = None
            
            
            
            
            
            
            
            
            
            
            
            
            
            
def show_processing_animation(self):
        """Zeigt einen einfachen Verarbeitungsdialog an"""
        if hasattr(self, 'animation_window') and self.animation_window:
            return
            
        self.animation_window = tk.Toplevel(self.root)
        self.animation_window.title("Video wird verarbeitet")
        self.animation_window.resizable(False, False)
        self.animation_window.transient(self.root)
        self.animation_window.grab_set()
        
        # Fenster zentrieren
        window_width = 350
        window_height = 150
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.animation_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Inhalt
        ttk.Label(self.animation_window, text="Video wird verarbeitet...", 
                 font=('Segoe UI', 11, 'bold')).pack(pady=10)
        
        progress = ttk.Progressbar(self.animation_window, mode='indeterminate', length=300)
        progress.pack(pady=5)
        progress.start()
        
        self.animation_status = tk.StringVar(value="Videoframes werden analysiert...")
        ttk.Label(self.animation_window, textvariable=self.animation_status).pack(pady=5)
        
        # Allow immediate closing of animation window
        def force_close_animation():
            try:
                # Give user option but don't block closing
                if hasattr(self.detector, 'detection_active') and self.detector.detection_active:
                    result = messagebox.askyesno(
                        "Verarbeitung beenden", 
                        "Möchten Sie die Verarbeitung abbrechen?",
                        parent=self.animation_window
                    )
                    if not result:
                        return  # User chose not to close
                    
                    # Stop detection immediately
                    self.detector.detection_active = False
                
                # Close window immediately
                self.animation_window.grab_release()
                self.animation_window.destroy()
                self.animation_window = None
                
            except Exception as e:
                # Error closing animation window - handled internally
                # Force close anyway
                try:
                    if hasattr(self, 'animation_window') and self.animation_window:
                        self.animation_window.grab_release()
                        self.animation_window.destroy()
                        self.animation_window = None
                except:
                    pass
        
        self.animation_window.protocol("WM_DELETE_WINDOW", force_close_animation)
        
        
        
        
def hide_processing_animation(self):
        """Verarbeitungsdialog ausblenden"""
        if hasattr(self, 'animation_window') and self.animation_window:
            try:
                self.animation_window.grab_release()
                self.animation_window.destroy()
                self.animation_window = None
            except Exception as e:
                # Error hiding animation window - handled internally
                self.animation_window = None
        self.animation_window = None
        self.animation_canvas = None
        
        
        
        
        
        
        
        
class status:
    def update_status(self, msg):
        """Update status - overlay replaces console logging"""
        # 🎥 OVERLAY SYSTEM: Console [STATUS] logging disabled
        # Video overlay system now handles progress feedback
        # Warning/error handling managed internally - removed console output
        if any(keyword in msg.lower() for keyword in ['warning', 'error', 'failed', 'fehler']):
            # Warning handled internally - removed console output
            pass
        if hasattr(self, 'root'):
            self.root.update_idletasks()

    def update_status(self, msg):
        """Update status - overlay replaces console logging"""
        # 🎥 OVERLAY SYSTEM: Console [STATUS] logging disabled
        # Video overlay system now handles progress feedback
        # Only show warnings and errors in console
        if any(keyword in msg.lower() for keyword in ['warning', 'error', 'failed', 'fehler']):
            print(f"[WARNING] {msg}")
        if hasattr(self, 'root'):
            self.root.update_idletasks()
        
    def update_status(self, message):
        """Update status - overlay replaces console logging"""
        # 🎥 OVERLAY SYSTEM: Console [STATUS] logging disabled
        # Video overlay system now handles progress feedback
        # Warning/error handling managed internally - removed console output
        if any(keyword in message.lower() for keyword in ['warning', 'error', 'failed', 'fehler']):
            # Warning handled internally - removed console output
            pass
        if hasattr(self, 'root'):
            self.root.update_idletasks() 