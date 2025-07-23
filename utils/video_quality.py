import cv2
import numpy as np



def analyze_video_quality(video_path, sample_frames=30):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"error": "Cannot open video"}

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    brightness_list = []
    contrast_list = []
    motion_diffs = []
    brightness_series = []
    noise_estimates = []

    high_motion_timestamps = []  # Store times (in seconds) of high camera motion
    motion_threshold = 20

    prev_gray = None
    sample_step = max(1, frame_count // sample_frames)

    for i in range(0, frame_count, sample_step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        brightness = np.mean(gray)
        contrast = np.std(gray)
        brightness_list.append(brightness)
        contrast_list.append(contrast)
        brightness_series.append(brightness)

        # Motion estimation
        if prev_gray is not None:
            diff = cv2.absdiff(gray, prev_gray)
            motion = np.mean(diff)
            motion_diffs.append(motion)

            if motion > motion_threshold:
                timestamp_sec = i / fps
                high_motion_timestamps.append(round(timestamp_sec, 2))  # Round for clarity

        prev_gray = gray

        # Noise estimation
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        noise_estimates.append(laplacian_var)

    cap.release()

    # Metrics
    avg_brightness = np.mean(brightness_list) if brightness_list else 0
    avg_contrast = np.mean(contrast_list) if contrast_list else 0
    avg_motion = np.mean(motion_diffs) if motion_diffs else 0
    brightness_std = np.std(brightness_series) if brightness_series else 0
    avg_noise = np.mean(noise_estimates) if noise_estimates else 0

    # Warnung
    warnings = []
    if avg_motion > motion_threshold:
        warnings.append("⚠️ Hohe Kamerabewegung erkannt.")
    if brightness_std > 15:
        warnings.append("⚠️ Beleuchtung ist instabil.")
    if avg_noise > 1000:
        warnings.append("⚠️ Hohes Bildrauschen (kann die Erkennung beeinträchtigen).")

    if warnings:
        warnings.append("Diese Probleme können jedoch behandelt werden.")

    # Convert all high motion timestamps to minute format
    high_motion_minutes = [round(ts / 60, 2) for ts in high_motion_timestamps]

    return {
        "fps": fps,
        "avg_brightness": avg_brightness,
        "avg_contrast": avg_contrast,
        "avg_motion": avg_motion,
        "brightness_std": brightness_std,
        "avg_noise": avg_noise,
        "warnings": warnings,
        "high_motion_timestamps": high_motion_timestamps,
        "high_motion_minutes": high_motion_minutes 
    }
