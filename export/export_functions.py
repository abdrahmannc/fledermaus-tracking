import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import getpass
import csv
from datetime import datetime

# Fix matplotlib font issues on Windows

from visualization.stereo_visualization import Stereo3DVisualizer


  
def export_results(self, event=None):
        """Enhanced CSV export with multiple options"""
        try:
            if not hasattr(self.detector, 'events') or not self.detector.events:
                messagebox.showwarning("Keine Daten", "Keine Erkennungsergebnisse zum Exportieren vorhanden.")
                return
            
            # Create export options dialog
            export_window = tk.Toplevel(self.root)
            export_window.title("CSV-Export Optionen")
            export_window.geometry("550x450")
            export_window.minsize(500, 400)
            export_window.resizable(True, True)
            export_window.transient(self.root)
            export_window.grab_set()
            
            # Center the window
            export_window.geometry("+%d+%d" % (
                self.root.winfo_rootx() + 50,
                self.root.winfo_rooty() + 50
            ))
            
            # Create main canvas with scrollbar for responsive design
            canvas = tk.Canvas(export_window)
            scrollbar = ttk.Scrollbar(export_window, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Pack canvas and scrollbar
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
  
            # Cleanup function to unbind when window closes
            def cleanup_bindings():
                try:
                    canvas.unbind_all("<MouseWheel>")
                except tk.TclError:
                    pass
            export_window.protocol("WM_DELETE_WINDOW", lambda: [cleanup_bindings(), export_window.destroy()])
            
            main_frame = ttk.Frame(scrollable_frame, padding=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(main_frame, text="CSV-Export Optionen", 
                     font=('Segoe UI', 12, 'bold')).pack(pady=(0, 15))
            
            # Export type selection
            export_type = tk.StringVar(value="standard")
            
            ttk.Radiobutton(main_frame, text="📊 Standard CSV (Erkennungsdaten)", 
                          variable=export_type, value="standard").pack(anchor=tk.W, pady=2)
            
            ttk.Radiobutton(main_frame, text="📈 Erweitert CSV (mit Flugdaten)", 
                          variable=export_type, value="enhanced").pack(anchor=tk.W, pady=2)
            
            ttk.Radiobutton(main_frame, text="📋 Zusammenfassung CSV (Statistiken)", 
                          variable=export_type, value="summary").pack(anchor=tk.W, pady=2)
            
            # Options frame
            options_frame = ttk.LabelFrame(main_frame, text="Export-Einstellungen", padding=10)
            options_frame.pack(fill=tk.X, pady=(15, 10))
            
            include_metadata = tk.BooleanVar(value=True)
            ttk.Checkbutton(options_frame, text="Metadaten einschließen", 
                          variable=include_metadata).pack(anchor=tk.W)
            
            include_validation = tk.BooleanVar(value=True)
            ttk.Checkbutton(options_frame, text="Validierungsstatus einschließen", 
                          variable=include_validation).pack(anchor=tk.W)
            
            # Buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=(15, 0))
            
            def do_export():
                try:
                    export_window.destroy()
                    
                    # Gather data for export
                    events = self.detector.events
                    video_path = self.video_path
                    
                    # ROI data
                    roi_data = None
                    if self.roi:
                        roi_data = {
                            'x': self.roi[0], 'y': self.roi[1], 
                            'width': self.roi[2], 'height': self.roi[3]
                        }
                    
                    # Polygon data
                    polygon_data = getattr(self, 'polygon_areas', None)
                    
                    # Choose export function based on selection
                    # Get user folder choice for consistent file placement
                    user_choice = getattr(self, 'user_folder_choice', None)
                    
                    if export_type.get() == "standard":
                        from export.csv_export import export_csv
                        result_path = export_csv(events, video_path, roi_data, polygon_data, user_choice)
                        
                        if result_path:
                            self.update_status("CSV-Export erfolgreich abgeschlossen")
                        
                    elif export_type.get() == "enhanced":
                        from export.csv_export import export_enhanced_csv
                        
                        # Get flight paths if available
                        flight_paths = getattr(self.detector, 'bat_paths', None)
                        
                        # Session info
                        session_info = {
                            'session_id': datetime.now().strftime("Session_%Y%m%d_%H%M%S"),
                            'location': 'Nicht angegeben',
                            'observer': getpass.getuser()
                        }
                        
                        export_enhanced_csv(events, video_path, roi_data, polygon_data, 
                                          flight_paths, session_info, user_choice)
                        
                    elif export_type.get() == "summary":
                        self.export_summary_csv(events, video_path, roi_data, polygon_data, user_choice)
                    
                except Exception as e:
                    messagebox.showerror("Export-Fehler", f"Fehler beim CSV-Export: {str(e)}")
            
            ttk.Button(button_frame, text="✅ Exportieren", command=do_export).pack(side=tk.RIGHT, padx=(5, 0))
            ttk.Button(button_frame, text="❌ Abbrechen", 
                      command=export_window.destroy).pack(side=tk.RIGHT)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Öffnen der Export-Optionen: {str(e)}")





def export_summary_csv(self, events, video_path, roi_data, polygon_data, user_choice=None):
        """Export summary statistics CSV"""
        try:
            # Use per-video folder if user chose one, otherwise ask
            if user_choice:
                file_path = os.path.join(user_choice, f"bat_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            else:
                try:
                    file_path = filedialog.asksaveasfilename(
                        defaultextension=".csv",
                        filetypes=[("CSV files", "*.csv")],
                        title="Zusammenfassung CSV speichern"
                    )
                    if not file_path:
                        return
                except KeyboardInterrupt:
                    print("Speichern abgebrochen.")
                    return
                except Exception as e:
                    messagebox.showerror("Fehler", f"Fehler beim Öffnen der Dateiauswahl: {str(e)}")
                    return
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow(['Fledermaus-Erkennungen - Zusammenfassung'])
                writer.writerow(['Erstellt am:', datetime.now().strftime("%d.%m.%Y %H:%M:%S")])
                writer.writerow([])
                
                # Video info
                if video_path:
                    writer.writerow(['Video-Datei:', os.path.basename(video_path)])
                
                # Detection method
                detection_method = "Gesamtes Video"
                if roi_data:
                    detection_method = "ROI-Bereich"
                elif polygon_data and len(polygon_data) > 0:
                    detection_method = f"Polygon-Bereiche ({len(polygon_data)})"
                writer.writerow(['Erkennungsmethode:', detection_method])
                
                writer.writerow([])
                
                # Statistics
                writer.writerow(['=== STATISTIKEN ==='])
                writer.writerow(['Kategorie', 'Wert', 'Einheit'])
                
                total_events = len(events)
                writer.writerow(['Gesamte Erkennungen', total_events, 'Anzahl'])
                
                if events:
                    durations = [event.get('duration', 0) for event in events]
                    total_duration = sum(durations)
                    avg_duration = total_duration / len(durations)
                    min_duration = min(durations)
                    max_duration = max(durations)
                    
                    writer.writerow(['Gesamte Aktivitätsdauer', f"{total_duration:.2f}", 'Sekunden'])
                    writer.writerow(['Durchschnittliche Dauer', f"{avg_duration:.2f}", 'Sekunden'])
                    writer.writerow(['Minimale Dauer', f"{min_duration:.2f}", 'Sekunden'])
                    writer.writerow(['Maximale Dauer', f"{max_duration:.2f}", 'Sekunden'])
                    
                    # Time distribution
                    short_events = len([d for d in durations if d < 1.0])
                    medium_events = len([d for d in durations if 1.0 <= d < 5.0])
                    long_events = len([d for d in durations if d >= 5.0])
                    
                    writer.writerow([])
                    writer.writerow(['=== DAUER-VERTEILUNG ==='])
                    writer.writerow(['Kurz (< 1s)', short_events, 'Anzahl'])
                    writer.writerow(['Mittel (1-5s)', medium_events, 'Anzahl'])
                    writer.writerow(['Lang (> 5s)', long_events, 'Anzahl'])
            
            messagebox.showinfo("Zusammenfassung Export", 
                              f"Zusammenfassung erfolgreich exportiert:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Export-Fehler", f"Fehler beim Zusammenfassungs-Export: {str(e)}")




def prompt_marked_video_export(self):
        """
        Prompt user with confirmation dialog for saving marked video
        """
        # Check if there are events detected (more reliable than checking marked_frames)
        if not hasattr(self.detector, 'events') or not self.detector.events:
            print("[DEBUG] No events detected, skipping marked video prompt")
            return
            
        # Also check if detector has marked frames capability
        if not hasattr(self.detector, 'marked_frames'):
            print("[DEBUG] Detector doesn't support marked frames")
            return
        
        # Show confirmation dialog
        result = messagebox.askyesno(
            "Markiertes Video speichern",
            f"Erkennung abgeschlossen! {len(self.detector.events)} Ereignisse gefunden.\n\n"
            "Möchten Sie das markierte Video speichern?\n\n"
            "Das Video zeigt die erkannten Fledermausbewegungen mit "
            "markierten Bereichen und Flugwegen.",
            icon='question'
        )
        
        if result:  # User clicked Yes
            self.export_marked_video()
        else:
            print("[INFO] User declined to save marked video")




def export_marked_video(self, event=None):
        """Export marked video through detector with error handling - now uses background processing"""
        try:
            # Use background export instead of blocking export
            self.export_marked_video_background()
        except Exception as e:
            messagebox.showerror("Export-Fehler", f"Fehler beim Export des markierten Videos: {str(e)}")
            print(f"[ERROR] Marked video export failed: {e}")
    
    
    
    
def export_marked_video_background(self, event=None):
        """Export marked video in background with progress tracking"""
        try:
            if not hasattr(self.detector, 'marked_frames') or not self.detector.marked_frames:
                messagebox.showinfo("Export Marked Video", "No marked frames available for export.")
                return
            
            # Show progress dialog
            progress_dialog = self.show_progress_dialog("Exporting Marked Video...", cancelable=True)
            
            # Prepare export parameters
            from export.video_export import export_video
            import getpass
            
            try:
                username = getpass.getuser()
            except:
                username = "user"
            
            # Get user choice for folder handling
            user_choice = getattr(self.detector.gui, 'user_folder_choice', None)
            
            def on_export_progress(progress):
                if progress_dialog and not progress_dialog.is_cancelled():
                    progress_dialog.update_progress(progress.get_percentage(), progress.get_status_text())
                    
                    # Close dialog when export is completed
                    if progress.get_percentage() >= 100:
                        self.hide_progress_dialog()
                        self.update_status("Marked video export completed successfully")
                        return
                    
                # Check for cancellation
                if progress_dialog and progress_dialog.is_cancelled():
                    self.background_processor.cancel_processing()
                    self.hide_progress_dialog()
                    self.update_status("Video export cancelled by user")
                    return
            
            # Start background export
            success = self.background_processor.start_export_background(
                export_video,
                self.detector.marked_frames,
                self.detector.fps,
                self.video_path,
                username,
                progress_callback=on_export_progress,
                user_choice=user_choice
            )
            
            if not success:
                self.hide_progress_dialog()
                messagebox.showerror("Export-Fehler", "Export läuft bereits oder konnte nicht gestartet werden")
                
        except Exception as e:
            self.hide_progress_dialog()
            error_msg = f"Failed to start background export: {str(e)}"
            messagebox.showerror("Export-Fehler", error_msg)
            self.update_status(error_msg)


def export_flightMap(self, event=None):
        """Export flight map visualization after detection"""
        try:
            # Check if detection has been performed and events exist
            if not hasattr(self.detector, 'events') or not self.detector.events:
                messagebox.showwarning("Keine Daten", "Führen Sie zuerst eine Erkennung durch, um Flugwege zu exportieren.")
                return
            
            # Get bat paths from detector
            if hasattr(self.detector, 'bat_paths') and self.detector.bat_paths:
                bat_paths = self.detector.bat_paths
            else:
                # Generate bat paths from events if not available
                bat_paths = self.generate_bat_paths_from_events()
            
            if not bat_paths:
                messagebox.showwarning("Keine Flugwege", "Keine Flugweg-Daten verfügbar.")
                return
            
            # Import visualization and result organization
            from visualization.visualization import export_flightMap
            from utils.result_organizer import create_video_result_structure, get_analysis_session_info, get_standardized_filename
            
            # Create structured result directories with user choice
            user_choice = getattr(self, 'user_folder_choice', None)
            structure = create_video_result_structure(self.video_path, user_choice=user_choice)
            session_info = get_analysis_session_info(self.video_path)
            
            # Generate standardized filename for flight map
            flight_filename = get_standardized_filename("flugweg", structure["video_name"])
            
            # Export flight map using structured organization
            result_path = export_flightMap(
                bat_paths, 
                structure["base"],  # Use the video folder directly
                filename_base=os.path.splitext(flight_filename)[0],  # Remove extension for function
                fps=getattr(self, 'fps', 30),
                total_frames=getattr(self, 'total_frames', None)
            )
            
            if result_path and os.path.exists(result_path):
                # Create session summary
                try:
                    from utils.result_organizer import create_result_summary
                    results_created = [result_path]
                    create_result_summary(structure, session_info, results_created)
                    
                    messagebox.showinfo("Flugkarte exportiert", f"Flugkarte und Zusammenfassung gespeichert:\n{structure['base']}")
                except:
                    messagebox.showinfo("Flugkarte exportiert", f"Flugkarte gespeichert:\n{result_path}")
                
                # Ask if user wants to open the visualization
                if messagebox.askyesno("Flugkarte anzeigen", "Möchten Sie die Flugkarte jetzt anzeigen?"):
                    self.display_flight_map(result_path)
            else:
                messagebox.showerror("Fehler", "Flugkarte konnte nicht erstellt werden.")
                
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Exportieren der Flugkarte: {str(e)}")



def export_pdf_report(self, event=None):
    
        """Export comprehensive PDF report with flight paths and analysis"""
        try:
            # Check if detection has been performed
            if not hasattr(self.detector, 'events') or not self.detector.events:
                messagebox.showwarning("Keine Daten", "Führen Sie zuerst eine Erkennung durch, um einen Bericht zu erstellen.")
                return
            
            # Show single input dialog for all video information
            video_info = self.show_video_info_dialog(self.video_path)
            
            if video_info is None:
                # User cancelled
                self.update_status("PDF-Export abgebrochen")
                return
            
            # Import enhanced PDF report generator
            from export.simple_pdf_report import create_pdf_with_video_info
            
            # Gather data for report
            events = self.detector.events
            
            # Transform events to match PDF report expected format
            transformed_events = []
            for event in events:
                transformed_event = {
                    'start_time': event.get('entry', 0),
                    'end_time': event.get('exit', event.get('entry', 0)),
                    'duration': event.get('duration', 0),
                    'frame_idx': event.get('frame_idx', 0),
                    'roi': event.get('roi'),
                    'bat_center': event.get('bat_center'),
                }
                
                # Copy additional fields
                if 'polygon_area' in event:
                    transformed_event['polygon_area'] = event['polygon_area']
                    
                transformed_events.append(transformed_event)
            
            video_path = self.video_path
            
            # Get bat paths if available
            bat_paths = getattr(self.detector, 'bat_paths', None)
            
            # Get ROI data if available
            roi_data = None
            if self.roi:
                roi_data = {
                    'x': self.roi[0],
                    'y': self.roi[1], 
                    'width': self.roi[2],
                    'height': self.roi[3]
                }
            
            # Get polygon data if available
            polygon_data = self.polygon_areas if hasattr(self, 'polygon_areas') else None
            
            # Get user folder choice for consistent file placement
            user_choice = getattr(self, 'user_folder_choice', None)
            
            # Call the enhanced PDF export function
            result = create_pdf_with_video_info(transformed_events, video_path, video_info, 
                                              bat_paths, roi_data, polygon_data, user_choice)
            
            if result is None:
                # Error occurred
                self.update_status("Fehler beim Erstellen des PDF-Berichts")
            elif result:
                self.update_status("PDF-Bericht erfolgreich erstellt")
                messagebox.showinfo("PDF erstellt", 
                                  f"PDF-Bericht wurde erfolgreich erstellt:\n{result}")
            else:
                self.update_status("Fehler beim PDF-Export")
                
        except ImportError:
            messagebox.showerror("Abhängigkeit fehlt", 
                               "PDF-Export-Modul konnte nicht geladen werden.\n"
                               "Bitte überprüfen Sie die Installation.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Erstellen des PDF-Berichts: {str(e)}")
            self.update_status("Fehler beim PDF-Export")

def export_radar_view(self, event=None):
        """Export radar-style visualization of flight paths"""
        try:
            # Check if detection has been performed and flight data exists
            if not hasattr(self.detector, 'events') or not self.detector.events:
                messagebox.showwarning("Keine Daten", "Führen Sie zuerst eine Erkennung durch, um eine Radar-Ansicht zu erstellen.")
                return
            
            # Get flight path data from validation session or bat paths
            flight_path_data = []
            
            if hasattr(self, 'flight_path_data') and self.flight_path_data:
                # Use validation session data if available
                flight_path_data = self.flight_path_data
            elif hasattr(self.detector, 'bat_paths') and self.detector.bat_paths:
                # Convert bat_paths to flight_path_data format
                for i, path in enumerate(self.detector.bat_paths):
                    if path:  # Skip empty paths
                        flight_path_data.append({
                            'event_id': i + 1,
                            'positions': path
                        })
            
            if not flight_path_data:
                messagebox.showwarning("Keine Flugdaten", "Keine Flugweg-Daten für Radar-Ansicht verfügbar.")
                return
            
            # Import radar visualization
            from visualization.visualization import create_radar_style_visualization
            
            self.update_status("Radar-Ansicht wird erstellt...")
            
            # Create radar visualization
            radar_path = create_radar_style_visualization(
                flight_path_data, 
                self.video_path, 
                "Fledermaus-Radar-Ansicht"
            )
            
            if radar_path and os.path.exists(radar_path):
                messagebox.showinfo("Radar-Ansicht exportiert", f"Radar-Ansicht gespeichert:\n{radar_path}")
                
                # Ask if user wants to open the image
                if messagebox.askyesno("Radar-Ansicht anzeigen", "Möchten Sie die Radar-Ansicht jetzt anzeigen?"):
                    try:
                        os.startfile(radar_path)  # Windows
                    except:
                        try:
                            subprocess.run(['xdg-open', radar_path])  # Linux
                        except:
                            messagebox.showinfo("Datei gespeichert", f"Datei gespeichert unter:\n{radar_path}")
                            
                self.update_status("Radar-Ansicht erfolgreich erstellt")
            else:
                messagebox.showerror("Fehler", "Radar-Ansicht konnte nicht erstellt werden.")
                self.update_status("Bereit")
                
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Erstellen der Radar-Ansicht: {str(e)}")
            self.update_status("Bereit")


    
def export_gis_data(self, event=None):
        """Export 3D data in GIS-compatible formats"""
        if not hasattr(self, 'current_3d_trajectory') or not self.current_3d_trajectory:
            messagebox.showerror("Fehler", "Keine 3D-Trajektoriendaten verfügbar. Führen Sie zuerst eine 3D-Analyse durch.")
            return
        
        try:
            # Select output directory
            output_dir = filedialog.askdirectory(title="GIS-Export Verzeichnis auswählen")
            if not output_dir:
                return
            
            self.update_status("Exportiere GIS-Daten...")
            
            # Create visualizer and export
            visualizer = Stereo3DVisualizer(self.current_3d_trajectory)
            gis_files = visualizer.export_gis_compatible_data(output_dir)
            
            if gis_files:
                file_list = "\n".join([f"• {os.path.basename(f)}" for f in gis_files])
                messagebox.showinfo("GIS-Export abgeschlossen", 
                                   f"GIS-Daten erfolgreich exportiert!\n\n"
                                   f"Erstellte Dateien:\n{file_list}\n\n"
                                   f"Gespeichert in: {output_dir}")
                
                # Open output directory
                os.startfile(output_dir)
                
                self.update_status(f"GIS-Export abgeschlossen: {len(gis_files)} Dateien")
            else:
                messagebox.showerror("Fehler", "GIS-Export fehlgeschlagen.")
                
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim GIS-Export: {e}")

    

def export_hotzone(self, event=None):
        self.detector.export_hotzone()
     

