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




def export_events_to_csv(events, video_path, csv_path):
    # Parse video start time from filename (adjust if you have better method)
    start_time = parse_start_time_from_filename(video_path)
    video_id = os.path.splitext(os.path.basename(video_path))[0]

    with open(csv_path, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Video", "Startzeit Video", "Zeit", "Uhrzeit"])

        for event in events:
            elapsed_seconds = event.get("entry", 0)
            zeit_str = seconds_to_hhmmss(elapsed_seconds)
            today = datetime.today()
            start_datetime = datetime.combine(today, start_time)
            event_datetime = start_datetime + timedelta(seconds=elapsed_seconds)
            uhrzeit_str = event_datetime.strftime("%H:%M:%S")

            writer.writerow([video_id, start_time.strftime("%H:%M:%S"), zeit_str, uhrzeit_str])

    print(f"Exported {len(events)} events to {csv_path}")
    
    
def export_results(self):
    if not self.events:
        messagebox.showinfo("Export Results", "No events to export.")
        return

    video_name = os.path.splitext(os.path.basename(self.video_path))[0]
    current_datetime = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')
    current_user = getpass.getuser()
    csv_filename = f"{video_name}_{current_datetime}_{current_user}.csv"
    csv_path = os.path.join(os.path.dirname(self.video_path), csv_filename)

    export_events_to_csv(self.events, self.video_path, csv_path)
    messagebox.showinfo("Export Results", f"Events exported successfully to:\n{csv_path}")