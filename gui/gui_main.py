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
            
    #
    def start_detection(self):
        if not self.video_path or not self.roi:
            self.status_var.set("Bitte laden Sie ein Video und wählen Sie ein ROI aus.")
            return
        
        # Show animation before starting detection
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
        
        # Hide animation when detection is stopped
        self.hide_processing_animation()

    def export_results(self):
        self.detector.export_results()

    def export_marked_video(self):
        self.detector.export_marked_video()

    def export_flightMap(self):
        self.detector.export_flightMap()

    def export_hotzone(self):
        self.detector.export_hotzone()
     
    #
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
        
    #
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
            # Change the column order to match the new German column names
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
    #     
    def main():
        root = tk.Tk()
        app = BatDetectorApp(root)
        root.mainloop()

    if __name__ == "__main__":
        main()