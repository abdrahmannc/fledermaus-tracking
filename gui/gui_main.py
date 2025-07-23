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
        self.root.title("IR-Fledermaus-Erkennungssystem")

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

        # Animation related attributes
        self.animation_window = None
        self.animation_canvas = None
        self.animation_running = False
        self.animation_thread = None
        self.bat_images = []

        self.detector = VideoDetector(self)
        self.setup_gui()
        
        #GUI
    def setup_gui(self):
        self.root.configure(bg="#222")
        control_frame = tk.Frame(self.root, padx=10, pady=10, bg="#282c34")
        control_frame.pack(side=tk.LEFT, fill=tk.Y)
        display_frame = tk.Frame(self.root, padx=10, pady=10, bg="#222")
        display_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        tk.Label(
            control_frame,
            text="IR-Fledermaus-Detektor",
            font=('Helvetica', 20, 'bold'),
            fg="#61dafb",
            bg="#282c34"
        ).pack(pady=10)
        tk.Label(
            control_frame,
            text="Anleitung:\n1. Video laden\n2. ROI auswählen\n3. Erkennung starten\n4. Ergebnisse exportieren",
            fg="white",
            bg="#282c34"
        ).pack(pady=4)

        self.btn_load = tk.Button(control_frame, text="Video laden", bg="#61dafb", fg="#222", command=self.load_video)
        self.btn_load.pack(fill=tk.X, pady=3)

        self.btn_select_roi = tk.Button(control_frame, text="ROI auswählen", state=tk.DISABLED, command=self.on_select_roi)
        self.btn_select_roi.pack(fill=tk.X, pady=3)

        self.btn_start = tk.Button(control_frame, text="Erkennung starten", state=tk.DISABLED, command=self.start_detection)
        self.btn_start.pack(fill=tk.X, pady=3)

        self.btn_stop = tk.Button(control_frame, text="Stop", state=tk.DISABLED, command=self.stop_detection)
        self.btn_stop.pack(fill=tk.X, pady=3)

        self.btn_validate = tk.Button(control_frame, text="Ereignisse validieren", state=tk.DISABLED, command=self.validate_events_gui)
        self.btn_validate.pack(fill=tk.X, pady=3)

        ttk.Separator(control_frame, orient="horizontal").pack(fill=tk.X, pady=8)

        self.btn_export_csv = tk.Button(control_frame, text="CSV exportieren", state=tk.DISABLED, command=self.export_results)
        self.btn_export_csv.pack(fill=tk.X, pady=3)
        self.btn_export_video = tk.Button(control_frame, text="Markiertes Video exportieren", state=tk.DISABLED, command=self.export_marked_video)
        self.btn_export_video.pack(fill=tk.X, pady=3)
        self.btn_export_flightMap = tk.Button(control_frame, text="Flugkarte exportieren", state=tk.DISABLED, command=self.export_flightMap)
        self.btn_export_flightMap.pack(fill=tk.X, pady=3)
        self.btn_export_hotzone = tk.Button(control_frame, text="Hotzonen exportieren", state=tk.DISABLED, command=self.export_hotzone)
        self.btn_export_hotzone.pack(fill=tk.X, pady=3)
        
        self.btn_previous_results = tk.Button(control_frame, text="View Previous Results", command=self.detector.load_previous_results)
        self.btn_previous_results.pack(fill=tk.X, pady=5)

        ttk.Separator(control_frame, orient="horizontal").pack(fill=tk.X, pady=8)

        self.add_labeled_entry(control_frame, "Bewegungsschwelle:", self.MOTION_THRESHOLD, "threshold")
        self.add_labeled_entry(control_frame, "Abkling-Frames:", self.COOLDOWN_FRAMES, "cooldown")
        self.add_labeled_entry(control_frame, "Min. Konturfläche:", self.MIN_CONTOUR_AREA, "min_area")
        self.add_labeled_entry(control_frame, "Max. Konturfläche:", self.MAX_CONTOUR_AREA, "max_area")

        tk.Checkbutton(
            control_frame,
            text="Debug-Modus (erkannte PNGs speichern)",
            variable=self.debug_mode,
            bg="#282c34",
            fg="white",
            selectcolor="#333"
        ).pack(anchor=tk.W, pady=4)

        self.status_var = tk.StringVar(value="Bereit")
        self.status_label = tk.Label(
            control_frame,
            textvariable=self.status_var,
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#282c34",
            fg="#bbb"
        )
        self.status_label.pack(fill=tk.X, pady=4)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(control_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X, pady=2)

        self.btn_play = tk.Button(self.root, text="Abspielen", command=self.play_video, state=tk.DISABLED)
        self.btn_play.pack(pady=2)
        self.btn_pause = tk.Button(self.root, text="Pausieren", command=self.pause_video, state=tk.DISABLED)
        self.btn_pause.pack(pady=2)
        self.btn_stop_video = tk.Button(self.root, text="Video stoppen", command=self.stop_video, state=tk.DISABLED)
        self.btn_stop_video.pack(pady=2)

        speed_frame = tk.Frame(self.root, bg="#222")
        speed_frame.pack(pady=2)
        tk.Label(speed_frame, text="Geschwindigkeit:", bg="#222", fg="#bbb").pack(side=tk.LEFT)
        self.speed_var = tk.StringVar(value="1.0x")
        self.speed_options = ["0.25x", "0.5x", "1.0x", "1.5x", "2.0x"]
        self.speed_box = ttk.Combobox(speed_frame, textvariable=self.speed_var, values=self.speed_options, width=5, state="readonly")
        self.speed_box.pack(side=tk.LEFT)
        self.speed_box.bind("<<ComboboxSelected>>", self.set_speed)

        self.canvas = tk.Canvas(display_frame, bg='black', width=800, height=450, highlightthickness=0)
        self.canvas.pack(expand=True, fill=tk.BOTH)

        self.time_var = tk.StringVar(value="00:00:00 / 00:00:00")
        self.time_label = tk.Label(display_frame, textvariable=self.time_var, bg="#222", fg="#fff", font=("Consolas", 12))
        self.time_label.pack()

        #Optionen
        self.tree = ttk.Treeview(display_frame, columns=('Einflug', 'Ausflug', 'Dauer'), show='headings')
        self.tree.heading('Einflug', text='Einflug')
        self.tree.heading('Ausflug', text='Ausflug')
        self.tree.heading('Dauer', text='Dauer')
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)