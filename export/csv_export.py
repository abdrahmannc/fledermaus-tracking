import csv
from tkinter import filedialog, messagebox
from datetime import datetime, timedelta, timezone
import os
import getpass

def safe_float(value, default=0.0):
    """Safely convert value to float, handling None and non-numeric types"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_duration_calculation(entry_time, exit_time):
    """Safely calculate duration from entry and exit times"""
    entry = safe_float(entry_time)
    exit = safe_float(exit_time)
    
    # If either time is invalid (converted to 0.0 from None), return 0
    if entry_time is None or exit_time is None:
        return 0.0
    
    return max(0.0, exit - entry)  # Ensure non-negative duration

def seconds_to_hhmmss(seconds):
    """Convert seconds to HH:MM:SS or MM:SS format with safe handling"""
    if seconds is None:
        return "unbekannt"
    try:
        seconds = float(seconds)
        if seconds < 0:
            return "unbekannt"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        # Return HH:MM:SS if hours > 0, otherwise MM:SS
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    except (ValueError, TypeError):
        return "unbekannt"

def export_csv(events, video_path=None, roi_data=None, polygon_data=None, user_choice=None):
    """
    Enhanced CSV export with comprehensive bat detection data
    Exports to per-video folder as part of consolidated workflow
    
    Args:
        events (list): Detection events with timestamps and durations
        video_path (str): Path to analyzed video file
        roi_data (dict): ROI information if used
        polygon_data (list): Polygon areas if used
        user_choice (str): User folder choice for organization
    """
    try:
        # Import result organization utilities
        from utils.result_organizer import create_video_result_structure, get_analysis_session_info, get_standardized_filename, create_result_summary
        
        # Create structured result directories with user choice
        structure = create_video_result_structure(video_path, user_choice=user_choice)
        session_info = get_analysis_session_info(video_path)
        
        # Generate filename using standardized naming
        filename = get_standardized_filename("detections", structure["video_name"])
        file_path = os.path.join(structure["base"], filename)
        
        print(f"[INFO] Exporting CSV to per-video folder: {file_path}")
    
    except Exception as e:
        print(f"[WARNING] Could not use structured export, falling back: {e}")
        # Fallback to old method if structure creation fails
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="CSV-Export speichern"
        )
        if not file_path:
            return None
    
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header with metadata
            writer.writerow(['# Fledermaus-Erkennungsbericht - CSV Export'])
            writer.writerow(['# Erstellt am:', datetime.now().strftime("%d.%m.%Y %H:%M:%S")])
            writer.writerow(['# Software:', 'Fledermaus-Detektor Pro v2.0'])
            writer.writerow(['# Benutzer:', getpass.getuser()])
            
            if video_path:
                writer.writerow(['# Video-Datei:', os.path.basename(video_path)])
                writer.writerow(['# Video-Pfad:', video_path])
            
            # Detection method information
            detection_method = "Gesamtes Video"
            if roi_data:
                detection_method = f"ROI ({roi_data.get('x', 0)}, {roi_data.get('y', 0)}, {roi_data.get('width', 0)}, {roi_data.get('height', 0)})"
            elif polygon_data and len(polygon_data) > 0:
                detection_method = f"Polygon-Bereiche ({len(polygon_data)} Bereiche)"
            
            writer.writerow(['# Erkennungsmethode:', detection_method])
            writer.writerow(['# Anzahl Erkennungen:', len(events)])
            
            # Calculate statistics with safe type handling
            if events:
                # Use safe_float to handle None and non-numeric values
                durations = [safe_float(event.get('duration')) for event in events]
                valid_durations = [d for d in durations if d > 0]  # Filter out zero/invalid durations
                
                total_duration = sum(valid_durations)
                avg_duration = total_duration / len(valid_durations) if valid_durations else 0
                min_duration = min(valid_durations) if valid_durations else 0
                max_duration = max(valid_durations) if valid_durations else 0
                
                writer.writerow(['# Gesamte Aktivitätsdauer (s):', f"{total_duration:.2f}"])
                writer.writerow(['# Durchschnittliche Dauer (s):', f"{avg_duration:.2f}"])
                writer.writerow(['# Minimale Dauer (s):', f"{min_duration:.2f}"])
                writer.writerow(['# Maximale Dauer (s):', f"{max_duration:.2f}"])
            
            writer.writerow([])  # Empty row separator
            
            # Enhanced column headers
            headers = [
                'Ereignis_Nr',
                'Einflugzeit_Sekunden', 
                'Ausflugzeit_Sekunden', 
                'Dauer_Sekunden',
                'Einflugzeit_Formatiert',
                'Ausflugzeit_Formatiert',
                'Dauer_Formatiert',
                'Validiert',
                'Validierungsentscheidung',
                'Validierungszeitpunkt',
                'Bemerkungen'
            ]
            writer.writerow(headers)
            
            # Write event data with safe type conversion
            for i, event in enumerate(events, 1):
                # Safe conversion of timing data with enhanced entry/exit handling
                entry_time = event.get('entry') or event.get('einflugzeit')
                exit_time = event.get('exit') or event.get('ausflugzeit')
                duration = event.get('duration') or event.get('dauer')
                
                # Apply safe conversion
                entry_time = safe_float(entry_time) if entry_time is not None else None
                exit_time = safe_float(exit_time) if exit_time is not None else None
                duration = safe_float(duration) if duration is not None else None
                
                # If duration is missing or invalid, calculate from entry/exit
                if (duration is None or duration <= 0) and entry_time is not None and exit_time is not None:
                    duration = safe_duration_calculation(entry_time, exit_time)
                
                validated = 'Ja' if event.get('validated', False) else 'Nein'
                validation_decision = event.get('validation_decision', 'unvalidiert')
                validation_timestamp = event.get('validation_timestamp', '')
                remarks = str(event.get('remarks', ''))  # Ensure string type
                
                # Add indicator for incomplete events
                if event.get('incomplete', False):
                    if not remarks:
                        remarks = "Ereignis unvollständig"
                    else:
                        remarks += " [unvollständig]"
                
                # Format times with placeholder handling
                if entry_time is not None:
                    entry_formatted = seconds_to_hhmmss(entry_time)
                    entry_seconds = f"{entry_time:.2f}"
                else:
                    entry_formatted = "unbekannt"
                    entry_seconds = "unbekannt"
                
                if exit_time is not None:
                    exit_formatted = seconds_to_hhmmss(exit_time)
                    exit_seconds = f"{exit_time:.2f}"
                else:
                    exit_formatted = "unbekannt"
                    exit_seconds = "unbekannt"
                
                if duration is not None and duration > 0:
                    duration_formatted = seconds_to_hhmmss(duration)
                    duration_seconds = f"{duration:.2f}"
                else:
                    duration_formatted = "unbekannt"
                    duration_seconds = "unbekannt"
                
                writer.writerow([
                    i,                           # Event number
                    entry_seconds,               # Entry time in seconds
                    exit_seconds,                # Exit time in seconds  
                    duration_seconds,            # Duration in seconds
                    entry_formatted,             # Entry time formatted
                    exit_formatted,              # Exit time formatted
                    duration_formatted,          # Duration formatted
                    validated,                   # Validation status
                    validation_decision,         # Validation decision (approved/rejected/unvalidiert)
                    validation_timestamp,        # Validation timestamp
                    remarks                      # Additional remarks
                ])
        
        # Create session summary and capture event points if structured organization is available
        try:
            if 'structure' in locals() and 'session_info' in locals():
                # Capture event points for fast replay
                from validation.persistent_validator import EventPointCapture
                event_capture = EventPointCapture(video_path)
                event_capture.capture_event_points(events)
                
                results_created = {
                    'csv_detections': os.path.basename(file_path),
                    'event_points': 'event_points.json',
                    'total_events': len(events)
                }
                summary_path = create_result_summary(structure, session_info, results_created)
                messagebox.showinfo("CSV Export", 
                              f"CSV-Daten und Ereignispunkte erstellt:\n{structure['base']}\n\n"
                              f"Anzahl Ereignisse: {len(events)}")
            else:
                messagebox.showinfo("CSV Export", 
                              f"Erkennungsdaten erfolgreich exportiert:\n{file_path}\n\n"
                              f"Anzahl Ereignisse: {len(events)}")
        except Exception as e:
            print(f"[WARNING] Could not create summary or event points: {e}")
            messagebox.showinfo("CSV Export", 
                          f"Erkennungsdaten erfolgreich exportiert:\n{file_path}\n\n"
                          f"Anzahl Ereignisse: {len(events)}")
        
        return file_path
        
    except Exception as e:
        messagebox.showerror("Export-Fehler", f"Fehler beim CSV-Export: {str(e)}")
        return None


def export_enhanced_csv(events, video_path=None, roi_data=None, polygon_data=None, 
                       flight_paths=None, session_info=None, user_choice=None):
    """
    Export comprehensive CSV with flight path data and enhanced analysis
    
    Args:
        events (list): Detection events
        video_path (str): Video file path
        roi_data (dict): ROI information
        polygon_data (list): Polygon data
        flight_paths (list): Flight path data
        session_info (dict): Session information
        user_choice (str): User folder choice for organization
    """
    try:
        # Use structured output if user choice provided
        if user_choice:
            from utils.result_organizer import create_video_result_structure, get_standardized_filename
            structure = create_video_result_structure(video_path, user_choice=user_choice)
            filename = get_standardized_filename("enhanced_detections", structure["video_name"])
            file_path = os.path.join(structure["base"], filename)
        else:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="Erweiterten CSV-Export speichern"
            )
            if not file_path:
                return
    except Exception as e:
        print(f"[WARNING] Could not use structured export: {e}")
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Erweiterten CSV-Export speichern"
        )
        if not file_path:
            return
    
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Enhanced header with session info
            writer.writerow(['# Erweiteter Fledermaus-Erkennungsbericht'])
            writer.writerow(['# Erstellt:', datetime.now().strftime("%d.%m.%Y %H:%M:%S")])
            
            if session_info:
                writer.writerow(['# Sitzung:', session_info.get('session_id', 'Unbekannt')])
                writer.writerow(['# Aufnahmeort:', session_info.get('location', 'Nicht angegeben')])
                writer.writerow(['# Beobachter:', session_info.get('observer', 'Nicht angegeben')])
            
            writer.writerow([])
            
            # Events section
            writer.writerow(['=== ERKENNUNGSEREIGNISSE ==='])
            headers = [
                'Nr', 'Start_s', 'Ende_s', 'Dauer_s', 'Start_Zeit', 'Ende_Zeit', 
                'Validiert', 'Validierungsentscheidung', 'Flugweg_Punkte', 'Durchschnitt_X', 'Durchschnitt_Y', 'Bemerkungen'
            ]
            writer.writerow(headers)
            
            for i, event in enumerate(events, 1):
                # Get flight path info for this event with safe handling
                flight_info = ""
                avg_x = avg_y = ""
                
                if flight_paths and i <= len(flight_paths):
                    path = flight_paths[i-1]
                    if path and len(path) > 0:
                        flight_info = str(len(path))
                        try:
                            x_coords = [safe_float(p[0]) for p in path if len(p) >= 2]
                            y_coords = [safe_float(p[1]) for p in path if len(p) >= 2]
                            if x_coords and y_coords:
                                avg_x = f"{sum(x_coords)/len(x_coords):.1f}"
                                avg_y = f"{sum(y_coords)/len(y_coords):.1f}"
                        except (IndexError, TypeError, ZeroDivisionError):
                            avg_x = avg_y = ""
                
                # Safe conversion of event timing data
                entry_time = safe_float(event.get('entry'))
                exit_time = safe_float(event.get('exit'))
                duration = safe_float(event.get('duration'))
                
                # Calculate duration if missing
                if duration <= 0 and entry_time >= 0 and exit_time >= 0:
                    duration = safe_duration_calculation(entry_time, exit_time)
                
                writer.writerow([
                    i,
                    f"{entry_time:.2f}",
                    f"{exit_time:.2f}",
                    f"{duration:.2f}",
                    seconds_to_hhmmss(entry_time),
                    seconds_to_hhmmss(exit_time),
                    'Ja' if event.get('validated', False) else 'Nein',
                    event.get('validation_decision', 'unvalidiert'),
                    flight_info,
                    avg_x,
                    avg_y,
                    str(event.get('remarks', ''))  # Ensure string type
                ])
            
            # Technical details section
            writer.writerow([])
            writer.writerow(['=== TECHNISCHE DETAILS ==='])
            writer.writerow(['Parameter', 'Wert'])
            
            if video_path:
                writer.writerow(['Video-Datei', os.path.basename(video_path)])
            
            detection_method = "Gesamtes Video"
            if roi_data:
                detection_method = f"ROI-Bereich"
            elif polygon_data:
                detection_method = f"Polygon-Bereiche ({len(polygon_data)})"
            writer.writerow(['Erkennungsmethode', detection_method])
            
            if events:
                total_duration = sum(safe_float(event.get('duration')) for event in events)
                writer.writerow(['Gesamte Aktivitätsdauer (s)', f"{total_duration:.2f}"])
                if len(events) > 0:
                    avg_duration = total_duration / len(events)
                    writer.writerow(['Durchschnittliche Ereignisdauer (s)', f"{avg_duration:.2f}"])
        
        messagebox.showinfo("Erweiterter CSV Export", 
                          f"Erweiterte Daten erfolgreich exportiert:\n{file_path}")
        
    except Exception as e:
        messagebox.showerror("Export-Fehler", f"Fehler beim erweiterten CSV-Export: {str(e)}")
        
        
        

# Remove duplicate function - using the safe version defined earlier

def parse_start_time_from_filename(filename):
    base = os.path.basename(filename)
    parts = base.split('_')
    if len(parts) >= 3:
        time_str = parts[2]  # '215828'
        if len(time_str) == 6:
            return datetime.strptime(time_str, "%H%M%S").time()
    # fallback
    return datetime.strptime("00:00:00", "%H:%M:%S").time()




def export_events_to_csv(events, video_path, csv_path, polygon_areas=None):
    """
    Export event data to CSV with enhanced polygon support
    
    Args:
        events: List of event dictionaries
        video_path: Path to the source video
        csv_path: Path where CSV will be saved
        polygon_areas: Optional list of polygon areas for reference
    """
    # Parse video start time from filename
    start_time = parse_start_time_from_filename(video_path)
    video_id = os.path.splitext(os.path.basename(video_path))[0]

    with open(csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Enhanced header with polygon information
        headers = [
            "Video", "Startzeit Video", "Zeit", "Uhrzeit", "Eintritt (s)", "Austritt (s)", 
            "Dauer (s)", "Frame Index", "Bat Center X", "Bat Center Y", "Polygon Bereich",
            "ROI X", "ROI Y", "ROI Width", "ROI Height"
        ]
        writer.writerow(headers)

        for event in events:
            # Safe conversion of timing data
            elapsed_seconds = safe_float(event.get("entry"))
            exit_time = safe_float(event.get("exit"))
            duration = safe_float(event.get("duration"))
            
            # Calculate duration if missing or invalid
            if duration <= 0 and elapsed_seconds >= 0 and exit_time >= 0:
                duration = safe_duration_calculation(elapsed_seconds, exit_time)
            
            zeit_str = seconds_to_hhmmss(elapsed_seconds)
            today = datetime.today()
            start_datetime = datetime.combine(today, start_time)
            event_datetime = start_datetime + timedelta(seconds=elapsed_seconds)
            uhrzeit_str = event_datetime.strftime("%H:%M:%S")
            
            # Extract event data with safe handling
            frame_idx = event.get("frame_idx", "")
            bat_center = event.get("bat_center", (None, None))
            bat_x, bat_y = bat_center if bat_center else ("", "")
            
            # Safe polygon area handling
            polygon_area = event.get("polygon_area", "")
            if polygon_area != "" and isinstance(polygon_area, (int, float)) and polygon_area >= 0:
                polygon_area = f"#{int(polygon_area) + 1}"
            else:
                polygon_area = ""
            
            # ROI information with safe handling
            roi = event.get("roi", (None, None, None, None))
            roi_x, roi_y, roi_w, roi_h = roi if roi and len(roi) >= 4 else ("", "", "", "")

            writer.writerow([
                video_id, 
                start_time.strftime("%H:%M:%S"), 
                zeit_str, 
                uhrzeit_str,
                f"{elapsed_seconds:.2f}" if elapsed_seconds >= 0 else "",
                f"{exit_time:.2f}" if exit_time >= 0 else "",
                f"{duration:.2f}" if duration >= 0 else "",
                frame_idx,
                bat_x,
                bat_y,
                polygon_area,
                roi_x,
                roi_y,
                roi_w,
                roi_h
            ])

    print(f"Exported {len(events)} events with polygon information to {csv_path}")
    
    
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
    
    
    
def export_events_to_csv(events, video_path, csv_path, username=None):
    """
    Export event data to CSV
    
    Args:
        events: List of event dictionaries
        video_path: Path to the source video
        csv_path: Path where CSV will be saved
        username: Optional username to include in the CSV
    """
    if username is None:
        try:
            import getpass
            username = getpass.getuser()
        except:
            username = "unknown"
            
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['entry_time', 'exit_time', 'duration', 'video_file', 'timestamp', 'user']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for event in events:
            # Safe handling of event data
            entry_time = safe_float(event.get('entry'))
            exit_time = safe_float(event.get('exit'))
            duration = safe_float(event.get('duration'))
            
            # Calculate duration if missing
            if duration <= 0 and entry_time >= 0 and exit_time >= 0:
                duration = safe_duration_calculation(entry_time, exit_time)
            
            # Only write row if we have valid entry and exit times
            if entry_time >= 0 and exit_time >= 0:
                writer.writerow({
                    'entry_time': f"{entry_time:.2f}",
                    'exit_time': f"{exit_time:.2f}",
                    'duration': f"{duration:.2f}",
                    'video_file': os.path.basename(video_path),
                    'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                    'user': username
                })


def export_summary_csv(events, video_path=None, user_choice=None):
    """
    Export summary statistics CSV with aggregate data
    
    Args:
        events (list): Detection events
        video_path (str): Video file path
        user_choice (str): User folder choice for organization
    """
    try:
        # Use structured output if user choice provided
        if user_choice:
            from utils.result_organizer import create_video_result_structure, get_standardized_filename
            structure = create_video_result_structure(video_path, user_choice=user_choice)
            filename = get_standardized_filename("summary", structure["video_name"])
            file_path = os.path.join(structure["base"], filename)
        else:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="Zusammenfassungs-CSV speichern"
            )
            if not file_path:
                return None
    except Exception as e:
        print(f"[WARNING] Could not use structured export: {e}")
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Zusammenfassungs-CSV speichern"
        )
        if not file_path:
            return None

    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header with metadata
            writer.writerow(['# Fledermaus-Erkennungszusammenfassung'])
            writer.writerow(['# Erstellt am:', datetime.now().strftime("%d.%m.%Y %H:%M:%S")])
            
            if video_path:
                writer.writerow(['# Video-Datei:', os.path.basename(video_path)])
            
            # Calculate summary statistics with safe handling
            if events:
                total_events = len(events)
                
                # Safe duration calculations
                durations = [safe_float(event.get('duration')) for event in events]
                valid_durations = [d for d in durations if d > 0]
                
                total_duration = sum(valid_durations)
                avg_duration = total_duration / len(valid_durations) if valid_durations else 0
                min_duration = min(valid_durations) if valid_durations else 0
                max_duration = max(valid_durations) if valid_durations else 0
                
                # Time-based analysis with safe handling
                entry_times = [safe_float(event.get('entry')) for event in events]
                exit_times = [safe_float(event.get('exit')) for event in events]
                
                valid_entry_times = [t for t in entry_times if t >= 0]
                valid_exit_times = [t for t in exit_times if t >= 0]
                
                first_activity = min(valid_entry_times) if valid_entry_times else 0
                last_activity = max(valid_exit_times) if valid_exit_times else 0
                active_period = max(0, last_activity - first_activity)
                
                writer.writerow([])
                writer.writerow(['Statistik', 'Wert', 'Einheit'])
                writer.writerow(['Gesamte Ereignisse', total_events, 'Anzahl'])
                writer.writerow(['Gesamte Aktivitätsdauer', f"{total_duration:.2f}", 'Sekunden'])
                writer.writerow(['Durchschnittliche Dauer', f"{avg_duration:.2f}", 'Sekunden'])
                writer.writerow(['Minimale Dauer', f"{min_duration:.2f}", 'Sekunden'])
                writer.writerow(['Maximale Dauer', f"{max_duration:.2f}", 'Sekunden'])
                writer.writerow(['Erste Aktivität', f"{first_activity:.2f}", 'Sekunden'])
                writer.writerow(['Letzte Aktivität', f"{last_activity:.2f}", 'Sekunden'])
                writer.writerow(['Aktiver Zeitraum', f"{active_period:.2f}", 'Sekunden'])
                
                # Activity density
                if active_period > 0:
                    activity_density = total_events / (active_period / 60)  # events per minute
                    writer.writerow(['Aktivitätsdichte', f"{activity_density:.2f}", 'Ereignisse/Minute'])
            else:
                writer.writerow(['Keine Ereignisse erkannt', '', ''])
        
        messagebox.showinfo("Zusammenfassung-Export", f"Zusammenfassung erfolgreich exportiert nach: {file_path}")
        return file_path
        
    except Exception as e:
        messagebox.showerror("Export-Fehler", f"Fehler beim Zusammenfassungs-Export: {str(e)}")
        return None