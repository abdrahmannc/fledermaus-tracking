import cv2

def format_time(seconds):
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02}:{secs:02}"

def is_inside_roi(bat_center, roi):
    if not bat_center or not roi:
        return False
    x, y, w, h = roi
    cx, cy = bat_center
    return x <= cx <= x + w and y <= cy <= y + h


def validate_event(video_path, start_frame, end_frame, roi=None, bat_center=None):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    paused = False