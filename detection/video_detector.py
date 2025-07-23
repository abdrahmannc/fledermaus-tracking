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