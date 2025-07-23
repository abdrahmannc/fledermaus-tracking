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