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