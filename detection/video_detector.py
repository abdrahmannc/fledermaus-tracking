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
