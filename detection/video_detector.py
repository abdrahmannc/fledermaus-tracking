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

    def load_video(self):
        self.video_path = filedialog.askopenfilename(
            title="Select IR Video File",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov"), ("All Files", "*.*")]
        )
        if not self.video_path:
            return
        self.cap = cv2.VideoCapture(self.video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        ret, frame = self.cap.read()
        if ret:
            frame_small = cv2.resize(frame, (640, 480))
            self.prev_gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
            self.gui.show_frame(frame_small)
            self.gui.update_status(f"Loaded: {os.path.basename(self.video_path)}")
            self.gui.btn_select_roi.config(state=tk.NORMAL)
        else:
            self.gui.update_status("Failed to read video")
        self.cap.release()
        self.cap = None

    def select_roi(self):
        cap = cv2.VideoCapture(self.video_path)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            raise RuntimeError("Failed to read frame for ROI selection.")
        r = cv2.selectROI("Select ROI (Drag rectangle, Enter to confirm)", frame, False, False)
        cv2.destroyAllWindows()
        if r and r[2] > 0 and r[3] > 0:
            self.roi = r
            return r
        else:
            return None

    def start_detection(self):
        if not self.video_path or not self.roi:
            self.gui.update_status("Video or ROI not set")
            return
        if self.processing:
            self.gui.update_status("Detection already running")
            return

        self.cap = cv2.VideoCapture(self.video_path)
        self.processing = True
        self.motion_history = []
        self.events = []
        self.marked_frames = []
        self.bat_centers = []
        self.cooldown_counter = 0
        self.bat_inside = False

        threading.Thread(target=self._process_video).start()

    def stop_detection(self):
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
                gray = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
                fgmask = self.back_sub.apply(gray)
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (NOISE_KERNEL, NOISE_KERNEL))
                fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)

                contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                motion_detected = False
                bat_center = None

                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if MIN_CONTOUR_AREA < area < MAX_CONTOUR_AREA:
                        M = cv2.moments(cnt)
                        if M["m00"] == 0:
                            continue
                        cx = int(M["m10"] / M["m00"]) + x
                        cy = int(M["m01"] / M["m00"]) + y
                        bat_center = (cx, cy)
                        motion_detected = True
                        break

                self.motion_history.append(motion_detected)
                if len(self.motion_history) > STABILIZATION_WINDOW:
                    self.motion_history.pop(0)
                stabilized_motion = sum(self.motion_history) > (STABILIZATION_WINDOW // 2)

                if self.cooldown_counter > 0:
                    self.cooldown_counter -= 1

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
                    self.gui.update_status(f"Bat entered at {frame_idx / self.fps:.2f}s")

                elif not stabilized_motion and self.bat_inside and self.cooldown_counter == 0:
                    self.bat_inside = False
                    exit_time = frame_idx / self.fps
                    if self.events:
                        self.events[-1]["exit"] = exit_time
                        self.events[-1]["duration"] = exit_time - self.events[-1]["entry"]
                    self.cooldown_counter = COOLDOWN_FRAMES
                    self.gui.update_status(f"Bat exited at {exit_time:.2f}s")

                marked = frame.copy()
                if bat_center:
                    cv2.circle(marked, bat_center, 7, (0, 255, 0), 2)
                    self.bat_centers.append(bat_center)
                cv2.rectangle(marked, (x, y), (x + w, y + h), (0, 255, 255), 1)
                self.marked_frames.append(marked)

        except Exception as e:
            self.gui.update_status(f"Error during detection: {str(e)}")
        finally:
            self.processing = False
            if self.cap:
                self.cap.release()
            self.gui.update_status(f"Detection finished, {len(self.events)} events detected")
            # NEW: Notify the GUI (thread-safe) that detection is done
            if hasattr(self.gui, 'on_detection_finished'):
                self.gui.root.after(0, self.gui.on_detection_finished)

    def export_marked_video(self):
        if not hasattr(self, "marked_frames") or not self.marked_frames:
            messagebox.showinfo("Export Video", "No frames to export")
            return
        export_video(self.marked_frames, self.fps, self.video_path)

    def is_inside_zone(self, x, y, zone_coords):
        x1, y1, x2, y2 = zone_coords
        return x1 <= x <= x2 and y1 <= y <= y2

    def analyze_tracks(self, tracks, zones):
        track_events = []
        for track in tracks:
            track_id = track["id"]
            points = track["points"]
            zone_status = {zone["id"]: False for zone in zones}
            for frame_id, x, y in points:
                for zone in zones:
                    inside = self.is_inside_zone(x, y, zone["coords"])
                    zone_id = zone["id"]
                    if inside and not zone_status[zone_id]:
                        track_events.append({
                            "track_id": track_id,
                            "frame": frame_id,
                            "zone": zone_id,
                            "event": "entered"
                        })
                        zone_status[zone_id] = True
                    elif not inside and zone_status[zone_id]:
                        track_events.append({
                            "track_id": track_id,
                            "frame": frame_id,
                            "zone": zone_id,
                            "event": "exited",
                        })
                        zone_status[zone_id] = False
        return track_events

    def compute_dwell_times(events):
        dwell_dict = defaultdict(dict)
        dwell_results = []
        for e in events:
            tid = e["track_id"]
            z = e["zone"]
            if e["event"] == "entered":
                dwell_dict[tid][z] = e["frame"]
            elif e["event"] == "exited" and z in dwell_dict[tid]:
                duration = e["frame"] - dwell_dict[tid][z]
                dwell_results.append({
                    "track_id": tid,
                    "zone": z,
                    "dwell_frames": duration
                })
                del dwell_dict[tid][z]
        return dwell_results



    def export_results(self):
        if not self.events:
            messagebox.showinfo("Export Results", "No events to export.")
            return

        # Extract base video name without extension
        video_name = os.path.splitext(os.path.basename(self.video_path))[0]
        
        # Get today's date
        today_str = datetime.today().strftime('%Y-%m-%d')

        # Construct filename
        csv_filename = f"{video_name}_{today_str}.csv"
        csv_path = os.path.join(os.path.dirname(self.video_path), csv_filename)

        # Export the data
        export_events_to_csv(self.events, self.video_path, csv_path)

        # Notify user
        messagebox.showinfo("Export Results", f"Events exported successfully to:\n{csv_path}")
            
        

    def export_flightMap(self):
        if not self.bat_centers or not self.events:
            messagebox.showinfo("Export Flight Map", "No bat trajectory data available.")
            return
        fps = 15
        bat_paths_with_time = {
            1: [(i / fps, pos[0], pos[1]) for i, pos in enumerate(self.bat_centers)]
        }
        output_dir = os.path.join(os.path.dirname(self.video_path), "exports")
        os.makedirs(output_dir, exist_ok=True)
        filename_base = os.path.splitext(os.path.basename(self.video_path))[0]
        img_path = export_flightMap(bat_paths_with_time, output_dir, filename_base=filename_base, user="IfAÖ")
        if img_path:
            messagebox.showinfo("Export Flight Map", f"Flight map saved:\n{img_path}")
        else:
            messagebox.showinfo("Export Flight Map", "Failed to generate flight map.")


    def export_hotzone(self):
        print("Exporting hotzone...")

    def filter_events_by_roi(self):
        if not self.roi:
            print("[WARNING] No ROI set for filtering.")
            return
        x, y, w, h = self.roi
        x2, y2 = x + w, y + h
        filtered_events = []
        for idx, event in enumerate(self.events):
            center = event.get("bat_center")
            if center:
                cx, cy = center
                if x <= cx <= x2 and y <= cy <= y2:
                    filtered_events.append(event)
                else:
                    print(f"[INFO] Event #{idx} filtered out: outside ROI.")
            else:
                print(f"[WARNING] Event #{idx} has no bat_center, skipping.")
        print(f"[INFO] Filtered {len(self.events) - len(filtered_events)} events outside ROI.")
        self.events = filtered_events

    def run_manual_validation(self):
        validated_events = []
        for idx, event in enumerate(self.events):
            if 'frame_idx' not in event:
                print(f"[WARNING] Event #{idx} missing 'frame_idx': {event}")
                continue
            frame_idx = event['frame_idx']
            print(f"[INFO] Validating event at frame {frame_idx}")
            is_valid = validate_event(self.video_path, frame_idx - 15, frame_idx + 15, roi=event.get("roi"))
            if is_valid:
                event['validated'] = True
                event['validated_frame'] = frame_idx
                validated_events.append(event)
            else:
                print(f"[INFO] Event at frame {frame_idx} was rejected.")
        print(f"[INFO] Validation complete. {len(validated_events)} out of {len(self.events)} events retained.")
        self.events = validated_events

    def get_events(self):
        """
        Return a list of events with entry, exit, and duration (in seconds).
        Only include events that have both entry and exit.
        """
        return [
            {
                "entry": ev["entry"],
                "exit": ev["exit"],
                "duration": ev["duration"]
            }
            for ev in self.events
            if ev.get("entry") is not None and ev.get("exit") is not None and ev.get("duration") is not None
        ]
    
    

    def load_previous_results(self):
        """Load and display previous analysis results"""
        try:
            # Get the directory containing videos
            if self.video_path:
                base_dir = os.path.dirname(self.video_path)
            else:
                # If no video is loaded, ask user for directory
                base_dir = filedialog.askdirectory(title="Select folder with analysis results")
                if not base_dir:
                    return
                
            # Look for CSV result files
            csv_files = glob.glob(os.path.join(base_dir, "*.csv"))
            
            if not csv_files:
                messagebox.showinfo("Previous Results", "No analysis results found in this directory.")
                return
                
            # Create a simple dialog to show available results
            results_window = tk.Toplevel(self.gui.root)
            results_window.title("Previous Analysis Results")
            results_window.geometry("600x400")
            
            # Create a listbox to display results
            results_frame = tk.Frame(results_window)
            results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            label = tk.Label(results_frame, text="Select a result file to view:")
            label.pack(anchor=tk.W, pady=(0, 5))
            
            listbox = tk.Listbox(results_frame, width=80, height=15)
            listbox.pack(fill=tk.BOTH, expand=True)
            
            # Add scrollbar
            scrollbar = tk.Scrollbar(listbox)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=listbox.yview)
            
            # Add files to listbox
            for csv_file in csv_files:
                file_info = f"{os.path.basename(csv_file)}"
                listbox.insert(tk.END, file_info)
                
            # Function to view selected result
            def view_selected_result():
                selection = listbox.curselection()
                if selection:
                    selected_file = csv_files[selection[0]]
                    self.display_csv_results(selected_file)
                    
            # Add button to view selected result
            view_button = tk.Button(results_frame, text="View Selected Result", command=view_selected_result)
            view_button.pack(pady=10)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load previous results: {str(e)}")





    def display_csv_results(self, csv_file):
        """Display the contents of a CSV result file"""
        try:
            # Read CSV file with basic Python
            import csv
            
            # Create a new window to display results
            result_window = tk.Toplevel(self.gui.root)
            result_window.title(f"Results: {os.path.basename(csv_file)}")
            result_window.geometry("800x600")
            
            # Create a frame for the results
            frame = tk.Frame(result_window)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Create text widget to display CSV content
            text = tk.Text(frame, wrap=tk.NONE)
            text.pack(fill=tk.BOTH, expand=True)
            
            # Add scrollbars
            yscroll = tk.Scrollbar(text, command=text.yview)
            yscroll.pack(side=tk.RIGHT, fill=tk.Y)
            xscroll = tk.Scrollbar(frame, command=text.xview, orient=tk.HORIZONTAL)
            xscroll.pack(side=tk.BOTTOM, fill=tk.X)
            text.config(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
            
            # Read and display the CSV data
            with open(csv_file, 'r') as f:
                csv_reader = csv.reader(f)
                headers = next(csv_reader)  # Get header row
                
                # Format and insert the headers
                header = "\t".join(headers)
                text.insert(tk.END, header + "\n")
                text.insert(tk.END, "-" * len(header) + "\n")
                
                # Insert data rows
                for row in csv_reader:
                    line = "\t".join(row)
                    text.insert(tk.END, line + "\n")
                
            # Add button to load associated video
            video_base = os.path.basename(csv_file).split("_")[0]
            video_dir = os.path.dirname(csv_file)
            
            # Look for possible video files
            video_files = []
            for ext in ['.avi', '.mp4', '.mov']:
                possible_file = os.path.join(video_dir, video_base + ext)
                if os.path.exists(possible_file):
                    video_files.append(possible_file)
            
            def load_associated_video():
                if video_files:
                    self.video_path = video_files[0]  # Take the first matching video
                    self.cap = cv2.VideoCapture(self.video_path)
                    self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
                    self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    self.gui.update_status(f"Loaded: {os.path.basename(self.video_path)}")
                    self.cap.release()
                    self.cap = None
                else:
                    messagebox.showinfo("Video Not Found", f"Could not find associated video file for {os.path.basename(csv_file)}")
            
            if video_files:
                load_button = tk.Button(frame, text="Load Associated Video", command=load_associated_video)
                load_button.pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display results: {str(e)}")