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