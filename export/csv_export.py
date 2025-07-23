import csv
from tkinter import filedialog, messagebox
from datetime import datetime, timedelta, timezone
import os

def export_csv(events):
    file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                         filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return
    try:
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Entry (s)', 'Exit (s)', 'Duration (s)'])
            for event in events:
                writer.writerow([round(event["entry"], 2),
                               round(event["exit"] or 0, 2),
                               round(event["duration"] or 0, 2)])
        messagebox.showinfo("Export CSV", f"Exported events to {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export CSV: {str(e)}")
        
        
        

def seconds_to_hhmmss(seconds):
    # Format seconds into HH:MM:SS (or MM:SS if < 1 hour)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h:02}:{m:02}:{s:02}"
    else:
        return f"{m:02}:{s:02}"


def parse_start_time_from_filename(filename):
    base = os.path.basename(filename)
    parts = base.split('_')
    if len(parts) >= 3:
        time_str = parts[2]  # '215828'
        if len(time_str) == 6:
            return datetime.strptime(time_str, "%H%M%S").time()
    # fallback
    return datetime.strptime("00:00:00", "%H:%M:%S").time()