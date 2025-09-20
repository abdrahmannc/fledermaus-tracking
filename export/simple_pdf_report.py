"""
Simple PDF Report Generation for Bat Detection Analysis
Creates basic PDF reports without complex dependencies
"""

import os
from datetime import datetime
from tkinter import messagebox, simpledialog
import re

# Try to import reportlab, fall back to simple text-based PDF if not available
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Try to import OpenCV and other modules for flight path visualization
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


def parse_datetime_from_filename(video_path):
    """
    Parse date and time from video filename.
    
    Looks for patterns like:
    - vid_YYYY-MM-DD_HHMMSS (e.g., vid_2025-01-15_191255_1.mp4)
    - YYYYMMDD_HHMMSS (e.g., 20250819_165922)
    - YYYYMMDD-HHMMSS 
    - video_YYYYMMDD_HHMMSS
    - bat_detections_YYYYMMDD_HHMMSS
    
    Returns:
        tuple: (formatted_date, formatted_time) or ("Unbekannt", "Unbekannt")
    """
    try:
        filename = os.path.basename(video_path)
        
        # Patterns to match different filename formats
        patterns = [
            # New pattern for vid_YYYY-MM-DD_HHMMSS format
            r'vid_(\d{4})-(\d{2})-(\d{2})_(\d{6})',  # vid_YYYY-MM-DD_HHMMSS
            r'video_(\d{4})-(\d{2})-(\d{2})_(\d{6})',  # video_YYYY-MM-DD_HHMMSS
            # Original patterns for YYYYMMDD_HHMMSS format
            r'(\d{8})_(\d{6})',  # YYYYMMDD_HHMMSS
            r'(\d{8})-(\d{6})',  # YYYYMMDD-HHMMSS
            r'video_(\d{8})_(\d{6})',  # video_YYYYMMDD_HHMMSS
            r'bat_detections_(\d{8})_(\d{6})',  # bat_detections_YYYYMMDD_HHMMSS
            r'multibat_(\d{8})_(\d{6})',  # multibat_YYYYMMDD_HHMMSS
            r'.*_(\d{8})_(\d{6})',  # any_prefix_YYYYMMDD_HHMMSS
            r'(\d{8}).*_(\d{6})',  # YYYYMMDD_any_HHMMSS
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, filename)
            if match:
                if i < 2:  # New YYYY-MM-DD_HHMMSS patterns
                    # Pattern: vid_YYYY-MM-DD_HHMMSS
                    year = int(match.group(1))
                    month = int(match.group(2))
                    day = int(match.group(3))
                    time_str = match.group(4)
                    
                    # Parse time
                    hour = int(time_str[:2])
                    minute = int(time_str[2:4])
                    second = int(time_str[4:6])
                else:
                    # Original YYYYMMDD_HHMMSS patterns
                    date_str = match.group(1)
                    time_str = match.group(2)
                    
                    # Validate lengths
                    if len(date_str) != 8 or len(time_str) != 6:
                        continue
                    
                    # Parse date
                    year = int(date_str[:4])
                    month = int(date_str[4:6])
                    day = int(date_str[6:8])
                    
                    # Parse time
                    hour = int(time_str[:2])
                    minute = int(time_str[2:4])
                    second = int(time_str[4:6])
                
                # Validate date and time ranges
                if (1900 <= year <= 2100 and 
                    1 <= month <= 12 and 
                    1 <= day <= 31 and 
                    0 <= hour <= 23 and 
                    0 <= minute <= 59 and 
                    0 <= second <= 59):
                    
                    # Format as DD.MM.YYYY and HH:MM:SS
                    formatted_date = f"{day:02d}.{month:02d}.{year}"
                    formatted_time = f"{hour:02d}:{minute:02d}:{second:02d}"
                    
                    return formatted_date, formatted_time
        
        # If no valid pattern found, return defaults
        return "Unbekannt", "Unbekannt"
        
    except Exception as e:
        print(f"Error parsing datetime from filename: {e}")
        return "Unbekannt", "Unbekannt"


def create_flight_path_image(flight_paths, video_path):
    """
    Create a flight path visualization image for the PDF report
    """
    if not OPENCV_AVAILABLE or not flight_paths:
        return None
    
    try:
        # Open video to get a background frame
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        # Get middle frame as background
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 2)
        ret, frame = cap.read()
        cap.release()
        
        if not ret or frame is None:
            return None
        
        # Create flight path overlay
        overlay = frame.copy()
        height, width = frame.shape[:2]
        
        # Define colors for different flight paths
        colors_list = [
            (0, 255, 0),    # Green
            (255, 0, 0),    # Blue
            (0, 0, 255),    # Red
            (255, 255, 0),  # Cyan
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Yellow
        ]
        
        # Draw flight paths
        for i, path in enumerate(flight_paths):
            if path and len(path) > 1:
                color = colors_list[i % len(colors_list)]
                
                # Convert path points to integers and draw lines
                points = []
                for point in path:
                    if isinstance(point, (list, tuple)) and len(point) >= 2:
                        x, y = int(point[0]), int(point[1])
                        # Ensure coordinates are within frame bounds
                        x = max(0, min(x, width - 1))
                        y = max(0, min(y, height - 1))
                        points.append((x, y))
                
                # Draw flight path as connected lines
                for j in range(len(points) - 1):
                    cv2.line(overlay, points[j], points[j + 1], color, 3)
                
                # Draw start and end markers
                if points:
                    cv2.circle(overlay, points[0], 8, (0, 255, 0), -1)  # Start (green)
                    cv2.circle(overlay, points[-1], 8, (0, 0, 255), -1)  # End (red)
                    
                    # Add path number
                    cv2.putText(overlay, f"#{i+1}", 
                               (points[0][0] + 10, points[0][1] - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Blend with original frame
        alpha = 0.7
        blended = cv2.addWeighted(frame, alpha, overlay, 1 - alpha, 0)
        
        # Save the image using structured organization
        from utils.result_organizer import create_video_result_structure, get_standardized_filename
        structure = create_video_result_structure(video_path)
        
        image_filename = get_standardized_filename("flight_paths", structure["video_name"])
        image_path = os.path.join(structure["base"], image_filename)
        
        cv2.imwrite(image_path, blended)
        return image_path
        
    except Exception as e:
        print(f"Error creating flight path image: {e}")
        return None


def create_simple_pdf_report(events, video_path, flight_paths=None, roi_data=None, polygon_data=None):
    """
    Create a simple PDF report with bat detection results
    
    Args:
        events (list): Detection events with timestamps and durations
        video_path (str): Path to analyzed video
        flight_paths (list): Flight path data (optional)
        roi_data (dict): ROI information if used
        polygon_data (list): Polygon areas if used
    """
    if not REPORTLAB_AVAILABLE:
        create_text_report(events, video_path, flight_paths, roi_data, polygon_data)
        return
        
    try:
        # Import result organization utilities
        from utils.result_organizer import create_video_result_structure, get_analysis_session_info, get_standardized_filename
        
        # Create structured result directories
        structure = create_video_result_structure(video_path)
        session_info = get_analysis_session_info(video_path)
        
        # Parse date and time from video filename first
        parsed_date, parsed_time = parse_datetime_from_filename(video_path)
        
        # Get user input for location, observer, and video information
        # Check for cancellation at each step
        location = simpledialog.askstring("Aufnahmeort", 
                                         "Bitte geben Sie den geografischen Ort der Aufnahme ein:",
                                         initialvalue="Unbekannter Ort")
        if location is None:  # User clicked Cancel
            return None
        if not location:
            location = "Unbekannter Ort"
            
        observer = simpledialog.askstring("Beobachter",
                                        "Bitte geben Sie den Namen des Beobachters ein:",
                                        initialvalue="Unbekannt")
        if observer is None:  # User clicked Cancel
            return None
        if not observer:
            observer = "Unbekannt"
        
        # Get additional video information
        video_description = simpledialog.askstring("Video-Beschreibung",
                                                  "Bitte beschreiben Sie das Video (optional):",
                                                  initialvalue="")
        if video_description is None:  # User clicked Cancel
            return None
        if not video_description:
            video_description = "Keine Beschreibung"
            
        # Use parsed date/time as initial values, allow user to override
        recording_date = simpledialog.askstring("Aufnahmedatum",
                                               f"Aufnahmedatum (automatisch erkannt: {parsed_date}):",
                                               initialvalue=parsed_date)
        if recording_date is None:  # User clicked Cancel
            return None
        if not recording_date:
            recording_date = parsed_date
            
        recording_time = simpledialog.askstring("Aufnahmezeit", 
                                               f"Aufnahmezeit (automatisch erkannt: {parsed_time}):",
                                               initialvalue=parsed_time)
        if recording_time is None:  # User clicked Cancel
            return None
        if not recording_time:
            recording_time = parsed_time
        
        # Create report filename using standardized naming
        filename = get_standardized_filename("report", structure["video_name"])
        report_path = os.path.join(structure["base"], filename)
        
        # Create PDF document with UTF-8 support
        doc = SimpleDocTemplate(report_path, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Try to use Unicode-supporting font
        try:
            pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
            default_font = 'DejaVuSans'
        except:
            default_font = 'Times-Roman'  # ReportLab built-in font
        
        # Title with UTF-8 support
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName=default_font
        )
        story.append(Paragraph("Fledermaus-Erkennungsbericht", title_style))
        story.append(Spacer(1, 30))
        
        # Report info - ensure video filename is properly extracted
        video_filename = "Unbekannt"
        if video_path:
            try:
                video_filename = os.path.basename(video_path)
                if not video_filename:  # If basename is empty
                    video_filename = "Unbekannt"
            except Exception:
                video_filename = "Unbekannt"
                
        info_data = [
            ['Video-Datei:', video_filename],
            ['Video-Beschreibung:', video_description],
            ['Aufnahmedatum:', recording_date],
            ['Aufnahmezeit:', recording_time],
            ['Aufnahmeort:', location],
            ['Beobachter:', observer],
            ['Analysiert am:', datetime.now().strftime("%d.%m.%Y um %H:%M:%S")],
            ['Software:', 'Fledermaus-Detektor Pro']
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 30))
        
        # Summary section
        story.append(Paragraph("Zusammenfassung", styles['Heading2']))
        
        total_detections = len(events)
        total_duration = sum(event.get('duration', 0) for event in events)
        avg_duration = total_duration / total_detections if total_detections > 0 else 0
        
        # Detection method
        detection_method = "Gesamtes Video"
        if roi_data:
            detection_method = "ROI (Interessenbereich)"
        elif polygon_data and len(polygon_data) > 0:
            detection_method = f"Polygon-Bereiche ({len(polygon_data)} Bereiche)"
        
        summary_data = [
            ['Gesamte Erkennungen:', str(total_detections)],
            ['Erkennungsmethode:', detection_method],
            ['Gesamte Aktivitätsdauer:', f"{total_duration:.1f} Sekunden"],
            ['Durchschnittliche Ereignisdauer:', f"{avg_duration:.1f} Sekunden"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        
        # Add flight path visualization if available
        if flight_paths:
            story.append(PageBreak())
            story.append(Paragraph("Flugbahn-Visualisierung", styles['Heading2']))
            
            try:
                # Create flight path image
                flight_image_path = create_flight_path_image(flight_paths, video_path)
                if flight_image_path and os.path.exists(flight_image_path):
                    # Add image to PDF
                    img = Image(flight_image_path, width=6*inch, height=4*inch)
                    story.append(img)
                    story.append(Spacer(1, 12))
                    story.append(Paragraph("Darstellung der erkannten Flugbahnen über den Videoframes.", styles['Normal']))
                else:
                    story.append(Paragraph("Flugbahn-Visualisierung konnte nicht erstellt werden.", styles['Normal']))
            except Exception as e:
                story.append(Paragraph(f"Flugbahn-Visualisierung nicht verfügbar (OpenCV/PIL erforderlich).", styles['Normal']))
                
            # Add flight path statistics
            story.append(Spacer(1, 10))
            flight_stats = f"Anzahl erkannter Flugbahnen: {len([path for path in flight_paths if path])}"
            story.append(Paragraph(flight_stats, styles['Normal']))
        
        # Detection details
        story.append(Paragraph("Detaillierte Erkennungsergebnisse", styles['Heading2']))
        
        if events:
            # Table header
            table_data = [['Nr.', 'Einflugzeit', 'Ausflugzeit', 'Dauer (s)']]
            
            # Add events
            for i, event in enumerate(events, 1):
                entry_time = format_time_simple(event.get('entry', 0))
                exit_time = format_time_simple(event.get('exit', 0))
                duration = f"{event.get('duration', 0):.1f}"
                
                table_data.append([str(i), entry_time, exit_time, duration])
            
            # Create table
            details_table = Table(table_data, colWidths=[0.5*inch, 1.5*inch, 1.5*inch, 1*inch])
            details_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            story.append(details_table)
        else:
            story.append(Paragraph("Keine Erkennungen gefunden.", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        messagebox.showinfo("PDF Bericht", f"Bericht erfolgreich erstellt:\n{report_path}")
        
        # Create session summary
        from utils.result_organizer import create_result_summary
        results_created = [report_path]
        
        # Add flight path image if it was created
        if flight_paths:
            try:
                flight_image_path = create_flight_path_image(flight_paths, video_path)
                if flight_image_path:
                    results_created.append(flight_image_path)
            except:
                pass
        
        create_result_summary(structure, session_info, results_created)
        
        # Ask if user wants to open the PDF
        if messagebox.askyesno("PDF öffnen", "Möchten Sie den PDF-Bericht jetzt öffnen?"):
            try:
                os.startfile(report_path)  # Windows
            except:
                try:
                    import subprocess
                    subprocess.run(['xdg-open', report_path])  # Linux
                except:
                    messagebox.showinfo("PDF erstellt", f"PDF-Bericht gespeichert unter:\n{report_path}")
        else:
            messagebox.showinfo("PDF erstellt", f"PDF-Bericht und Zusammenfassung gespeichert unter:\n{structure['base']}")
        
        return report_path
        
    except Exception as e:
        messagebox.showerror("PDF-Fehler", f"Fehler beim Erstellen des PDF-Berichts: {str(e)}")
        return None


def create_text_report(events, video_path, flight_paths=None, roi_data=None, polygon_data=None):
    """
    Create a text-based report when reportlab is not available
    """
    try:
        # Import result organization utilities
        from utils.result_organizer import create_video_result_structure, get_analysis_session_info, get_standardized_filename
        
        # Create structured result directories
        structure = create_video_result_structure(video_path)
        session_info = get_analysis_session_info(video_path)
        
        # Generate filename using standardized naming
        filename = get_standardized_filename("report_text", structure["video_name"])
        file_path = os.path.join(structure["base"], filename)
        
        # Parse date and time from video filename first
        parsed_date, parsed_time = parse_datetime_from_filename(video_path)
        
        # Get user input including video information
        # Check for cancellation at each step
        location = simpledialog.askstring("Aufnahmeort", 
                                         "Bitte geben Sie den geografischen Ort der Aufnahme ein:",
                                         initialvalue="Unbekannter Ort")
        if location is None:  # User clicked Cancel
            return None
        if not location:
            location = "Unbekannter Ort"
            
        observer = simpledialog.askstring("Beobachter",
                                        "Bitte geben Sie den Namen des Beobachters ein:",
                                        initialvalue="Unbekannt")
        if observer is None:  # User clicked Cancel
            return None
        if not observer:
            observer = "Unbekannt"
            
        # Get additional video information
        video_description = simpledialog.askstring("Video-Beschreibung",
                                                  "Bitte beschreiben Sie das Video (optional):",
                                                  initialvalue="")
        if video_description is None:  # User clicked Cancel
            return None
        if not video_description:
            video_description = "Keine Beschreibung"
            
        # Use parsed date/time as initial values, allow user to override
        recording_date = simpledialog.askstring("Aufnahmedatum",
                                               f"Aufnahmedatum (automatisch erkannt: {parsed_date}):",
                                               initialvalue=parsed_date)
        if recording_date is None:  # User clicked Cancel
            return None
        if not recording_date:
            recording_date = parsed_date
            
        recording_time = simpledialog.askstring("Aufnahmezeit", 
                                               f"Aufnahmezeit (automatisch erkannt: {parsed_time}):",
                                               initialvalue=parsed_time)
        if recording_time is None:  # User clicked Cancel
            return None
        if not recording_time:
            recording_time = parsed_time
        # Extract video filename safely
        video_filename = "Unbekannt"
        if video_path:
            try:
                video_filename = os.path.basename(video_path)
                if not video_filename:  # If basename is empty
                    video_filename = "Unbekannt"
            except Exception:
                video_filename = "Unbekannt"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("FLEDERMAUS-ERKENNUNGSBERICHT\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Video-Datei: {video_filename}\n")
            f.write(f"Video-Beschreibung: {video_description}\n")
            f.write(f"Aufnahmedatum: {recording_date}\n")
            f.write(f"Aufnahmezeit: {recording_time}\n")
            f.write(f"Aufnahmeort: {location}\n")
            f.write(f"Beobachter: {observer}\n")
            f.write(f"Analysiert am: {datetime.now().strftime('%d.%m.%Y um %H:%M:%S')}\n")
            f.write(f"Software: Fledermaus-Detektor Pro\n\n")
            
            # Summary
            f.write("ZUSAMMENFASSUNG\n")
            f.write("-" * 20 + "\n")
            
            total_detections = len(events)
            total_duration = sum(event.get('duration', 0) for event in events)
            avg_duration = total_duration / total_detections if total_detections > 0 else 0
            
            detection_method = "Gesamtes Video"
            if roi_data:
                detection_method = "ROI (Interessenbereich)"
            elif polygon_data and len(polygon_data) > 0:
                detection_method = f"Polygon-Bereiche ({len(polygon_data)} Bereiche)"
            
            f.write(f"Gesamte Erkennungen: {total_detections}\n")
            f.write(f"Erkennungsmethode: {detection_method}\n")
            f.write(f"Gesamte Aktivitätsdauer: {total_duration:.1f} Sekunden\n")
            f.write(f"Durchschnittliche Ereignisdauer: {avg_duration:.1f} Sekunden\n\n")
            
            # Detailed results
            f.write("DETAILLIERTE ERKENNUNGSERGEBNISSE\n")
            f.write("-" * 35 + "\n")
            
            if events:
                f.write(f"{'Nr.':<4} {'Einflugzeit':<12} {'Ausflugzeit':<12} {'Dauer (s)':<10}\n")
                f.write("-" * 42 + "\n")
                
                for i, event in enumerate(events, 1):
                    entry_time = format_time_simple(event.get('entry', 0))
                    exit_time = format_time_simple(event.get('exit', 0))
                    duration = f"{event.get('duration', 0):.1f}"
                    
                    f.write(f"{i:<4} {entry_time:<12} {exit_time:<12} {duration:<10}\n")
            else:
                f.write("Keine Erkennungen gefunden.\n")
        
        # Create session summary
        from utils.result_organizer import create_result_summary
        results_created = [file_path]
        create_result_summary(structure, session_info, results_created)
        
        messagebox.showinfo("Text-Bericht", f"Text-Bericht und Zusammenfassung erstellt:\n{structure['base']}")
        return file_path
        
    except Exception as e:
        messagebox.showerror("Text-Bericht Fehler", f"Fehler beim Erstellen des Text-Berichts: {str(e)}")
        return None


def format_time_simple(seconds):
    """Format seconds to MM:SS format"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


# Main export function to be called from GUI
def export_pdf_report(events, video_path, flight_paths=None, roi_data=None, polygon_data=None):
    """
    Main function to export PDF report - for backward compatibility
    """
    return create_simple_pdf_report(events, video_path, flight_paths, roi_data, polygon_data)


def create_pdf_with_video_info(events, video_path, video_info, flight_paths=None, roi_data=None, polygon_data=None, user_choice=None):
    """
    Create PDF report with pre-collected video information
    
    Args:
        events: Detection events
        video_path: Path to video file
        video_info: Dictionary with video information fields
        flight_paths: Flight path data
        roi_data: ROI information
        polygon_data: Polygon data
        user_choice: User folder choice for organization
        
    Returns:
        str: Path to created PDF or None if failed
    """
    try:
        if not REPORTLAB_AVAILABLE:
            # Fall back to text report
            return create_text_report_with_info(events, video_path, video_info, flight_paths, roi_data, polygon_data, user_choice)
        
        # Import result organization utilities
        from utils.result_organizer import create_video_result_structure, get_analysis_session_info, get_standardized_filename
        
        # Create structured result directories with user choice
        structure = create_video_result_structure(video_path, user_choice=user_choice)
        session_info = get_analysis_session_info(video_path)
        
        # Create report filename using standardized naming
        filename = get_standardized_filename("report", structure["video_name"])
        report_path = os.path.join(structure["base"], filename)
        
        # Create PDF document with UTF-8 support
        doc = SimpleDocTemplate(report_path, pagesize=A4)
        story = []
        
        # Try to use Unicode-supporting font
        try:
            pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
            default_font = 'DejaVuSans'
        except:
            default_font = 'Times-Roman'  # ReportLab built-in font
        
        # Define styles with UTF-8 support
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            fontName=default_font,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=15,
            textColor=colors.darkblue
        )
        
        # Title
        story.append(Paragraph("Fledermaus-Erkennungs-Bericht", title_style))
        story.append(Spacer(1, 12))
        
        # Video information section
        story.append(Paragraph("Video-Informationen", heading_style))
        
        video_data = [
            ['Video-Name:', video_info.get('video_name', 'Unbekannt')],
            ['Dateiname:', os.path.basename(video_path)],
            ['Aufnahmedatum:', video_info.get('recording_date', 'Unbekannt')],
            ['Aufnahmezeit:', video_info.get('recording_time', 'Unbekannt')],
            ['Aufnahmeort:', video_info.get('location', 'Unbekannt')],
            ['Beobachter:', video_info.get('observer', 'Unbekannt')],
            ['Beschreibung:', video_info.get('description', 'Keine Beschreibung')]
        ]
        
        video_table = Table(video_data, colWidths=[2*inch, 4*inch])
        video_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(video_table)
        story.append(Spacer(1, 20))
        
        # Analysis summary
        story.append(Paragraph("Analyse-Zusammenfassung", heading_style))
        
        total_events = len(events)
        total_duration = max([event['end_time'] for event in events]) if events else 0
        
        summary_data = [
            ['Erkannte Ereignisse:', str(total_events)],
            ['Analyse-Zeitraum:', f"{total_duration:.1f} Sekunden"],
            ['Ereignisse pro Minute:', f"{(total_events / (total_duration / 60)):.1f}" if total_duration > 0 else "0"],
            ['Bericht erstellt:', datetime.now().strftime("%d.%m.%Y %H:%M:%S")]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Add flight path visualization if available
        if flight_paths:
            story.append(Paragraph("Flugweg-Visualisierung", heading_style))
            
            # Create flight path image
            flight_image_path = create_flight_path_image(flight_paths, video_path)
            if flight_image_path and os.path.exists(flight_image_path):
                try:
                    img = Image(flight_image_path, width=6*inch, height=4*inch)
                    story.append(img)
                    story.append(Spacer(1, 20))
                except Exception as e:
                    story.append(Paragraph(f"Flugweg-Bild konnte nicht geladen werden: {str(e)}", styles['Normal']))
                    story.append(Spacer(1, 20))
        
        # ROI information
        if roi_data:
            story.append(Paragraph("Region of Interest (ROI)", heading_style))
            roi_info = [
                ['X-Position:', str(roi_data['x'])],
                ['Y-Position:', str(roi_data['y'])],
                ['Breite:', str(roi_data['width'])],
                ['Höhe:', str(roi_data['height'])]
            ]
            
            roi_table = Table(roi_info, colWidths=[2*inch, 4*inch])
            roi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            story.append(roi_table)
            story.append(Spacer(1, 20))
        
        # Events details
        if events:
            story.append(Paragraph("Erkennungs-Details", heading_style))
            
            # Create events table
            events_data = [['#', 'Start (s)', 'Ende (s)', 'Dauer (s)', 'Zentrum X', 'Zentrum Y']]
            
            for i, event in enumerate(events[:50], 1):  # Limit to first 50 events
                events_data.append([
                    str(i),
                    f"{event['start_time']:.2f}",
                    f"{event['end_time']:.2f}",
                    f"{event['end_time'] - event['start_time']:.2f}",
                    f"{event.get('center_x', 'N/A')}",
                    f"{event.get('center_y', 'N/A')}"
                ])
            
            if len(events) > 50:
                events_data.append(['...', '...', '...', '...', '...', '...'])
                events_data.append([f'Total: {len(events)} events', '', '', '', '', ''])
            
            events_table = Table(events_data, colWidths=[0.5*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
            events_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            story.append(events_table)
        
        # Build PDF
        doc.build(story)
        
        # Create result summary
        from utils.result_organizer import create_result_summary
        results_created = {
            'pdf_report': os.path.basename(report_path),
            'analysis_summary': f"{total_events} events detected",
            'flight_paths': bool(flight_paths)
        }
        
        create_result_summary(structure, session_info, results_created)
        
        return report_path
        
    except Exception as e:
        print(f"[ERROR] Failed to create PDF report: {e}")
        return None


def create_text_report_with_info(events, video_path, video_info, flight_paths=None, roi_data=None, polygon_data=None, user_choice=None):
    """
    Create text report with pre-collected video information
    """
    try:
        # Import result organization utilities
        from utils.result_organizer import create_video_result_structure, get_analysis_session_info, get_standardized_filename
        
        # Create structured result directories
        structure = create_video_result_structure(video_path, user_choice=user_choice)
        session_info = get_analysis_session_info(video_path)
        
        # Create report filename
        filename = get_standardized_filename("report", structure["video_name"]).replace('.pdf', '.txt')
        report_path = os.path.join(structure["base"], filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("FLEDERMAUS-ERKENNUNGS-BERICHT\n")
            f.write("=" * 50 + "\n\n")
            
            # Video information
            f.write("VIDEO-INFORMATIONEN:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Video-Name: {video_info.get('video_name', 'Unbekannt')}\n")
            f.write(f"Dateiname: {os.path.basename(video_path)}\n")
            f.write(f"Aufnahmedatum: {video_info.get('recording_date', 'Unbekannt')}\n")
            f.write(f"Aufnahmezeit: {video_info.get('recording_time', 'Unbekannt')}\n")
            f.write(f"Aufnahmeort: {video_info.get('location', 'Unbekannt')}\n")
            f.write(f"Beobachter: {video_info.get('observer', 'Unbekannt')}\n")
            f.write(f"Beschreibung: {video_info.get('description', 'Keine Beschreibung')}\n\n")
            
            # Analysis summary
            total_events = len(events)
            total_duration = max([event['end_time'] for event in events]) if events else 0
            
            f.write("ANALYSE-ZUSAMMENFASSUNG:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Erkannte Ereignisse: {total_events}\n")
            f.write(f"Analyse-Zeitraum: {total_duration:.1f} Sekunden\n")
            f.write(f"Ereignisse pro Minute: {(total_events / (total_duration / 60)):.1f}\n" if total_duration > 0 else "Ereignisse pro Minute: 0\n")
            f.write(f"Bericht erstellt: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n")
            
            # Events details
            if events:
                f.write("ERKENNUNGS-DETAILS:\n")
                f.write("-" * 20 + "\n")
                f.write(f"{'#':<3} {'Start (s)':<10} {'Ende (s)':<10} {'Dauer (s)':<10} {'Zentrum X':<10} {'Zentrum Y':<10}\n")
                f.write("-" * 65 + "\n")
                
                for i, event in enumerate(events, 1):
                    f.write(f"{i:<3} {event['start_time']:<10.2f} {event['end_time']:<10.2f} "
                           f"{event['end_time'] - event['start_time']:<10.2f} "
                           f"{event.get('center_x', 'N/A'):<10} {event.get('center_y', 'N/A'):<10}\n")
        
        # Create result summary
        from utils.result_organizer import create_result_summary
        results_created = {
            'text_report': os.path.basename(report_path),
            'analysis_summary': f"{total_events} events detected",
            'flight_paths': bool(flight_paths)
        }
        
        create_result_summary(structure, session_info, results_created)
        
        return report_path
        
    except Exception as e:
        print(f"[ERROR] Failed to create text report: {e}")
        return None
