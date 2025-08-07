import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw
import cv2

from detection.video_detector import VideoDetector
from utils.video_quality import analyze_video_quality
import math
import time
import threading

def format_time(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

class BatDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fledermaus-Detektor Pro")
        self.root.state("zoomed")
        
        # Konfiguration des Hauptfensters
        self.root.configure(bg="#f0f0f0")
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Benutzerdefinierte Stile
        self.style.configure('TFrame', background="#f0f0f0")
        self.style.configure('TLabel', background="#f0f0f0", font=('Segoe UI', 9))
        self.style.configure('TButton', font=('Segoe UI', 9), padding=5)
        self.style.configure('TEntry', padding=3)
        self.style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'))
        self.style.configure('Status.TLabel', background="#e0e0e0", relief=tk.SUNKEN, padding=5)
        
        # Erkennungsparameter
        self.MOTION_THRESHOLD = 30
        self.COOLDOWN_FRAMES = 15
        self.MIN_CONTOUR_AREA = 5
        self.MAX_CONTOUR_AREA = 100

        self.debug_mode = tk.BooleanVar(value=False)
        self.scale_factor = 0.5
        self.video_path = ""
        self.roi = None
        self.processing = False
        self.playing = False
        self.fps = 30
        self.total_frames = 0
        self.current_frame_idx = 0
        self.playback_speed = 1.0

        # Detektor initialisieren
        self.detector = VideoDetector(self)
        
        # Benutzeroberfläche erstellen
        self.setup_gui()
        
    def setup_gui(self):
        """Konfiguriert die Hauptbenutzeroberfläche"""
        # Hauptcontainer-Frames erstellen
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Linkes Panel - Steuerung
        control_frame = ttk.LabelFrame(main_frame, text="Steuerung", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Rechtes Panel - Videoanzeige und Ergebnisse
        display_frame = ttk.Frame(main_frame)
        display_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        
        # Videoanzeige-Bereich
        video_frame = ttk.LabelFrame(display_frame, text="Video-Anzeige", padding=10)
        video_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(display_frame, bg='#222', width=800, height=450, highlightthickness=1, relief=tk.SUNKEN)
        self.canvas.pack(expand=False, fill=None, pady=(0, 8))
        
        # Video-Steuerung
        video_controls = ttk.Frame(video_frame)
        video_controls.pack(fill=tk.X, pady=(5, 0))
        
        self.btn_play = ttk.Button(video_controls, text="▶ Abspielen", command=self.play_video, state=tk.DISABLED)
        self.btn_play.pack(side=tk.LEFT, padx=2)
        
        self.btn_pause = ttk.Button(video_controls, text="⏸ Pausieren", command=self.pause_video, state=tk.DISABLED)
        self.btn_pause.pack(side=tk.LEFT, padx=2)
        
        self.btn_stop_video = ttk.Button(video_controls, text="⏹ Stopp", command=self.stop_video, state=tk.DISABLED)
        self.btn_stop_video.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(video_controls, text="Geschwindigkeit:").pack(side=tk.LEFT, padx=(10, 2))
        self.speed_var = tk.StringVar(value="1.0x")
        self.speed_options = ["0.25x", "0.5x", "1.0x", "1.5x", "2.0x"]
        self.speed_box = ttk.Combobox(video_controls, textvariable=self.speed_var, 
                                     values=self.speed_options, width=5, state="readonly")
        self.speed_box.pack(side=tk.LEFT)
        self.speed_box.bind("<<ComboboxSelected>>", self.set_speed)
        
        self.time_var = tk.StringVar(value="00:00:00 / 00:00:00")
        time_label = ttk.Label(video_controls, textvariable=self.time_var, font=('Consolas', 10))
        time_label.pack(side=tk.RIGHT)
        
        # Ergebnistabelle
        results_frame = ttk.LabelFrame(display_frame, text="Erkennungsergebnisse", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.tree = ttk.Treeview(results_frame, columns=('Einflug', 'Ausflug', 'Dauer'), show='headings')
        self.tree.heading('Einflug', text='Einflugzeit')
        self.tree.heading('Ausflug', text='Ausflugzeit')
        self.tree.heading('Dauer', text='Dauer')
        self.tree.column('Einflug', width=120, anchor=tk.CENTER)
        self.tree.column('Ausflug', width=120, anchor=tk.CENTER)
        self.tree.column('Dauer', width=120, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Steuerungsbereich-Abschnitte
        self.create_file_controls(control_frame)
        self.create_detection_controls(control_frame)
        self.create_parameter_controls(control_frame)
        self.create_export_controls(control_frame)
        self.create_status_bar(control_frame)
        
    def create_file_controls(self, parent):
        """Dateiverwaltungs-Steuerelemente erstellen"""
        file_frame = ttk.LabelFrame(parent, text="Datei-Operationen", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_load = ttk.Button(file_frame, text="Video laden", command=self.load_video)
        self.btn_load.pack(fill=tk.X, pady=2)
        
        self.btn_select_roi = ttk.Button(file_frame, text="ROI auswählen", state=tk.DISABLED, command=self.on_select_roi)
        self.btn_select_roi.pack(fill=tk.X, pady=2)
        
        self.btn_previous_results = ttk.Button(file_frame, text="Vorherige Ergebnisse anzeigen", 
                                             command=self.detector.load_previous_results)
        self.btn_previous_results.pack(fill=tk.X, pady=(10, 2))
        
    def create_detection_controls(self, parent):
        """Erkennungs-Steuerelemente erstellen"""
        detect_frame = ttk.LabelFrame(parent, text="Erkennung", padding=10)
        detect_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_start = ttk.Button(detect_frame, text="Erkennung starten", state=tk.DISABLED, command=self.start_detection)
        self.btn_start.pack(fill=tk.X, pady=2)
        
        self.btn_stop = ttk.Button(detect_frame, text="Erkennung stoppen", state=tk.DISABLED, command=self.stop_detection)
        self.btn_stop.pack(fill=tk.X, pady=2)
        
        self.btn_validate = ttk.Button(detect_frame, text="Ereignisse validieren", state=tk.DISABLED, 
                                     command=self.validate_events_gui)
        self.btn_validate.pack(fill=tk.X, pady=(10, 2))
        
        ttk.Checkbutton(detect_frame, text="Debug-Modus (erkannte PNGs speichern)", 
                       variable=self.debug_mode).pack(anchor=tk.W, pady=2)
        
    def create_parameter_controls(self, parent):
        """Erkennungsparameter-Steuerelemente erstellen"""
        param_frame = ttk.LabelFrame(parent, text="Erkennungsparameter", padding=10)
        param_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.add_parameter_entry(param_frame, "Bewegungsschwelle:", self.MOTION_THRESHOLD, "threshold")
        self.add_parameter_entry(param_frame, "Abkling-Frames:", self.COOLDOWN_FRAMES, "cooldown")
        self.add_parameter_entry(param_frame, "Min. Konturfläche:", self.MIN_CONTOUR_AREA, "min_area")
        self.add_parameter_entry(param_frame, "Max. Konturfläche:", self.MAX_CONTOUR_AREA, "max_area")
        
    def create_export_controls(self, parent):
        """Export-Steuerelemente erstellen"""
        export_frame = ttk.LabelFrame(parent, text="Ergebnisse exportieren", padding=10)
        export_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_export_csv = ttk.Button(export_frame, text="CSV exportieren", state=tk.DISABLED, 
                                       command=self.export_results)
        self.btn_export_csv.pack(fill=tk.X, pady=2)
        
        self.btn_export_video = ttk.Button(export_frame, text="Markiertes Video exportieren", state=tk.DISABLED, 
                                         command=self.export_marked_video)
        self.btn_export_video.pack(fill=tk.X, pady=2)
        
        self.btn_export_flightMap = ttk.Button(export_frame, text="Flugkarte exportieren", state=tk.DISABLED, 
                                             command=self.export_flightMap)
        self.btn_export_flightMap.pack(fill=tk.X, pady=2)
        
        self.btn_export_hotzone = ttk.Button(export_frame, text="Hotzonen exportieren", state=tk.DISABLED, 
                                           command=self.export_hotzone)
        self.btn_export_hotzone.pack(fill=tk.X, pady=2)
        
    def create_status_bar(self, parent):
        """Statusleiste und Fortschrittsanzeige erstellen"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.status_var = tk.StringVar(value="Bereit")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                style='Status.TLabel', anchor=tk.W)
        status_label.pack(fill=tk.X)
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(parent, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X)
        
    def add_parameter_entry(self, parent, label, default, attr):
        """Hilfsfunktion zum Erstellen beschrifteter Parametereingabefelder"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(frame, text=label, width=18, anchor=tk.W).pack(side=tk.LEFT)
        entry = ttk.Entry(frame, width=8)
        entry.insert(0, str(default))
        entry.pack(side=tk.RIGHT)
        setattr(self, f"entry_{attr}", entry)
        
    def update_status(self, msg):
        """Aktualisiert die Statusmeldung"""
        self.status_var.set(msg)
        self.root.update_idletasks()

    def show_processing_animation(self):
        """Zeigt einen einfachen Verarbeitungsdialog an"""
        if hasattr(self, 'animation_window') and self.animation_window:
            return
            
        self.animation_window = tk.Toplevel(self.root)
        self.animation_window.title("Video wird verarbeitet")
        self.animation_window.resizable(False, False)
        self.animation_window.transient(self.root)
        self.animation_window.grab_set()
        
        # Fenster zentrieren
        window_width = 350
        window_height = 150
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.animation_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Inhalt
        ttk.Label(self.animation_window, text="Video wird verarbeitet...", 
                 font=('Segoe UI', 11, 'bold')).pack(pady=10)
        
        progress = ttk.Progressbar(self.animation_window, mode='indeterminate', length=300)
        progress.pack(pady=5)
        progress.start()
        
        self.animation_status = tk.StringVar(value="Videoframes werden analysiert...")
        ttk.Label(self.animation_window, textvariable=self.animation_status).pack(pady=5)
        
        # Verhindern, dass das Fenster geschlossen wird
        self.animation_window.protocol("WM_DELETE_WINDOW", lambda: None)
        
    def hide_processing_animation(self):
        """Verarbeitungsdialog ausblenden"""
        if hasattr(self, 'animation_window') and self.animation_window:
            try:
                self.animation_window.grab_release()
                self.animation_window.destroy()
            except tk.TclError:
                pass
        self.animation_window = None
        self.animation_canvas = None
        
    def add_labeled_entry(self, parent, label, default, attr):
        frame = tk.Frame(parent, bg="#282c34")
        frame.pack(fill=tk.X, pady=1)
        tk.Label(frame, text=label, fg="#bbb", bg="#282c34").pack(side=tk.LEFT)
        entry = tk.Entry(frame, width=8)
        entry.insert(0, str(default))
        entry.pack(side=tk.RIGHT)
        setattr(self, f"entry_{attr}", entry)

    def update_status(self, msg):
        self.status_var.set(msg)
        self.root.update_idletasks()
        
    def load_video(self):
        self.video_path = filedialog.askopenfilename(
            title="IR-Video auswählen",
            filetypes=[("Video-Dateien", "*.mp4 *.avi *.mov"), ("Alle Dateien", "*.*")]
        )
        if not self.video_path:
            return
        self.cap = cv2.VideoCapture(self.video_path)
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.fps = fps if fps and fps > 0 else 30
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame_idx = 0

        ret, frame = self.cap.read()
        if ret:
            frame_small = cv2.resize(frame, None, fx=self.scale_factor, fy=self.scale_factor)
            green_frame = frame_small.copy()
            green_frame[:, :, 0] = 0
            green_frame[:, :, 2] = 0
            self.show_frame(green_frame)
        else:
            messagebox.showerror("Fehler", "Video konnte nicht gelesen werden.")
            return

        info = analyze_video_quality(self.video_path)
        if "error" in info:
            self.status_var.set("Fehler beim Laden des Videos")
            return

        self.video_quality_info = info
        if info["warnings"]:
            messagebox.showwarning("Video-Qualitätswarnung", "\n".join(info["warnings"]))

        high_motion_minutes = info.get("high_motion_minutes", [])
        if high_motion_minutes:
            motion_times = ", ".join(f"{t:.2f} min" for t in high_motion_minutes)
            messagebox.showinfo("Kamerabewegung", f"\u26a0\ufe0f Hohe Kamerabewegung in:\n\n{motion_times}")

        self.status_var.set(
            f"Geladen: {os.path.basename(self.video_path)} | Helligkeit: {info['avg_brightness']:.1f} | "
            f"Kontrast: {info['avg_contrast']:.1f} | Bewegung: {info['avg_motion']:.1f} | FPS: {self.fps:.1f}"
        )
        self.detector.video_path = self.video_path
        self.detector.status_var = self.status_var
        self.detector.btn_select_roi = self.btn_select_roi
        self.detector.scale_factor = self.scale_factor

        self.btn_play.config(state=tk.NORMAL)
        self.btn_pause.config(state=tk.NORMAL)
        self.btn_stop_video.config(state=tk.NORMAL)
        self.btn_select_roi.config(state=tk.NORMAL)
        self.btn_start.config(state=tk.DISABLED)
        self.update_time_label(0)

    def on_select_roi(self):
        try:
            roi = self.detector.select_roi()
        except RuntimeError as e:
            messagebox.showerror("Fehler", str(e))
            return
        if roi is not None:
            self.roi = roi
            self.status_var.set("ROI wurde ausgewählt.")
            self.btn_start.config(state=tk.NORMAL)
            cap = cv2.VideoCapture(self.detector.video_path)
            ret, frame = cap.read()
            cap.release()
            if ret:
                x, y, w, h = map(int, roi)
                frame_with_roi = frame.copy()
                cv2.rectangle(frame_with_roi, (x, y), (x + w, y + h), (0, 255, 0), 2)
                self.show_frame(frame_with_roi)
        else:
            self.status_var.set("ROI-Auswahl abgebrochen.")
            
    def start_detection(self):
        if not self.video_path or not self.roi:
            self.status_var.set("Bitte laden Sie ein Video und wählen Sie ein ROI aus.")
            return
        
        # Animation vor Beginn der Erkennung anzeigen
        self.show_processing_animation()
        
        self.detector.cap = cv2.VideoCapture(self.video_path)
        self.detector.fps = self.fps
        self.detector.start_detection()
        self.btn_stop.config(state=tk.NORMAL)
        self.enable_export_buttons()
        self.btn_validate.config(state=tk.NORMAL)

    def stop_detection(self):
        self.detector.stop_detection()
        self.status_var.set("Erkennung gestoppt.")
        self.btn_stop.config(state=tk.DISABLED)
        
        # Animation ausblenden, wenn Erkennung gestoppt wird
        self.hide_processing_animation()

    def export_results(self):
        self.detector.export_results()

    def export_marked_video(self):
        self.detector.export_marked_video()

    def export_flightMap(self):
        self.detector.export_flightMap()

    def export_hotzone(self):
        self.detector.export_hotzone()
     
    def show_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width > 0 and canvas_height > 0:
            img = img.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(image=img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def play_video(self):
        if not hasattr(self, "cap") or not self.cap.isOpened():
            messagebox.showerror("Fehler", "Kein Video geladen oder Video kann nicht geöffnet werden.")
            return
        self.playing = True
        self._stream_video()

    def pause_video(self):
        self.playing = False

    def stop_video(self):
        self.playing = False
        if hasattr(self, "cap") and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame_idx = 0
            ret, frame = self.cap.read()
            if ret:
                frame_small = cv2.resize(frame, None, fx=self.scale_factor, fy=self.scale_factor)
                self.show_frame(frame_small)
                self.update_time_label(0)

    def set_speed(self, event=None):
        try:
            self.playback_speed = float(self.speed_var.get().replace("x", ""))
        except ValueError:
            self.playback_speed = 1.0

    def _stream_video(self):
        if not self.playing:
            return
        ret, frame = self.cap.read()
        if not ret:
            self.playing = False
            return
        self.current_frame_idx = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        frame_small = cv2.resize(frame, None, fx=self.scale_factor, fy=self.scale_factor)
        self.show_frame(frame_small)
        self.update_time_label(self.current_frame_idx / self.fps)
        delay = int(1000 / (self.fps * self.playback_speed))
        self.root.after(delay, self._stream_video)
        
    def update_time_label(self, current_sec):
        total_sec = self.total_frames / self.fps if self.fps else 0
        self.time_var.set(f"{format_time(current_sec)} / {format_time(total_sec)}")

    def enable_export_buttons(self):
        self.btn_export_csv.config(state=tk.NORMAL)
        self.btn_export_video.config(state=tk.NORMAL)
        self.btn_export_flightMap.config(state=tk.NORMAL)
        self.btn_export_hotzone.config(state=tk.NORMAL)

    def validate_events_gui(self):
        if self.detector:
            try:
                self.detector.run_manual_validation()
                self.status_var.set("Manuelle Validierung abgeschlossen.")
                print("Manuelle Validierung abgeschlossen.")
            except AttributeError:
                messagebox.showerror("Fehler", "Manuelle Validierungsmethode im Detektor nicht implementiert.")

    def update_event_tree(self, events):
        """
        Aktualisiert die Treeview mit Fledermaus-Ereignissen.
        events: Eine Liste von Dicts wie {'entry': float, 'exit': float, 'duration': float}
        """
        for i in self.tree.get_children():
            self.tree.delete(i)
        for event in events:
            entry = format_time(event['entry'])
            exit_ = format_time(event['exit'])
            duration = format_time(event['duration'])
            # Reihenfolge der Spalten an die neuen deutschen Spaltennamen anpassen
            self.tree.insert('', 'end', values=(entry, exit_, duration))

    def on_detection_finished(self):
        """
        Wird vom VideoDetector aufgerufen, nachdem der Erkennungs-Thread abgeschlossen ist.
        Aktualisiert die Ereignistabelle mit den finalen Erkennungsergebnissen.
        """
        # Hide animation when detection is finished
        self.hide_processing_animation()
        
        if hasattr(self.detector, 'get_events'):
            events = self.detector.get_events()
            self.update_event_tree(events)