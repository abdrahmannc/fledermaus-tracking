# utils/config.py

# Motion detection thresholds, contour size, etc.
MOTION_THRESHOLD = 30
COOLDOWN_FRAMES = 15
MIN_CONTOUR_AREA = 5
MAX_CONTOUR_AREA = 100
NOISE_KERNEL = 3
STABILIZATION_WINDOW = 15

# ========== PERFORMANCE CONFIGURATION ==========

# Contour processing mode
# False = Sequential processing (default, faster for most cases)
# True = Parallel processing (may be faster for scenes with many contours)
USE_PARALLEL_CONTOUR = False

DEBUG_FRAMES_DIR = "bat_debug_frames"
MARKED_VIDEO_FILE = "bat_marked_output.avi"
HEATMAP_PNG_FILE = "bat_flight_heatmap.png"
HOTZONE_PNG_FILE = "bat_hotzone_map.png"

# ========== POLYGON VISUALIZATION CONFIGURATION ==========

# Polygon visualization colors (BGR format)
POLYGON_ACTIVE_COLOR = (0, 255, 0)      # Bright green for polygons with detected bats
POLYGON_INACTIVE_COLOR = (255, 255, 0)   # Yellow for monitoring polygons
POLYGON_OUTLINE_THICKNESS_ACTIVE = 3     # Line thickness for active polygon outlines
POLYGON_OUTLINE_THICKNESS_INACTIVE = 2   # Line thickness for inactive polygon outlines

# Polygon overlay settings
POLYGON_OVERLAY_ALPHA = 0.25             # Transparency for polygon fill overlays (0.0-1.0)
POLYGON_ENABLE_OVERLAY = True            # Enable/disable semi-transparent polygon fills
POLYGON_ENABLE_INFO_PANEL = True         # Enable/disable info panel with detection counts

# Bat detection visualization in polygons
BAT_DETECTION_COLOR = (0, 255, 0)        # Main bat detection circle color
BAT_CENTER_COLOR = (255, 255, 255)       # Bat center point color
BAT_CROSSHAIR_COLOR = (0, 0, 255)        # Crosshair color for precise center
BAT_DETECTION_RADIUS = 10                # Main detection circle radius
BAT_CENTER_RADIUS = 5                    # Center point radius
BAT_OUTER_RING_RADIUS = 15               # Outer detection ring radius

# Text and labeling
POLYGON_LABEL_FONT = 1                   # cv2.FONT_HERSHEY_SIMPLEX = 1
POLYGON_LABEL_SCALE = 0.8                # Font scale for polygon labels
POLYGON_LABEL_THICKNESS = 2              # Font thickness for polygon labels
BAT_LABEL_FONT = 1                       # Font for bat detection labels
BAT_LABEL_SCALE = 0.6                    # Font scale for bat labels
BAT_LABEL_THICKNESS = 2                  # Font thickness for bat labels

# Info panel settings
INFO_PANEL_BACKGROUND_COLOR = (0, 0, 0)  # Background color for info panel
INFO_PANEL_TEXT_COLOR = (255, 255, 255)  # Text color for info panel
INFO_PANEL_ALPHA = 0.7                   # Transparency for info panel background
INFO_PANEL_WIDTH = 250                   # Width of info panel
INFO_PANEL_POSITION = (10, 10)           # (x, y) position of info panel
