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



from datetime import datetime, timezone
import os
import cv2

def export_video(frames, fps, source_video_path, username=None):
    """
    Exportiert markierte Frames als Video
    
    Args:
        frames: Liste der zu exportierenden Frames
        fps: Bilder pro Sekunde
        source_video_path: Pfad zum Quellvideo
        username: Optionaler Benutzername für Videometadaten
    """
    if not frames:
        return False
        
    # Wenn kein Benutzername angegeben ist, versuche System-Benutzernamen zu bekommen
    if username is None:
        try:
            import getpass
            username = getpass.getuser()
        except:
            username = "unbekannt"
            
    # Aktuelles Datum und Uhrzeit im UTC-Format
    current_datetime = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')
    
    # Ausgabeordner "exports" im Verzeichnis des Quellvideos anlegen, falls nicht vorhanden
    output_dir = os.path.join(os.path.dirname(source_video_path), "exports")
    os.makedirs(output_dir, exist_ok=True)
    
    # Ausgabedateiname mit Basisnamen, Zeitstempel und Benutzername
    base_name = os.path.splitext(os.path.basename(source_video_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}_marked_{current_datetime}_{username}.avi")
    
    # Framegröße bestimmen
    height, width = frames[0].shape[:2]
    
    # VideoWriter initialisieren (XVID-Codec)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Alle Frames in das Video schreiben
    for frame in frames:
        out.write(frame)
        
    # Ressourcen freigeben
    out.release()
    
    print(f"[INFO] Markiertes Video exportiert nach: {output_path}")
    return output_path
