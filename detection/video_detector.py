import csv
from datetime import datetime
import os
import threading
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from collections import defaultdict
from validation.manual_validator import validate_event
from export.csv_export import export_events_to_csv
from visualization.visualization import export_flightMap
from export.video_export import export_video
import json
import glob
from datetime import datetime, timezone
import getpass
from os.path import join, exists, dirname, basename

from utils.config import (
    MIN_CONTOUR_AREA, MAX_CONTOUR_AREA,
    NOISE_KERNEL, STABILIZATION_WINDOW,
    COOLDOWN_FRAMES
)

#
class VideoDetector:
    def __init__(self, gui):
        self.gui = gui
        self.cap = None
        self.fps = 0
        self.total_frames = 0
        self.processing = False
        self.back_sub = cv2.createBackgroundSubtractorMOG2()
        self.motion_history = []
        self.events = []
        self.marked_frames = []
        self.bat_centers = []
        self.cooldown_counter = 0
        self.bat_inside = False
        self.roi = None  # (x, y, w, h)
        self.prev_gray = None
        self.video_path = None
        
        
    #
    def load_video(self):
        # Open file dialog to select the IR video file
        self.video_path = filedialog.askopenfilename(
            title="IR-Video auswählen",
            filetypes=[("Video-Dateien", "*.mp4 *.avi *.mov"), ("Alle Dateien", "*.*")]
        )
        if not self.video_path:
            return

        # Load the selected video
        self.cap = cv2.VideoCapture(self.video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Read the first frame of the video
        ret, frame = self.cap.read()
        if ret:
            # Resize the frame for GUI display and convert to grayscale
            frame_small = cv2.resize(frame, (640, 480))
            self.prev_gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)

            # Show frame in the GUI and update status
            self.gui.show_frame(frame_small)
            self.gui.update_status(f"Geladen: {os.path.basename(self.video_path)}")

            # Enable the ROI selection button
            self.gui.btn_select_roi.config(state=tk.NORMAL)
        else:
            # Failed to read the video
            self.gui.update_status("Fehler beim Laden des Videos")

        # Release video capture object
        self.cap.release()
        self.cap = None


    def select_roi(self):
        # Re-open the video to extract the first frame
        cap = cv2.VideoCapture(self.video_path)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            raise RuntimeError("Failed to read a frame for ROI selection.")

        # Launch OpenCV ROI selection tool
        r = cv2.selectROI("ROI auswählen (ziehen, Enter zum Bestätigen)", frame, False, False)
        cv2.destroyAllWindows()

        # If a valid ROI is selected, return it
        if r and r[2] > 0 and r[3] > 0:
            self.roi = r
            return r
        else:
            return None  # No valid ROI selected



def start_detection(self):
    # Ensure both video path and ROI are set before starting detection
    if not self.video_path or not self.roi:
        self.gui.update_status("Video oder ROI fehlt")
        return

    # Prevent starting if a detection is already running
    if self.processing:
        self.gui.update_status("Erkennung läuft bereits")
        return

    # Prepare video capture and detection state
    self.cap = cv2.VideoCapture(self.video_path)
    self.processing = True
    self.motion_history = []
    self.events = []
    self.marked_frames = []
    self.bat_centers = []
    self.cooldown_counter = 0
    self.bat_inside = False

    # Start video processing in a background thread
    threading.Thread(target=self._process_video).start()


def stop_detection(self):
    # Stop the processing loop
    self.processing = False


def _process_video(self):
    x, y, w, h = self.roi
    frame_idx = 0

    try:
        while self.processing and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
            frame_idx += 1

            # Convert the ROI area to grayscale
            gray = cv2.cvtColor(frame[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY)

            # Apply background subtraction to detect motion
            fgmask = self.back_sub.apply(gray)

            # Remove noise using morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (NOISE_KERNEL, NOISE_KERNEL))
            fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)

            # Detect contours in the motion mask
            contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            motion_detected = False
            bat_center = None

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if MIN_CONTOUR_AREA < area < MAX_CONTOUR_AREA:
                    # Compute the centroid of the contour
                    M = cv2.moments(cnt)
                    if M["m00"] == 0:
                        continue
                    cx = int(M["m10"] / M["m00"]) + x
                    cy = int(M["m01"] / M["m00"]) + y
                    bat_center = (cx, cy)
                    motion_detected = True
                    break

            # Update motion history for temporal stabilization
            self.motion_history.append(motion_detected)
            if len(self.motion_history) > STABILIZATION_WINDOW:
                self.motion_history.pop(0)
            stabilized_motion = sum(self.motion_history) > (STABILIZATION_WINDOW // 2)

            # Cooldown logic to avoid duplicate detection
            if self.cooldown_counter > 0:
                self.cooldown_counter -= 1

            # Detect bat entering the ROI
            if stabilized_motion and not self.bat_inside and self.cooldown_counter == 0:
                self.bat_inside = True
                self.events.append({
                    "entry": frame_idx / self.fps,
                    "exit": None,
                    "duration": None,
                    "frame_idx": frame_idx,
                    "roi": self.roi,
                    "bat_center": bat_center
                })
                self.cooldown_counter = COOLDOWN_FRAMES
                self.gui.update_status(f"Fledermaus eingetreten bei {frame_idx / self.fps:.2f}s")

            # Detect bat exiting the ROI
            elif not stabilized_motion and self.bat_inside and self.cooldown_counter == 0:
                self.bat_inside = False
                exit_time = frame_idx / self.fps
                if self.events:
                    self.events[-1]["exit"] = exit_time
                    self.events[-1]["duration"] = exit_time - self.events[-1]["entry"]
                self.cooldown_counter = COOLDOWN_FRAMES
                self.gui.update_status(f"Fledermaus verlassen bei {exit_time:.2f}s")

            # Draw ROI and bat position on frame
            marked = frame.copy()
            if bat_center:
                cv2.circle(marked, bat_center, 7, (0, 255, 0), 2)
                self.bat_centers.append(bat_center)
            cv2.rectangle(marked, (x, y), (x + w, y + h), (0, 255, 255), 1)
            self.marked_frames.append(marked)

    except Exception as e:
        # Handle any errors during detection
        self.gui.update_status(f"Fehler während der Erkennung: {str(e)}")
    finally:
        # Clean up after detection ends
        self.processing = False
        if self.cap:
            self.cap.release()
        self.gui.update_status(f"Erkennung abgeschlossen, {len(self.events)} Ereignisse erkannt")

        # Notify GUI if it supports completion callback
        if hasattr(self.gui, 'on_detection_finished'):
            self.gui.root.after(0, self.gui.on_detection_finished)

#
def export_marked_video(self):
    # Ensure there are marked frames to export
    if not hasattr(self, "marked_frames") or not self.marked_frames:
        messagebox.showinfo("Export Video", "Keine Frames zum Exportieren vorhanden")
        return

    # Export the video using the helper function
    export_video(self.marked_frames, self.fps, self.video_path)


def export_results(self):
    # Ensure there are detection events to export
    if not self.events:
        messagebox.showinfo("Export Ergebnisse", "Keine Ereignisse zum Exportieren.")
        return

    # Generate filename based on video name and current date
    video_name = os.path.splitext(os.path.basename(self.video_path))[0]
    today_str = datetime.today().strftime('%Y-%m-%d')
    csv_filename = f"{video_name}_{today_str}.csv"
    csv_path = os.path.join(os.path.dirname(self.video_path), csv_filename)

    # Export the events to CSV file
    export_events_to_csv(self.events, self.video_path, csv_path)

    # Inform the user
    messagebox.showinfo("Export Ergebnisse", f"Ereignisse erfolgreich exportiert nach:\n{csv_path}")


def export_flightMap(self):
    # Ensure there are bat tracking points and events recorded
    if not self.bat_centers or not self.events:
        messagebox.showinfo("Export Flugkarte", "Keine Fledermaus-Trajektorien verfügbar.")
        return

    # Create time-based flight path (dummy fps used for spacing)
    fps = 15
    bat_paths_with_time = {
        1: [(i / fps, pos[0], pos[1]) for i, pos in enumerate(self.bat_centers)]
    }

    # Set output directory and filename
    output_dir = os.path.join(os.path.dirname(self.video_path), "exports")
    os.makedirs(output_dir, exist_ok=True)
    filename_base = os.path.splitext(os.path.basename(self.video_path))[0]

    # Export the flight map image
    img_path = export_flightMap(bat_paths_with_time, output_dir, filename_base=filename_base, user="IfAÖ")

    # Inform the user
    if img_path:
        messagebox.showinfo("Export Flugkarte", f"Flugkarte gespeichert:\n{img_path}")
    else:
        messagebox.showinfo("Export Flugkarte", "Flugkarte konnte nicht generiert werden.")


def export_hotzone(self):
    # Placeholder for future hotzone export implementation
    print("Exportiere Hotzone...")
