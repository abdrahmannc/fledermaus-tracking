
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import cv2
import time
import threading
from visualization.stereo_visualization import create_3d_flight_visualization
from detection.stereo_detector import StereoDetector
from gui.stereo_gui_extension import StereoGUIExtension

def format_time(seconds):
    """Format seconds to HH:MM:SS format"""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

# Flag to check if 3D stereo analysis dependencies are available
STEREO_3D_AVAILABLE = True  # Set this based on your system configuration

class StereoVisionModule:

    def start_stereo_calibration(self):
        """Start stereo camera calibration process"""
        messagebox.showinfo("Stereo-Kalibrierung",
                           "Die Stereo-Kalibrierung wird über die 3D-Analyse GUI  durchgeführt.\n"
                           "Klicken Sie auf '🚀 3D Analyse ' um fortzufahren.")

def show_3d_visualization(self):
        """Show 3D visualization of detected flights"""
        if not STEREO_3D_AVAILABLE:
            messagebox.showerror("3D-Modul nicht verfügbar",
                               "Die 3D-Visualisierung ist nicht verfügbar.")
            return

        if not hasattr(self.detector, 'events') or not self.detector.events:
            messagebox.showwarning("Keine Daten",
                                 "Keine Erkennungsergebnisse für 3D-Visualisierung vorhanden.")
            return

        messagebox.showinfo("3D-Visualisierung",
                           "Die 3D-Visualisierung wird über die 3D-Analyse GUI bereitgestellt.\n"
                           "Klicken Sie auf '🚀 3D Analyse ' um fortzufahren.")


def switch_to_3d_mode(self):
        """Switch to 3D stereo mode"""
        if not STEREO_3D_AVAILABLE:
            messagebox.showerror("3D nicht verfügbar",
                               "3D-Modus ist nicht verfügbar. Verwenden Sie die '🚀 3D Analyse ' Funktion.")
            self.mode_var.set("2D")
            return

        self.mode_var.set("3D")
        if hasattr(self, 'stereo_3d_frame'):
            self.stereo_3d_frame.pack(fill=tk.X, pady=(0, 5))

        # Initialize mode_status_var if it doesn't exist
        if not hasattr(self, 'mode_status_var'):
            self.mode_status_var = tk.StringVar()

        self.mode_status_var.set("Modus: 3D Stereo-Analyse")
        self.update_status("Modus: 3D Stereo-Erkennung")







# ===== 3D STEREO ANALYSIS METHODS =====

def switch_to_2d_mode(self):
    """Switch to 2D analysis mode"""
    self.current_mode = "2D"
    self.mode_status_var.set("Modus: 2D Standard")

    # Enable/disable appropriate controls
    if hasattr(self, 'btn_load_stereo'):
        self.btn_load_stereo.configure(state=tk.DISABLED)
    if hasattr(self, 'btn_3d_analysis'):
        self.btn_3d_analysis.configure(state=tk.DISABLED)

    self.update_status("2D Modus aktiviert - Standard-Videoanalyse")



    self.current_mode = "3D"
    self.mode_status_var.set("Modus: 3D Stereo-Analyse")

    # Enable 3D controls
    if hasattr(self, 'btn_load_stereo'):
        self.btn_load_stereo.configure(state=tk.NORMAL)

    self.update_status("3D Stereo-Modus aktiviert - Laden Sie Stereo-Videos")

    # Show information dialog
    messagebox.showinfo("3D Stereo-Modus",
                        "3D Stereo-Analyse aktiviert!\n\n"
                        "Nächste Schritte:\n"
                        "1. Klicken Sie 'Stereo-Videos laden'\n"
                        "2. Wählen Sie linke und rechte Kamera-Videos\n"
                        "3. Starten Sie die 3D-Analyse\n"
                        "4. Betrachten Sie 3D-Visualisierungen")

def switch_to_hybrid_mode(self):
    """Switch to hybrid 2D/3D analysis mode"""
    if not STEREO_3D_AVAILABLE:
        messagebox.showerror("Fehler", "3D Stereo-Module nicht verfügbar.\nBitte installieren Sie die erforderlichen Abhängigkeiten.")
        self.mode_var.set("2D")  # Reset to 2D
        return

    self.current_mode = "Hybrid"
    self.mode_status_var.set("Modus: Hybrid (2D + 3D)")

    # Enable both 2D and 3D controls
    if hasattr(self, 'btn_load_stereo'):
        self.btn_load_stereo.configure(state=tk.NORMAL)

    self.update_status("Hybrid-Modus aktiviert - 2D und 3D Analyse verfügbar")

def load_stereo_videos(self):
    """Load stereo video pair for 3D analysis"""
    try:
        # Load left camera video
        left_path = filedialog.askopenfilename(
            title="Linke Kamera Video auswählen",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv *.wmv"), ("All Files", "*.*")]
        )

        if not left_path:
            return

        # Load right camera video
        right_path = filedialog.askopenfilename(
            title="Rechte Kamera Video auswählen",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv *.wmv"), ("All Files", "*.*")]
        )

        if not right_path:
            return

        # Store paths
        self.left_video_path = left_path
        self.right_video_path = right_path

        # Validate videos
        left_cap = cv2.VideoCapture(left_path)
        right_cap = cv2.VideoCapture(right_path)

        if not left_cap.isOpened() or not right_cap.isOpened():
            messagebox.showerror("Fehler", "Ein oder beide Videos konnten nicht geladen werden.")
            left_cap.release()
            right_cap.release()
            return

        # Check frame counts
        left_frames = int(left_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        right_frames = int(right_cap.get(cv2.CAP_PROP_FRAME_COUNT))

        left_cap.release()
        right_cap.release()

        if abs(left_frames - right_frames) > 5:  # Allow small difference
            result = messagebox.askyesno("Warnung",
                f"Die Videos haben unterschiedliche Frame-Anzahlen:\n"
                f"Links: {left_frames} Frames\n"
                f"Rechts: {right_frames} Frames\n\n"
                f"Möchten Sie trotzdem fortfahren?")
            if not result:
                return

        # Initialize stereo detector
        self.stereo_detector = StereoDetector()
        self.stereo_detector.load_stereo_videos(left_path, right_path)

        # Enable 3D analysis button
        if hasattr(self, 'btn_3d_analysis'):
            self.btn_3d_analysis.configure(state=tk.NORMAL)

        # Update status
        left_name = os.path.basename(left_path)
        right_name = os.path.basename(right_path)
        self.update_status(f"Stereo-Videos geladen: {left_name} & {right_name}")

        messagebox.showinfo("Erfolg",
                            f"Stereo-Videos erfolgreich geladen!\n\n"
                            f"Links: {left_name}\n"
                            f"Rechts: {right_name}\n"
                            f"Frames: {min(left_frames, right_frames)}\n\n"
                            f"Klicken Sie '3D-Analyse starten' um fortzufahren.")

    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Laden der Stereo-Videos: {e}")

def start_3d_analysis(self):
    """Start 3D stereo analysis"""
    if not self.stereo_detector:
        messagebox.showerror("Fehler", "Bitte laden Sie zuerst Stereo-Videos.")
        return

    try:
        # Show processing dialog
        self.show_processing_animation()
        self.animation_status.set("3D Stereo-Analyse läuft...")

        # Create output directory
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("results", f"stereo_analysis_{timestamp}")
        os.makedirs(output_dir, exist_ok=True)

        # Setup progress callback
        def progress_callback(current, total):
            if hasattr(self, 'progress_var'):
                progress = (current / total) * 100
                self.progress_var.set(progress)
            if hasattr(self, 'animation_status'):
                self.animation_status.set(f"3D-Analyse: Frame {current}/{total}")
            self.root.update_idletasks()

        self.stereo_detector.set_progress_callback(progress_callback)

        # Run detection in separate thread
        def run_detection():
            try:
                # Auto-generate calibration if needed
                self.stereo_detector.auto_generate_calibration()

                # Start detection
                self.stereo_detector.start_detection(output_dir)

                # Get results
                events = self.stereo_detector.get_detection_events()
                trajectory_3d = self.stereo_detector.get_3d_trajectory()

                # Update UI in main thread
                self.root.after(0, lambda: self.on_3d_analysis_complete(events, trajectory_3d, output_dir))

            except Exception as e:
                self.root.after(0, lambda: self.on_3d_analysis_error(str(e)))

        # Start detection thread
        detection_thread = threading.Thread(target=run_detection, daemon=True)
        detection_thread.start()

    except Exception as e:
        self.hide_processing_animation()
        messagebox.showerror("Fehler", f"Fehler beim Starten der 3D-Analyse: {e}")

def on_3d_analysis_complete(self, events, trajectory_3d, output_dir):
    """Handle completion of 3D analysis"""
    try:
        self.hide_processing_animation()

        # Store results
        self.current_3d_events = events
        self.current_3d_trajectory = trajectory_3d
        self.current_output_dir = output_dir

        # Enable visualization buttons
        if hasattr(self, 'btn_view_3d'):
            self.btn_view_3d.configure(state=tk.NORMAL)
        if hasattr(self, 'btn_export_gis'):
            self.btn_export_gis.configure(state=tk.NORMAL)

        # Update results table (combine 2D and 3D data if in hybrid mode)
        if self.current_mode == "Hybrid" and hasattr(self, 'tree'):
            # Show both 2D and 3D results
            self.tree.delete(*self.tree.get_children())
            for i, event in enumerate(events):
                start_time = format_time(event.start_frame / self.fps if hasattr(self, 'fps') else 30)
                end_time = format_time(event.end_frame / self.fps if hasattr(self, 'fps') else 30)
                duration = f"{event.duration:.1f}s"
                self.tree.insert('', 'end', values=(start_time, end_time, duration))

        # Show success message
        messagebox.showinfo("3D-Analyse abgeschlossen",
                            f"3D Stereo-Analyse erfolgreich abgeschlossen!\n\n"
                            f"Ergebnisse:\n"
                            f"• {len(events)} Erkennungsereignisse\n"
                            f"• {len(trajectory_3d)} 3D-Trajektorienpunkte\n"
                            f"• Gespeichert in: {os.path.basename(output_dir)}\n\n"
                            f"Verwenden Sie die Visualisierungsoptionen um die 3D-Ergebnisse anzuzeigen.")

        self.update_status(f"3D-Analyse abgeschlossen: {len(events)} Ereignisse gefunden")

    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler bei der Verarbeitung der 3D-Ergebnisse: {e}")

def on_3d_analysis_error(self, error_msg):
    """Handle 3D analysis errors"""
    self.hide_processing_animation()
    messagebox.showerror("3D-Analyse Fehler", f"Die 3D-Analyse ist fehlgeschlagen:\n\n{error_msg}")
    self.update_status("3D-Analyse fehlgeschlagen")

def view_3d_visualization(self):
    """Create and view 3D visualizations"""
    if not hasattr(self, 'current_3d_trajectory') or not self.current_3d_trajectory:
        messagebox.showerror("Fehler", "Keine 3D-Trajektoriendaten verfügbar. Führen Sie zuerst eine 3D-Analyse durch.")
        return

    try:
        # Show visualization options dialog
        viz_dialog = tk.Toplevel(self.root)
        viz_dialog.title("3D Visualisierung erstellen")
        viz_dialog.resizable(False, False)
        viz_dialog.transient(self.root)
        viz_dialog.grab_set()

        # Center dialog
        viz_dialog.geometry("400x300+{}+{}".format(
            self.root.winfo_x() + 100,
            self.root.winfo_y() + 100
        ))

        ttk.Label(viz_dialog, text="Wählen Sie Visualisierungsformat:",
                    font=('Segoe UI', 11, 'bold')).pack(pady=10)

        # Format selection
        format_var = tk.StringVar(value="matplotlib")

        formats = [
            ("matplotlib", "📊 Statisches 3D-Diagramm (PNG)"),
            ("plotly", "🌐 Interaktive 3D-Visualisierung (HTML)"),
            ("open3d", "☁️ 3D-Punktwolke (PLY)")
        ]

        for value, text in formats:
            ttk.Radiobutton(viz_dialog, text=text, variable=format_var, value=value).pack(anchor=tk.W, padx=20, pady=5)

        # Buttons frame
        btn_frame = ttk.Frame(viz_dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=20)

        def create_visualization():
            try:
                selected_format = format_var.get()
                viz_dialog.destroy()

                # Create visualization
                self.update_status(f"Erstelle {selected_format} Visualisierung...")

                output_path = create_3d_flight_visualization(
                    self.current_3d_trajectory,
                    video_path=self.left_video_path,
                    output_format=selected_format
                )

                if output_path:
                    # Open the created file
                    if selected_format == "plotly":
                        os.startfile(output_path)  # Open HTML in browser
                    elif selected_format == "matplotlib":
                        os.startfile(output_path)  # Open PNG with default viewer
                    elif selected_format == "open3d":
                        messagebox.showinfo("3D-Punktwolke erstellt",
                                            f"3D-Punktwolke gespeichert unter:\n{output_path}\n\n"
                                            f"Öffnen Sie die .ply Datei mit einem 3D-Viewer wie MeshLab.")

                    self.update_status(f"3D Visualisierung erstellt: {os.path.basename(output_path)}")
                else:
                    messagebox.showerror("Fehler", "Visualisierung konnte nicht erstellt werden.")

            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler bei der Visualisierung: {e}")

        ttk.Button(btn_frame, text="Erstellen", command=create_visualization).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Abbrechen", command=viz_dialog.destroy).pack(side=tk.LEFT, padx=5)

    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Öffnen der Visualisierung: {e}")



def open_3d_analysis_gui(self, event=None):
    """Open the responsive dedicated 3D Analysis GUI """
    try:
        if not STEREO_3D_AVAILABLE:
            messagebox.showerror("3D-Modul nicht verfügbar",
                                "Die 3D-Analyse-Module sind nicht verfügbar.\n"
                                "Stellen Sie sicher, dass alle benötigten Bibliotheken installiert sind.")
            return

        # Check if we have any detection results to work with
        if not hasattr(self.detector, 'events') or not self.detector.events:
            response = messagebox.askyesno("Keine 2D-Ereignisse",
                                            "Es wurden noch keine 2D-Erkennungsereignisse gefunden.\n\n"
                                            "Möchten Sie trotzdem die 3D-Analyse öffnen?\n"
                                            "(Sie können später Stereo-Videos laden und analysieren)")
            if not response:
                return

        self.update_status("Öffne 3D-Analyse GUI ...")

        # Create responsive dedicated 3D analysis window
        stereo_window = tk.Toplevel(self.root)
        stereo_window.title("🚀 3D Stereo-Flugbahn-Analyse")

        # Responsive window sizing
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        if screen_width <= 1366:
            # Small screen - optimized size
            window_width = min(900, screen_width - 100)
            window_height = min(600, screen_height - 100)
        else:
            # Large screen - spacious layout
            window_width = 1000
            window_height = 700

        stereo_window.geometry(f"{window_width}x{window_height}")
        stereo_window.minsize(800, 500)
        stereo_window.transient(self.root)

        # Center the window responsively
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        stereo_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Initialize the Stereo GUI Extension
        if not hasattr(self, 'stereo_extension') or not self.stereo_extension:
            self.stereo_extension = StereoGUIExtension(self)

        # Setup the responsive 3D interface in the new window
        self.stereo_extension.setup_stereo_interface(stereo_window)

        # Update status
        self.update_status("3D-Analyse GUI  geöffnet")

        # Show helpful information
        messagebox.showinfo("3D-Analyse geöffnet",
                            "🚀 3D Stereo-Analyse geöffnet!\n\n"
                            "In diesem Fenster können Sie:\n"
                            "• Stereo-Kamera Videos laden\n"
                            "• 3D-Flugbahn-Analyse durchführen\n"
                            "• 3D-Visualisierungen erstellen\n"
                            "• GIS-kompatible 3D-Daten exportieren\n\n"
                            "Das Fenster ist für Ihren Bildschirm optimiert.\n"
                            "Bei kleinen Bildschirmen können Sie scrollen.")

    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Öffnen der 3D-Analyse: {e}")
        # 3D GUI Error handled internally - removed console output


