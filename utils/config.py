# utils/config.py

# Motion detection thresholds, contour size, etc.
MOTION_THRESHOLD = 30
COOLDOWN_FRAMES = 15
MIN_CONTOUR_AREA = 5
MAX_CONTOUR_AREA = 100
NOISE_KERNEL = 3
STABILIZATION_WINDOW = 15

DEBUG_FRAMES_DIR = "bat_debug_frames"
MARKED_VIDEO_FILE = "bat_marked_output.avi"
HEATMAP_PNG_FILE = "bat_flight_heatmap.png"
HOTZONE_PNG_FILE = "bat_hotzone_map.png"
