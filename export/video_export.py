import cv2
from tkinter import messagebox, filedialog
from datetime import datetime
import os
import getpass

def export_video(frames, fps, original_video_path, username=None, user_choice=None):
    """
    Export marked frames as video to the per-video results folder
    
    Args:
        frames: List of frames to export
        fps: Frames per second
        original_video_path: Path to the source video
        username: Optional username for file metadata
        user_choice: Optional user choice for folder handling ('reuse', 'new_version', etc.)
    
    Returns:
        str: Path to exported video or None if failed
    """
    if not frames:
        messagebox.showinfo("Video exportieren", "Keine Bilder zum Exportieren vorhanden.")
        return None

    try:
        # Import result organization utilities
        from utils.result_organizer import create_video_result_structure
        
        # Create structured result directories with user choice
        structure = create_video_result_structure(original_video_path, user_choice=user_choice)
        
        # Generate standardized filename for marked video
        if username is None:
            try:
                username = getpass.getuser()
            except:
                username = "user"
        
        # Create filename with timestamp and username
        current_datetime = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"marked_video_{current_datetime}_{username}.avi"
        output_path = os.path.join(structure["base"], filename)
        
        # Ensure the directory exists
        os.makedirs(structure["base"], exist_ok=True)
        
    except Exception as e:
        print(f"[WARNING] Failed to use structured organization, falling back to user selection: {e}")
        # Fallback to manual folder selection
        folder_path = filedialog.askdirectory(title="Ordner zum Speichern des Videos auswählen")
        if not folder_path:
            messagebox.showinfo("Export abgebrochen", "Kein Ordner ausgewählt.")
            return None

        # Generate filename with original video name and timestamp
        base_name = os.path.splitext(os.path.basename(original_video_path))[0]
        current_datetime = datetime.now().strftime('%Y%m%d_%H%M%S')
        if username is None:
            try:
                username = getpass.getuser()
            except:
                username = "user"
        
        filename = f"{base_name}_marked_{current_datetime}_{username}.avi"
        output_path = os.path.join(folder_path, filename)

    try:
        # Get frame dimensions
        height, width = frames[0].shape[:2]
        
        # Initialize VideoWriter with XVID codec
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not writer.isOpened():
            raise Exception("Failed to initialize video writer")

        # Write all frames to the video
        for frame in frames:
            writer.write(frame)
        
        writer.release()

        print(f"[INFO] Markiertes Video exportiert nach: {output_path}")
        messagebox.showinfo("Export abgeschlossen", f"Markiertes Video wurde gespeichert unter:\n{output_path}")
        return output_path
        
    except Exception as e:
        print(f"[ERROR] Video export failed: {e}")
        messagebox.showerror("Export-Fehler", f"Fehler beim Video-Export: {str(e)}")
        return None
