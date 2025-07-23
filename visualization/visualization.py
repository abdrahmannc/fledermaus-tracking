from collections import defaultdict
from fileinput import filename
import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timezone
import logging


logger = logging.getLogger(__name__)

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





def export_flightMap(bat_paths_with_time, output_dir, filename_base=None, user=None):
    """
    Export flight map visualization
    
    Args:
        bat_paths_with_time: Dictionary of bat paths with timestamps
        output_dir: Directory to save the output
        filename_base: Base name for the output file
        user: Username to include in the metadata
    """
    # If user not provided, try to get system username
    if user is None:
        try:
            import getpass
            user = getpass.getuser()
        except:
            user = "unknown"
            
    # Rest of the function...
    # Make sure to include the user in the output filename
    current_datetime = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')
    if filename_base:
        output_path = os.path.join(output_dir, f"{filename_base}_flightmap_{current_datetime}_{user}.png")
    else:
        output_path = os.path.join(output_dir, f"flightmap_{current_datetime}_{user}.png")
    