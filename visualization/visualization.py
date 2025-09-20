import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import logging
import cv2
import math

# Configure matplotlib for UTF-8 and Unicode support
import matplotlib
matplotlib.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'sans-serif']

logger = logging.getLogger(__name__)

def create_flight_path_visualization(flight_path_data, video_path, title="Flugwege"):
    """
    Create flight path visualization from validation session data
    
    Args:
        flight_path_data (list): List of flight path records from validation session
        video_path (str): Path to the video file
        title (str): Title for the visualization
        
    Returns:
        str: Path to saved visualization or None if failed
    """
    if not flight_path_data:
        logger.warning("No flight path data provided")
        return None
        
    try:
        # Get video dimensions
        cap = cv2.VideoCapture(video_path)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        
        # Set up plot with video dimensions
        plt.xlim(0, frame_width)
        plt.ylim(frame_height, 0)  # Invert Y axis to match video coordinates
        plt.xlabel('X Position (pixels)')
        plt.ylabel('Y Position (pixels)')
        plt.title(title)
        plt.grid(True, alpha=0.3)
        
        # Process flight path data
        colors = plt.cm.tab10(np.linspace(0, 1, max(10, len(flight_path_data))))
        
        for i, path_record in enumerate(flight_path_data):
            if 'positions' not in path_record or not path_record['positions']:
                continue
                
            positions = path_record['positions']
            color = colors[i % len(colors)]
            
            # Extract x, y coordinates
            x_coords = [pos[0] for pos in positions]
            y_coords = [pos[1] for pos in positions]
            
            # Plot flight path
            plt.plot(x_coords, y_coords, color=color, linewidth=2, alpha=0.7, 
                    label=f"Ereignis {path_record.get('event_id', i+1)}")
            
            # Mark start and end points
            if len(positions) > 0:
                plt.scatter(x_coords[0], y_coords[0], color=color, s=100, marker='o', 
                          edgecolors='black', linewidth=2, label=f"Start {i+1}")
                plt.scatter(x_coords[-1], y_coords[-1], color=color, s=100, marker='s', 
                          edgecolors='black', linewidth=2, label=f"Ende {i+1}")
        
        # Add legend
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
        # Save visualization
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_basename = os.path.splitext(os.path.basename(video_path))[0]
        filename = f"flugwege_{video_basename}_{timestamp}.png"
        
        # Create output directory
        output_dir = os.path.join(os.path.dirname(video_path), 'results', 'visualizations', 'flight_paths')
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight', format='png')
        plt.close()
        
        logger.info(f"Flight path visualization saved to: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating flight path visualization: {str(e)}")
        return None


def create_radar_style_visualization(flight_path_data, video_path, title="Fledermaus-Radar"):
    """
    Create a radar-style flight path visualization similar to air traffic control displays
    
    Args:
        flight_path_data (list): List of flight path records from validation session
        video_path (str): Path to the video file
        title (str): Title for the visualization
        
    Returns:
        str: Path to saved visualization or None if failed
    """
    if not flight_path_data:
        logger.warning("No flight path data provided for radar visualization")
        return None
        
    try:
        # Get video dimensions
        cap = cv2.VideoCapture(video_path)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        
        # Create radar-style visualization
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(14, 10))
        fig.patch.set_facecolor('black')
        
        # Set up radar-style plot
        ax.set_xlim(0, frame_width)
        ax.set_ylim(frame_height, 0)  # Invert Y axis to match video coordinates
        ax.set_facecolor('black')
        
        # Add radar-style grid
        grid_spacing_x = frame_width // 10
        grid_spacing_y = frame_height // 10
        
        for x in range(0, frame_width + 1, grid_spacing_x):
            ax.axvline(x, color='green', alpha=0.3, linewidth=0.5)
        for y in range(0, frame_height + 1, grid_spacing_y):
            ax.axhline(y, color='green', alpha=0.3, linewidth=0.5)
        
        # Create radar-style coordinate markers
        for x in range(0, frame_width + 1, grid_spacing_x * 2):
            for y in range(0, frame_height + 1, grid_spacing_y * 2):
                ax.plot(x, y, '+', color='lime', markersize=4, alpha=0.6)
        
        # Color schemes for different bats (radar-style colors)
        radar_colors = ['#00FF00', '#FF4500', '#00BFFF', '#FFD700', '#FF69B4', 
                       '#00CED1', '#FF6347', '#98FB98', '#DDA0DD', '#F0E68C']
        
        bat_trails = []  # Store trail positions for fade effect
        
        # Process each flight path
        for i, path_record in enumerate(flight_path_data):
            if 'positions' not in path_record or not path_record['positions']:
                continue
                
            positions = path_record['positions']
            color = radar_colors[i % len(radar_colors)]
            
            # Extract coordinates
            x_coords = [pos[0] for pos in positions]
            y_coords = [pos[1] for pos in positions]
            
            if len(positions) < 2:
                continue
            
            # Create trail effect (fade from current position backwards)
            trail_length = min(20, len(positions))  # Show last 20 positions
            
            for j in range(len(positions) - trail_length, len(positions)):
                if j < 0:
                    continue
                    
                alpha = (j - (len(positions) - trail_length)) / trail_length
                alpha = max(0.1, alpha)  # Minimum visibility
                
                if j < len(positions) - 1:
                    # Draw trail segments
                    ax.plot([x_coords[j], x_coords[j+1]], [y_coords[j], y_coords[j+1]], 
                           color=color, alpha=alpha, linewidth=2)
            
            # Current position (brightest)
            current_x, current_y = positions[-1]
            
            # Create radar blip effect
            circle1 = plt.Circle((current_x, current_y), 8, color=color, alpha=0.9, fill=True)
            circle2 = plt.Circle((current_x, current_y), 15, color=color, alpha=0.4, fill=False, linewidth=2)
            circle3 = plt.Circle((current_x, current_y), 25, color=color, alpha=0.2, fill=False, linewidth=1)
            
            ax.add_patch(circle1)
            ax.add_patch(circle2)
            ax.add_patch(circle3)
            
            # Add bat ID label
            ax.annotate(f'BAT-{i+1:02d}', 
                       (current_x + 30, current_y - 10),
                       color=color, fontsize=10, fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.7))
            
            # Add movement vector (direction arrow)
            if len(positions) >= 2:
                prev_pos = positions[-2]
                dx = current_x - prev_pos[0]
                dy = current_y - prev_pos[1]
                
                # Only show arrow if there's significant movement
                if math.sqrt(dx*dx + dy*dy) > 5:
                    ax.arrow(current_x, current_y, dx*3, dy*3, 
                           head_width=8, head_length=10, fc=color, ec=color, alpha=0.8)
        
        # Radar-style title and labels
        ax.set_title(title, color='lime', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('X Position (pixels)', color='white', fontsize=12)
        ax.set_ylabel('Y Position (pixels)', color='white', fontsize=12)
        
        # Add timestamp
        timestamp_text = f"Scan Time: {datetime.now().strftime('%H:%M:%S')}"
        ax.text(0.02, 0.98, timestamp_text, transform=ax.transAxes, 
               color='lime', fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.8))
        
        # Add detection statistics
        stats_text = f"Contacts: {len(flight_path_data)}\nActive Tracks: {len(flight_path_data)}"
        ax.text(0.98, 0.98, stats_text, transform=ax.transAxes, 
               color='white', fontsize=10, verticalalignment='top', horizontalalignment='right',
               bbox=dict(boxstyle="round,pad=0.5", facecolor='darkgreen', alpha=0.8))
        
        # Customize ticks for radar appearance
        ax.tick_params(colors='white', which='both')
        
        # Save radar visualization
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_basename = os.path.splitext(os.path.basename(video_path))[0]
        filename = f"fledermaus_radar_{video_basename}_{timestamp}.png"
        
        # Create output directory
        output_dir = os.path.join(os.path.dirname(video_path), 'results', 'visualizations', 'radar_display')
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='black')
        plt.close()
        
        # Reset style to default
        plt.style.use('default')
        
        logger.info(f"Radar-style visualization saved to: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating radar-style visualization: {str(e)}")
        # Reset style on error
        plt.style.use('default')
        return None


def create_enhanced_flight_display(flight_path_data, video_path, title="Enhanced Flight Display"):
    """
    Create an enhanced flight path display with multiple visualization options
    
    Args:
        flight_path_data (list): List of flight path records
        video_path (str): Path to the video file
        title (str): Title for the visualization
        
    Returns:
        tuple: (standard_path, radar_path) - paths to both visualizations
    """
    standard_path = create_flight_path_visualization(flight_path_data, video_path, title)
    radar_path = create_radar_style_visualization(flight_path_data, video_path, title + " - Radar View")
    
    return standard_path, radar_path

def add_time_to_bat_paths(bat_paths, fps):
    """
    Convert bat paths from [(x,y), ...] to [(time, x, y), ...]
    assuming each point is one frame apart.
    
    Args:
        bat_paths (dict): keys=bat_id, values=list of (x,y) tuples
        fps (float): frames per second of the video
    
    Returns:
        dict: keys=bat_id, values=list of (time, x, y) tuples
    """
    bat_paths_with_time = {}
    for bat_id, positions in bat_paths.items():
        bat_paths_with_time[bat_id] = [(i / fps, pos[0], pos[1]) for i, pos in enumerate(positions)]
    return bat_paths_with_time






def export_flightMap(bat_paths, output_dir, filename_base=None, user="IfAÖ", fps=30, total_frames=None):
    if not bat_paths:
        print("Keine Fledermausrouten zum Visualisieren vorhanden.")
        return None

    os.makedirs(output_dir, exist_ok=True)
    plt.figure(figsize=(10, 8))

    for bat_id, path in bat_paths.items():
        if not path or len(path) < 2:
            continue

        path_array = np.array(path)
        times = path_array[:, 0]
        x = path_array[:, 1]
        y = path_array[:, 2]

        plt.plot(x, y, label=f"Fledermaus {bat_id}")
        plt.scatter(x[0], y[0], color='green', s=100, marker='*')  # Start
        plt.scatter(x[-1], y[-1], color='red', s=100, marker='*')  # Ende

    plt.title("Flugkarten der Fledermäuse")
    plt.xlabel("X Position")
    plt.ylabel("Y Position")
    plt.legend()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    plt.figtext(0.01, 0.01, f"Datum: {timestamp} | Benutzer: {user}", fontsize=8, color='gray')

    out_filename = f"{filename_base}_flugkarte.png" if filename_base else "flugkarte.png"
    out_path = os.path.join(output_dir, out_filename)
    plt.savefig(out_path)
    plt.close()

    print(f"[INFO] Flugkarte gespeichert unter: {out_path}")

    # Internally call plot_activity_timelin
    _plot_activity_timeline_internal(
        bat_paths=bat_paths,
        output_dir=output_dir,
        total_frames=total_frames,
        fps=fps,
        filename_base=filename_base,
        user=user
    )

    return out_path


def _plot_activity_timeline_internal(bat_paths, output_dir, total_frames=None, fps=15, filename_base="video", user="IfAÖ"):
    from collections import defaultdict

    activity = defaultdict(int)
    for bat_id, path in bat_paths.items():
        for (t, x, y) in path:
            sec = int(t)
            activity[sec] += 1

    duration_sec = int(total_frames / fps) if total_frames else max(activity.keys()) + 1
    time_axis = np.arange(duration_sec)
    values = [activity.get(t, 0) for t in time_axis]

    plt.figure(figsize=(12, 2.5))
    plt.fill_between(time_axis, values, step="pre", alpha=0.5, color='blue')
    plt.plot(time_axis, values, color='black', linewidth=1.2)

    plt.title("Bataktivität im Videoverlauf")
    plt.xlabel("Zeit (Sekunden)")
    plt.ylabel("Anzahl der aktiven Fledermäuse")
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    plt.figtext(0.01, 0.01, f"Datum: {timestamp} | Benutzer: {user}", fontsize=8, color="gray")

    filename = f"{filename_base}_activity_timeline.png"
    output_path = os.path.join(output_dir, filename)
    plt.savefig(output_path)
    plt.close()

    print(f"[INFO] Aktivitätsdiagramm gespeichert unter: {output_path}")





def export_flightMap(bat_paths_with_time, output_dir, filename_base=None, user=None, fps=30, total_frames=None):
    """
    Enhanced flight map export with better visualization
    
    Args:
        bat_paths_with_time: Dictionary of bat paths with timestamps
        output_dir: Directory to save the output
        filename_base: Base name for the output file
        user: Username to include in the metadata
        fps: Frames per second of the video
        total_frames: Total frames in video
    """
    if not bat_paths_with_time:
        print("Keine Fledermausrouten zum Visualisieren vorhanden.")
        return None
        
    # If user not provided, try to get system username
    if user is None:
        try:
            import getpass
            user = getpass.getuser()
        except:
            user = "IfAÖ"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Create enhanced visualization
    fig, ((ax_main, ax_timeline), (ax_stats, ax_empty)) = plt.subplots(2, 2, figsize=(16, 12),
                                                                       gridspec_kw={'height_ratios': [3, 1],
                                                                                   'width_ratios': [3, 1],
                                                                                   'hspace': 0.3, 'wspace': 0.3})
    
    # Hide the empty subplot
    ax_empty.axis('off')
    
    # Color palette for different bats
    colors = plt.cm.Set3(np.linspace(0, 1, max(10, len(bat_paths_with_time))))
    
    # Track statistics
    total_paths = 0
    max_duration = 0
    
    for bat_id, path in bat_paths_with_time.items():
        if not path or len(path) < 2:
            continue

        path_array = np.array(path)
        if path_array.shape[1] >= 3:  # Ensure we have time, x, y data
            times = path_array[:, 0]
            x = path_array[:, 1]
            y = path_array[:, 2]
            
            duration = times[-1] - times[0] if len(times) > 1 else 0
            max_duration = max(max_duration, duration)
            
            color = colors[total_paths % len(colors)]
            
            # Plot flight path
            ax_main.plot(x, y, color=color, linewidth=3, alpha=0.8, 
                        label=f'{bat_id} ({duration:.1f}s)')
            
            # Mark start and end points
            ax_main.scatter(x[0], y[0], color=color, s=150, marker='o', 
                          edgecolors='black', linewidth=2, zorder=5, label=f'Start {bat_id}')
            ax_main.scatter(x[-1], y[-1], color=color, s=150, marker='s', 
                          edgecolors='black', linewidth=2, zorder=5, label=f'Ende {bat_id}')
            
            # Add direction arrows
            if len(x) > 5:
                for i in range(2, len(x)-2, max(1, len(x)//8)):
                    dx = x[i+1] - x[i-1]
                    dy = y[i+1] - y[i-1]
                    if dx != 0 or dy != 0:
                        ax_main.annotate('', xy=(x[i], y[i]), 
                                       xytext=(x[i]-dx*0.05, y[i]-dy*0.05),
                                       arrowprops=dict(arrowstyle='->', 
                                                     color=color, lw=2, alpha=0.8))
            
            total_paths += 1
    
    # Customize main plot
    ax_main.set_xlabel('X Position (Pixel)', fontsize=14, fontweight='bold')
    ax_main.set_ylabel('Y Position (Pixel)', fontsize=14, fontweight='bold')
    ax_main.set_title(f'Fledermaus-Flugwege - {filename_base or "Analyse"}', 
                     fontsize=18, fontweight='bold', pad=20)
    ax_main.grid(True, alpha=0.3, linestyle='--')
    ax_main.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=11)
    ax_main.invert_yaxis()  # Match video coordinates
    
    # Timeline subplot
    y_pos = 0
    for bat_id, path in bat_paths_with_time.items():
        if not path or len(path) < 2:
            continue
            
        path_array = np.array(path)
        if path_array.shape[1] >= 3:
            times = path_array[:, 0]
            start_time = times[0]
            end_time = times[-1]
            
            color = colors[y_pos % len(colors)]
            ax_timeline.barh(y_pos, end_time - start_time, left=start_time, 
                           height=0.6, color=color, alpha=0.7)
            ax_timeline.text(start_time + (end_time - start_time)/2, y_pos, 
                           f'{bat_id}', ha='center', va='center', fontsize=10, fontweight='bold')
            y_pos += 1
    
    ax_timeline.set_xlabel('Zeit (Sekunden)', fontsize=12, fontweight='bold')
    ax_timeline.set_ylabel('Fledermaus ID', fontsize=12, fontweight='bold')
    ax_timeline.set_title('Zeitlicher Verlauf', fontsize=14, fontweight='bold')
    ax_timeline.grid(True, alpha=0.3, axis='x')
    
    # Statistics
    ax_stats.axis('off')
    stats_text = f"""
ANALYSE-ZUSAMMENFASSUNG
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Anzahl erkannter Fledermäuse: {total_paths}
Längste Flugzeit: {max_duration:.1f} Sekunden
Bearbeiter: {user}
Erstellt am: {datetime.now().strftime("%d.%m.%Y um %H:%M:%S")}
Video-FPS: {fps:.1f}
"""
    
    ax_stats.text(0.05, 0.95, stats_text, transform=ax_stats.transAxes, 
                 fontsize=12, verticalalignment='top', fontfamily='monospace',
                 bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
    
    # Save with timestamp
    current_datetime = datetime.now().strftime('%Y%m%d_%H%M%S')
    if filename_base:
        output_path = os.path.join(output_dir, f"{filename_base}_flugkarte_{current_datetime}.png")
    else:
        output_path = os.path.join(output_dir, f"flugkarte_{current_datetime}.png")
    
    try:
        # Save with UTF-8 support and proper encoding
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none',
                   format='png')  # Explicitly specify PNG format
        plt.close()
        
        print(f"✅ Flugkarte erfolgreich gespeichert: {output_path}")
        
        # Call activity timeline function
        _plot_activity_timeline_internal(
            bat_paths=bat_paths_with_time,
            output_dir=output_dir,
            total_frames=total_frames,
            fps=fps,
            filename_base=filename_base,
            user=user
        )
        
        return output_path
        
    except Exception as e:
        print(f"❌ Fehler beim Speichern der Flugkarte: {str(e)}")
        plt.close()
        return None
    