"""
GUI Integration module for 3D Analysis and Stereo Vision

This module bridges the GUI main application with the 3D analysis functionality 
in the detection module, providing a clean interface for the GUI to access 
3D analysis features.
"""

from tkinter import messagebox
import sys
import os
import importlib.util

# Import the actual 3D analysis functions from the detection module
try:
    # PyInstaller-compatible import approach
    import sys
    import os
    
    # Add detection folder to path for import
    detection_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "detection")
    if detection_path not in sys.path:
        sys.path.insert(0, detection_path)
    
    # Import using __import__ with the problematic filename
    analysis_3d_module = __import__("3d_analysis_and_stereo_vision")
    
    # Import functions from the loaded module
    format_time = analysis_3d_module.format_time
    STEREO_3D_AVAILABLE = analysis_3d_module.STEREO_3D_AVAILABLE
    StereoVisionModule = analysis_3d_module.StereoVisionModule
    show_3d_visualization = analysis_3d_module.show_3d_visualization
    switch_to_2d_mode = analysis_3d_module.switch_to_2d_mode
    switch_to_3d_mode = analysis_3d_module.switch_to_3d_mode
    switch_to_hybrid_mode = analysis_3d_module.switch_to_hybrid_mode
    load_stereo_videos = analysis_3d_module.load_stereo_videos
    start_3d_analysis = analysis_3d_module.start_3d_analysis
    on_3d_analysis_complete = analysis_3d_module.on_3d_analysis_complete
    on_3d_analysis_error = analysis_3d_module.on_3d_analysis_error
    view_3d_visualization = analysis_3d_module.view_3d_visualization
    open_3d_analysis_gui = analysis_3d_module.open_3d_analysis_gui
    
    # Check if all required dependencies are available
    try:
        pass
        
        ANALYSIS_3D_AVAILABLE = True
        # Module loaded successfully - removed print statement for cleaner output
        
    except ImportError as e:
        ANALYSIS_3D_AVAILABLE = False
        # 3D Analysis dependencies not fully available - handled internally
        
except ImportError as e:
    # Could not import 3D analysis functions - handled internally
    ANALYSIS_3D_AVAILABLE = False
    
    # Provide fallback functions
    def show_3d_visualization(self):
        messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")
    
    def switch_to_2d_mode(self):
        pass  # Already in 2D mode
    
    def switch_to_3d_mode(self):
        messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")
    
    def switch_to_hybrid_mode(self):
        messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")
    
    def load_stereo_videos(self):
        messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")
    
    def start_3d_analysis(self):
        messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")
    
    def on_3d_analysis_complete(self, results):
        pass
    
    def on_3d_analysis_error(self, error):
        pass
    
    def view_3d_visualization(self):
        messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")
    
    def open_3d_analysis_gui(self):
        messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")
    
    def start_stereo_calibration(self):
        messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")
    
    def progress_callback(self, progress):
        pass
    
    def run_detection(self):
        messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")
    
    def create_visualization(self):
        messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")


def check_3d_availability():
    """Check if 3D analysis is available and return status"""
    return ANALYSIS_3D_AVAILABLE


def get_3d_status_message():
    """Get a status message about 3D availability"""
    if ANALYSIS_3D_AVAILABLE:
        return "✓ 3D Analysis verfügbar"
    else:
        return "⚠ 3D Analysis nicht vollständig verfügbar"


# Export the availability flag for the main GUI
__all__ = [
    'ANALYSIS_3D_AVAILABLE',
    'check_3d_availability', 
    'get_3d_status_message',
    'show_3d_visualization',
    'switch_to_2d_mode',
    'switch_to_3d_mode', 
    'switch_to_hybrid_mode',
    'load_stereo_videos',
    'start_3d_analysis',
    'on_3d_analysis_complete',
    'on_3d_analysis_error',
    'view_3d_visualization',
    'open_3d_analysis_gui',
    'start_stereo_calibration',
    'progress_callback',
    'run_detection',
    'create_visualization'
]