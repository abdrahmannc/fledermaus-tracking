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
        
     #Animation   
    def show_processing_animation(self):
        """
        Shows an animated window indicating that bat detection is in progress.
        Displays a flying bat animation alongside progress indicators.
        """
        if self.animation_window is not None:
            return
        
        # Create animation window
        self.animation_window = tk.Toplevel(self.root)
        self.animation_window.title("Fledermaus-Erkennung läuft")
        self.animation_window.geometry("400x300")
        self.animation_window.configure(bg="#282c34")
        self.animation_window.resizable(False, False)
        
        # Center window
        window_width = 400
        window_height = 300
        screen_width = self.animation_window.winfo_screenwidth()
        screen_height = self.animation_window.winfo_screenheight()
        position_x = int((screen_width - window_width) / 2)
        position_y = int((screen_height - window_height) / 2)
        self.animation_window.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
        
        # Add title label
        title_label = tk.Label(
            self.animation_window, 
            text="Fledermäuse werden erkannt...", 
            font=('Helvetica', 14, 'bold'),
            fg="#61dafb", 
            bg="#282c34"
        )
        title_label.pack(pady=(20, 10))
        
        # Add canvas for animation
        self.animation_canvas = tk.Canvas(
            self.animation_window, 
            width=350, 
            height=150, 
            bg="#282c34",
            highlightthickness=0
        )
        self.animation_canvas.pack(pady=10)
        
        # Add progress bar
        self.animation_progress = ttk.Progressbar(
            self.animation_window, 
            mode='indeterminate', 
            length=300
        )
        self.animation_progress.pack(pady=10)
        self.animation_progress.start(15)
        
        # Status text
        self.animation_status = tk.StringVar(value="Spezielle Algorithmen analysieren das Video...")
        animation_status_label = tk.Label(
            self.animation_window, 
            textvariable=self.animation_status,
            fg="white", 
            bg="#282c34"
        )
        animation_status_label.pack(pady=5)
        
        # Prevent closing the window with X button
        self.animation_window.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Create bat images for animation (simple silhouettes)
        self._create_bat_images()
        
        # Start animation in a separate thread
        self.animation_running = True
        self.animation_thread = threading.Thread(target=self._run_bat_animation)
        self.animation_thread.daemon = True
        self.animation_thread.start()
        
        # Update status messages periodically
        self._update_animation_status()

    def _create_bat_images(self):
        """Create a series of bat silhouette images for the animation"""
        self.bat_images = []
        
        # Create 8 bat images with different wing positions
        for i in range(8):
            img = Image.new('RGBA', (60, 30), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Body
            draw.ellipse((25, 10, 35, 20), fill='black')
            
            # Head
            draw.ellipse((33, 8, 40, 15), fill='black')
            
            # Wings - different positions based on animation frame
            wing_angle = math.sin(i/7 * math.pi) * 0.8
            
            # Left wing points
            lw_x1, lw_y1 = 25, 15  # Wing joint
            lw_x2, lw_y2 = 5, 15 - 10 * wing_angle  # Wing tip
            lw_x3, lw_y3 = 15, 20  # Wing bottom
            
            # Right wing points
            rw_x1, rw_y1 = 35, 15  # Wing joint
            rw_x2, rw_y2 = 55, 15 - 10 * wing_angle  # Wing tip
            rw_x3, rw_y3 = 45, 20  # Wing bottom
            
            # Draw wings
            draw.polygon([(lw_x1, lw_y1), (lw_x2, lw_y2), (lw_x3, lw_y3)], fill='black')
            draw.polygon([(rw_x1, rw_y1), (rw_x2, rw_y2), (rw_x3, rw_y3)], fill='black')
            
            # Convert to PhotoImage for Tkinter
            photo = ImageTk.PhotoImage(img)
            self.bat_images.append(photo)

    def _run_bat_animation(self):
        """Run the flying bat animation"""
        if not hasattr(self, 'animation_canvas') or self.animation_canvas is None:
            return
            
        bat_y = 75  # Vertical center of the canvas
        bat_x = -50  # Start off-screen
        img_idx = 0
        
        try:
            while self.animation_running and self.animation_canvas:
                if not self.animation_window:
                    break
                    
                # Clear previous bat
                self.animation_canvas.delete("bat")
                
                # Choose bat image based on animation frame
                bat_img = self.bat_images[img_idx]
                img_idx = (img_idx + 1) % len(self.bat_images)
                
                # Draw bat at current position
                bat_y_offset = int(math.sin(bat_x/30) * 10)  # Vertical movement
                self.animation_canvas.create_image(
                    bat_x, bat_y + bat_y_offset, 
                    image=bat_img, 
                    tags="bat"
                )
                
                # Update bat position
                bat_x += 5
                if bat_x > 400:
                    bat_x = -50
                    
                # Update the animation
                self.animation_canvas.update()
                time.sleep(0.05)
        except (tk.TclError, RuntimeError, AttributeError):
            # Window might have been destroyed
            pass

    def _update_animation_status(self):
        """Updates the status message during animation"""
        if not self.animation_running or not self.animation_window:
            return
            
        messages = [
            "Spezielle Algorithmen analysieren das Video...",
            "Erkennung Fledermausflügel...",
            "Flugmuster werden berechnet...",
            "Analyse der Infrarotdaten...",
            "Bewegungsspuren werden verfolgt...",
            "Erkennungsfilter werden angewendet..."
        ]
        
        message_idx = 0
        
        def update_text():
            nonlocal message_idx
            if not self.animation_running or not self.animation_window:
                return
                
            try:
                self.animation_status.set(messages[message_idx])
                message_idx = (message_idx + 1) % len(messages)
                self.animation_window.after(2000, update_text)
            except (tk.TclError, AttributeError):
                # Window might have been destroyed
                pass
        
        update_text()

    def hide_processing_animation(self):
        """Stop and hide the animation window"""
        self.animation_running = False
        
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(0.1)
        
        if self.animation_window:
            try:
                self.animation_window.destroy()
            except tk.TclError:
                pass
        
        self.animation_window = None
        self.animation_canvas = None