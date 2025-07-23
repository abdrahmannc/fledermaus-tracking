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
       
    for frame_id in range(start_frame, end_frame + 1):
        if not paused:
            ret, frame = cap.read()
            if not ret:
                break

            # Timestamp
            timestamp = frame_id / fps
            time_str = format_time(timestamp)
            cv2.putText(frame, f"Time: {time_str}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Draw ROI box
            if roi:
                x, y, w, h = roi
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 0), 2)

            # Draw bat center circle always, red if inside ROI, gray otherwise
            if bat_center:
                color = (0, 0, 255) if is_inside_roi(bat_center, roi) else (200, 200, 200)
                cv2.circle(frame, bat_center, 10, color, 2)

                # Label if outside ROI
                if not is_inside_roi(bat_center, roi):
                    cv2.putText(frame, "Bat outside ROI", (bat_center[0] + 10, bat_center[1] - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

            cv2.imshow('Manual Validation (Y/N, SPACE = pause, Q = quit)', frame)
            
            
        key = cv2.waitKey(30) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('y'):
            print(f"Event confirmed at {time_str}.")
            cap.release()
            cv2.destroyAllWindows()
            return True
        elif key == ord('n'):
            print(f"Event rejected at {time_str}.")
            cap.release()
            cv2.destroyAllWindows()
            return False
        elif key == ord(' '):  # Pause/resume toggle
                paused = not paused

        cap.release()
        cv2.destroyAllWindows()
        return False