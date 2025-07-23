import cv2

def format_time(seconds):
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02}:{secs:02}"

def is_inside_roi(bat_center, roi):
    if not bat_center or not roi:
        return False
    x, y, w, h = roi
    cx, cy = bat_center
    return x <= cx <= x + w and y <= cy <= y + h


def validate_event(video_path, start_frame, end_frame, roi=None, bat_center=None):
    """
    Validiert ein Ereignis durch Video-Playback mit Interaktion.

    Steuerung während der Wiedergabe:
    - Leertaste: Pause / Weiter
    - Ziffern 1-5: Geschwindigkeit (1x bis 5x)
    - R: Zurück zum Start-Frame
    - Y: Ereignis bestätigen
    - N: Ereignis ablehnen
    - Q / ESC: Wiedergabe beenden

    Args:
        video_path (str): Pfad zum Video.
        start_frame (int): Start-Frame der Wiedergabe.
        end_frame (int): End-Frame der Wiedergabe.
        roi (tuple): Rechteck (x, y, w, h) für Bereichsmarkierung (optional).
        bat_center (tuple): Position der Fledermaus (x, y) (optional).

    Returns:
        bool: True wenn bestätigt, False wenn abgelehnt oder abgebrochen.
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    paused = False
    current_frame = start_frame
    playback_speed = 1.0
    
    while current_frame <= end_frame and cap.isOpened():
        if not paused:
            ret, frame = cap.read()
            if not ret:
                break
            current_frame += 1
        
        # Zeit- und Frame-Anzeige
        timestamp = current_frame / fps
        time_str = f"{int(timestamp // 60):02}:{int(timestamp % 60):02}"
        cv2.putText(frame, f"Zeit: {time_str} (Frame: {current_frame})", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # ROI zeichnen, falls definiert
        if roi:
            x, y, w, h = roi
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 0), 2)
        
        # Fledermausposition markieren (Farbe je nach Position)
        if bat_center:
            color = (0, 0, 255) if is_inside_roi(bat_center, roi) else (200, 200, 200)
            cv2.circle(frame, bat_center, 10, color, 2)
        
        # Bedienhinweise übersichtlich anzeigen
        controls = [
            "Steuerung:",
            "[SPACE] Pause / Weiter",
            "[1-5] Geschwindigkeit (1x - 5x)",
            "[R] Zurücksetzen",
            "[Y] Bestätigen   [N] Ablehnen",
            "[Q/ESC] Beenden"
        ]
        for i, text in enumerate(controls):
            cv2.putText(frame, text, (10, 60 + i*25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        cv2.imshow('Ereignisvalidierung', frame)
        
        key = cv2.waitKey(int(1000 / (fps * playback_speed))) & 0xFF
        
        if key == ord(' ') or key == 32:  # Leertaste: Pause/Weiter
            paused = not paused
        elif key in (ord('q'), 27):  # Q oder ESC: Beenden
            break
        elif key == ord('y'):  # Bestätigen
            cap.release()
            cv2.destroyAllWindows()
            return True
        elif key == ord('n'):  # Ablehnen
            cap.release()
            cv2.destroyAllWindows()
            return False
        elif ord('1') <= key <= ord('5'):  # Geschwindigkeit anpassen
            playback_speed = key - ord('0')
        elif key == ord('r'):  # Zurück zum Anfang
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            current_frame = start_frame
            paused = False
    
    cap.release()
    cv2.destroyAllWindows()
    return False