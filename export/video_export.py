import cv2
from tkinter import messagebox, filedialog
from datetime import datetime
import os

# Mit ROI
def export_video(frames, fps, original_video_path):
    if not frames:
        messagebox.showinfo("Video exportieren", "Keine Bilder zum Exportieren vorhanden.")
        return

    folder_path = filedialog.askdirectory(title="Ordner zum Speichern des Videos auswählen")
    if not folder_path:
        messagebox.showinfo("Export abgebrochen", "Kein Ordner ausgewählt.")
        return

    # Ursprünglichen Videonamen ohne Erweiterung extrahieren
    base_name = os.path.splitext(os.path.basename(original_video_path))[0]

    # Heutiges Datum im Format Tag-Monat-Jahr
    today_str = datetime.now().strftime("%d-%m-%Y")

    # Neuen Dateinamen mit Datum erstellen
    filename = f"{base_name}_{today_str}.avi"
    output_path = os.path.join(folder_path, filename)

    height, width = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for frame in frames:
        writer.write(frame)
    writer.release()

    messagebox.showinfo("Export abgeschlossen", f"Video wurde gespeichert unter:\n{output_path}")
