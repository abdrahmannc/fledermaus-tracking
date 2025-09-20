"""
Result Organization Utilities
Provides structured organization for analysis results based on video files
"""

import os
import re
from datetime import datetime


def get_video_name_from_path(video_path):
    """
    Extract clean video name from path for folder naming
    
    Args:
        video_path (str): Full path to video file
        
    Returns:
        str: Clean video name suitable for folder naming
    """
    if not video_path:
        return "unknown_video"
    
    try:
        # Get filename without extension
        filename = os.path.splitext(os.path.basename(video_path))[0]
        
        # Clean filename for folder naming (remove special characters)
        # Allow letters, numbers, underscores, hyphens
        clean_name = re.sub(r'[^\w\-_]', '_', filename)
        
        # Remove multiple consecutive underscores
        clean_name = re.sub(r'_+', '_', clean_name)
        
        # Remove leading/trailing underscores
        clean_name = clean_name.strip('_')
        
        if not clean_name:
            return "unknown_video"
            
        return clean_name
    except Exception:
        return "unknown_video"


def create_video_result_structure(video_path, base_results_dir=None, user_choice=None):
    """
    Create structured directory hierarchy for a specific video's results
    
    Args:
        video_path (str): Path to the video file being analyzed
        base_results_dir (str): Base directory for results (optional)
        user_choice (str): User's choice for handling existing folders ('reuse', 'new_version', 'cancel')
        
    Returns:
        dict: Dictionary with paths for different result types, or None if cancelled
    """
    if base_results_dir is None:
        if video_path:
            # Use app root results directory
            app_root = os.path.dirname(os.path.dirname(__file__))  # Go up from utils/
            base_results_dir = os.path.join(app_root, "results")
        else:
            base_results_dir = "results"
    
    video_name = get_video_name_from_path(video_path)
    
    # Get folder path based on user choice or folder existence
    folder_result = get_video_folder_with_user_choice(base_results_dir, video_name, user_choice)
    
    if folder_result is None:
        return None  # User cancelled
    
    video_results_dir, folder_choice = folder_result
    
    # Define structure - all files directly in the video folder
    structure = {
        "base": video_results_dir,
        "video_name": os.path.basename(video_results_dir),  # Final folder name used
        "choice": folder_choice,  # Record what choice was made
        "is_existing": folder_choice in ['reuse', 'overwrite']
    }
    
    # Create directory
    os.makedirs(video_results_dir, exist_ok=True)
    
    return structure


def get_unique_video_folder(base_dir, video_name):
    """
    Get a unique folder name for the video, handling conflicts with existing folders
    
    Args:
        base_dir (str): Base results directory
        video_name (str): Clean video name
        
    Returns:
        str: Unique folder path
    """
    # Try the base name first
    folder_path = os.path.join(base_dir, video_name)
    
    if not os.path.exists(folder_path):
        return folder_path
    
    # If folder exists, try numbered versions
    counter = 1
    while True:
        numbered_name = f"{video_name}_{counter}"
        folder_path = os.path.join(base_dir, numbered_name)
        
        if not os.path.exists(folder_path):
            return folder_path
            
        counter += 1
        
        # Safety check to prevent infinite loop
        if counter > 9999:
            # Use timestamp as last resort
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return os.path.join(base_dir, f"{video_name}_{timestamp}")


def get_video_folder_with_user_choice(base_dir, video_name, user_choice=None):
    """
    Get video folder path with user choice for handling existing folders
    
    Args:
        base_dir (str): Base results directory
        video_name (str): Clean video name
        user_choice (str): Pre-determined user choice ('reuse', 'new_version', 'cancel')
        
    Returns:
        tuple: (folder_path, choice) or None if cancelled
    """
    primary_folder = os.path.join(base_dir, video_name)
    
    # If folder doesn't exist, create it
    if not os.path.exists(primary_folder):
        return primary_folder, "new"
    
    # Folder exists - handle based on user choice
    if user_choice == "reuse":
        return primary_folder, "reuse"
    elif user_choice == "new_version":
        # Create numbered version
        counter = 1
        while True:
            numbered_name = f"{video_name}_{counter}"
            folder_path = os.path.join(base_dir, numbered_name)
            
            if not os.path.exists(folder_path):
                return folder_path, "new_version"
                
            counter += 1
            
            # Safety check
            if counter > 9999:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return os.path.join(base_dir, f"{video_name}_{timestamp}"), "new_version"
    elif user_choice == "cancel":
        return None
    else:
        # No user choice provided - this should be handled by the GUI
        # For backward compatibility, return the primary folder
        return primary_folder, "reuse"


def analyze_existing_folder(folder_path):
    """
    Analyze what files exist in a folder to help user make decisions
    
    Args:
        folder_path (str): Path to the existing folder
        
    Returns:
        dict: Information about existing files
    """
    if not os.path.exists(folder_path):
        return {"exists": False, "files": [], "analysis_count": 0}
    
    try:
        files = os.listdir(folder_path)
        
        analysis_files = {
            "csv": [],
            "pdf": [],
            "videos": [],
            "images": [],
            "other": []
        }
        
        for file in files:
            file_lower = file.lower()
            if file_lower.endswith('.csv'):
                analysis_files["csv"].append(file)
            elif file_lower.endswith('.pdf'):
                analysis_files["pdf"].append(file)
            elif file_lower.endswith('.avi') or file_lower.endswith('.mp4'):
                analysis_files["videos"].append(file)
            elif file_lower.endswith('.png') or file_lower.endswith('.jpg'):
                analysis_files["images"].append(file)
            else:
                analysis_files["other"].append(file)
        
        # Get latest modification time
        latest_time = None
        if files:
            try:
                latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(folder_path, f)))
                latest_time = datetime.fromtimestamp(
                    os.path.getmtime(os.path.join(folder_path, latest_file))
                ).strftime("%d.%m.%Y %H:%M")
            except:
                latest_time = "Unbekannt"
        
        total_analysis_files = len(analysis_files["csv"]) + len(analysis_files["pdf"]) + len(analysis_files["videos"])
        
        return {
            "exists": True,
            "files": analysis_files,
            "total_files": len(files),
            "analysis_count": total_analysis_files,
            "latest_modification": latest_time,
            "folder_path": folder_path
        }
        
    except Exception as e:
        return {"exists": True, "error": str(e), "files": [], "analysis_count": 0}


def get_standardized_filename(file_type, video_folder_name):
    """
    Get standardized filename for different output types
    
    Args:
        file_type (str): Type of file ('report', 'detections', 'flugweg', 'marked_video')
        video_folder_name (str): Name of the video folder
        
    Returns:
        str: Standardized filename
    """
    filename_map = {
        'report': 'report.pdf',
        'report_text': 'report.txt', 
        'detections': 'detections.csv',
        'flugweg': 'flugweg.png',
        'marked_video': 'marked_video.mp4',
        'flight_paths': 'flight_paths.png'
    }
    
    return filename_map.get(file_type, f"{file_type}.txt")


def get_analysis_session_info(video_path):
    """
    Generate analysis session information
    
    Args:
        video_path (str): Path to video file
        
    Returns:
        dict: Session information
    """
    video_name = get_video_name_from_path(video_path)
    timestamp = datetime.now()
    
    return {
        "video_name": video_name,
        "session_id": f"{video_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}",
        "timestamp": timestamp,
        "video_path": video_path
    }


def create_result_summary(structure, session_info, results_created):
    """
    Create a summary file for the analysis session
    
    Args:
        structure (dict): Result directory structure
        session_info (dict): Session information
        results_created (list): List of files created during analysis
    """
    summary_path = os.path.join(structure["base"], "analysis_summary.txt")
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("FLEDERMAUS-ANALYSE ZUSAMMENFASSUNG\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Video-Datei: {os.path.basename(session_info['video_path']) if session_info['video_path'] else 'Unbekannt'}\n")
        f.write(f"Ordner-Name: {structure['video_name']}\n")
        f.write(f"Analysiert am: {session_info['timestamp'].strftime('%d.%m.%Y um %H:%M:%S')}\n")
        if session_info['video_path']:
            f.write(f"Video-Pfad: {session_info['video_path']}\n")
        f.write("\n")
        
        f.write("ERSTELLE DATEIEN:\n")
        f.write("-" * 30 + "\n")
        
        for file_path in results_created:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                f.write(f"✓ {filename} ({file_size:,} bytes)\n")
            else:
                filename = os.path.basename(file_path) if file_path else "unbekannte Datei"
                f.write(f"✗ {filename} (nicht gefunden)\n")
        
        f.write(f"\nInsgesamt {len(results_created)} Dateien erstellt.\n")
        f.write(f"Alle Ergebnisse gespeichert in: {structure['base']}\n")
    
    return summary_path
