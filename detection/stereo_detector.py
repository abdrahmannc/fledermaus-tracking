"""
Teil 3: 3D Stereo Bat Detection Module

This module extends the existing 2D detection system with stereoscopic 3D capabilities
while maintaining full compatibility with existing workflows.
"""

import cv2
import numpy as np
import threading
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import json
from datetime import datetime

from .video_detector import VideoDetector
from utils.config import MIN_CONTOUR_AREA, MAX_CONTOUR_AREA, NOISE_KERNEL


@dataclass
class StereoCalibration:
    """Stereo camera calibration parameters"""
    camera_matrix_left: np.ndarray
    camera_matrix_right: np.ndarray
    dist_coeffs_left: np.ndarray
    dist_coeffs_right: np.ndarray
    rotation_matrix: np.ndarray
    translation_vector: np.ndarray
    essential_matrix: np.ndarray
    fundamental_matrix: np.ndarray
    rectification_left: np.ndarray
    rectification_right: np.ndarray
    projection_left: np.ndarray
    projection_right: np.ndarray
    disparity_to_depth_matrix: np.ndarray
    roi_left: Tuple[int, int, int, int]
    roi_right: Tuple[int, int, int, int]


@dataclass
class Point3D:
    """3D point representation"""
    x: float
    y: float
    z: float
    confidence: float = 1.0
    timestamp: float = 0.0
    frame_idx: int = 0


@dataclass
class StereoEvent:
    """Extended event structure for 3D detection"""
    # 2D compatibility fields (preserve existing interface)
    entry: float
    exit: float
    duration: float
    frame_idx: int
    bat_center: Tuple[int, int]  # 2D center for compatibility
    
    # 3D-specific fields
    position_3d: Optional[Point3D] = None
    trajectory_3d: List[Point3D] = None
    depth_confidence: float = 0.0
    stereo_disparity: float = 0.0
    
    # Metadata
    detection_mode: str = "2d"  # "2d", "3d", or "hybrid"
    stereo_frame_pair: Optional[Tuple[np.ndarray, np.ndarray]] = None


class StereoDetector:
    """
    3D Stereo detection system that extends VideoDetector functionality
    without breaking existing interfaces.
    """
    
    def __init__(self, gui, mode="2d"):
        # Initialize base 2D detector for compatibility
        self.base_detector = VideoDetector(gui)
        self.gui = gui
        self.mode = mode  # "2d", "3d", or "hybrid"
        
        # Stereo-specific attributes
        self.left_video_path = None
        self.right_video_path = None
        self.calibration = None
        self.stereo_matcher = None
        
        # 3D data storage
        self.stereo_events = []
        self.point_cloud_data = []
        self.trajectory_3d = []
        
        # Processing state
        self.stereo_processing = False
        self.depth_estimation_enabled = False
        
        # Delegate 2D functionality to base detector
        self._setup_compatibility_layer()
    
    def _setup_compatibility_layer(self):
        """Setup compatibility layer to preserve existing interfaces"""
        # Delegate all 2D methods to base detector
        for attr_name in dir(self.base_detector):
            if not attr_name.startswith('_') and callable(getattr(self.base_detector, attr_name)):
                if not hasattr(self, attr_name):
                    setattr(self, attr_name, getattr(self.base_detector, attr_name))
        
        # Override properties to point to base detector
        self.events = self.base_detector.events
        self.marked_frames = self.base_detector.marked_frames
        self.event_frames = self.base_detector.event_frames
        self.video_path = self.base_detector.video_path
        self.roi = self.base_detector.roi
        self.polygon_areas = self.base_detector.polygon_areas
    
    def load_stereo_videos(self, left_path: str, right_path: str) -> bool:
        """Load synchronized stereo video pair"""
        try:
            self.left_video_path = left_path
            self.right_video_path = right_path
            
            # Validate video compatibility
            if not self._validate_stereo_pair():
                return False
            
            # Set primary video path for 2D compatibility
            self.base_detector.video_path = left_path
            self.base_detector.load_video()
            
            self.gui.update_status(f"Stereo videos loaded: {os.path.basename(left_path)} | {os.path.basename(right_path)}")
            return True
            
        except Exception as e:
            self.gui.update_status(f"Error loading stereo videos: {str(e)}")
            return False
    
    def _validate_stereo_pair(self) -> bool:
        """Validate that stereo videos are compatible"""
        try:
            cap_left = cv2.VideoCapture(self.left_video_path)
            cap_right = cv2.VideoCapture(self.right_video_path)
            
            # Check frame counts
            frames_left = int(cap_left.get(cv2.CAP_PROP_FRAME_COUNT))
            frames_right = int(cap_right.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Check frame rates
            fps_left = cap_left.get(cv2.CAP_PROP_FPS)
            fps_right = cap_right.get(cv2.CAP_PROP_FPS)
            
            # Check resolutions
            width_left = int(cap_left.get(cv2.CAP_PROP_FRAME_WIDTH))
            height_left = int(cap_left.get(cv2.CAP_PROP_FRAME_HEIGHT))
            width_right = int(cap_right.get(cv2.CAP_PROP_FRAME_WIDTH))
            height_right = int(cap_right.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            cap_left.release()
            cap_right.release()
            
            # Validate compatibility
            if abs(frames_left - frames_right) > 5:  # Allow small difference
                raise ValueError(f"Frame count mismatch: L={frames_left}, R={frames_right}")
            
            if abs(fps_left - fps_right) > 0.1:
                raise ValueError(f"FPS mismatch: L={fps_left}, R={fps_right}")
            
            if width_left != width_right or height_left != height_right:
                raise ValueError(f"Resolution mismatch: L={width_left}x{height_left}, R={width_right}x{height_right}")
            
            return True
            
        except Exception as e:
            self.gui.update_status(f"Stereo validation failed: {str(e)}")
            return False
    
    def load_calibration(self, calibration_path: str) -> bool:
        """Load stereo camera calibration from file"""
        try:
            with open(calibration_path, 'r') as f:
                calib_data = json.load(f)
            
            self.calibration = StereoCalibration(
                camera_matrix_left=np.array(calib_data['camera_matrix_left']),
                camera_matrix_right=np.array(calib_data['camera_matrix_right']),
                dist_coeffs_left=np.array(calib_data['dist_coeffs_left']),
                dist_coeffs_right=np.array(calib_data['dist_coeffs_right']),
                rotation_matrix=np.array(calib_data['rotation_matrix']),
                translation_vector=np.array(calib_data['translation_vector']),
                essential_matrix=np.array(calib_data['essential_matrix']),
                fundamental_matrix=np.array(calib_data['fundamental_matrix']),
                rectification_left=np.array(calib_data['rectification_left']),
                rectification_right=np.array(calib_data['rectification_right']),
                projection_left=np.array(calib_data['projection_left']),
                projection_right=np.array(calib_data['projection_right']),
                disparity_to_depth_matrix=np.array(calib_data['disparity_to_depth_matrix']),
                roi_left=tuple(calib_data['roi_left']),
                roi_right=tuple(calib_data['roi_right'])
            )
            
            # Initialize stereo matcher
            self._initialize_stereo_matcher()
            
            self.gui.update_status("Stereo calibration loaded successfully")
            return True
            
        except Exception as e:
            self.gui.update_status(f"Error loading calibration: {str(e)}")
            return False
    
    def _initialize_stereo_matcher(self):
        """Initialize stereo matching algorithm"""
        # Use SGBM for better quality
        self.stereo_matcher = cv2.StereoSGBM_create(
            minDisparity=0,
            numDisparities=64,  # Must be divisible by 16
            blockSize=11,
            P1=8 * 3 * 11**2,
            P2=32 * 3 * 11**2,
            disp12MaxDiff=1,
            uniquenessRatio=15,
            speckleWindowSize=0,
            speckleRange=2,
            preFilterCap=63,
            mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
        )
    
    def set_detection_mode(self, mode: str):
        """Set detection mode: 2d, 3d, or hybrid"""
        if mode not in ["2d", "3d", "hybrid"]:
            raise ValueError("Mode must be '2d', '3d', or 'hybrid'")
        
        self.mode = mode
        self.gui.update_status(f"Detection mode set to: {mode.upper()}")
    
    def start_stereo_detection(self):
        """Start 3D stereo detection process"""
        if self.mode == "2d":
            # Fallback to 2D detection
            return self.base_detector.start_detection()
        
        if not self.left_video_path or not self.right_video_path:
            self.gui.update_status("Stereo videos not loaded")
            return
        
        if not self.calibration:
            self.gui.update_status("Stereo calibration not loaded")
            return
        
        self.stereo_processing = True
        self.stereo_events = []
        
        # Start stereo processing in separate thread
        threading.Thread(target=self._process_stereo_video, daemon=True).start()
    
    def _process_stereo_video(self):
        """Process synchronized stereo video for 3D detection"""
        try:
            cap_left = cv2.VideoCapture(self.left_video_path)
            cap_right = cv2.VideoCapture(self.right_video_path)
            
            # Get video properties
            fps = cap_left.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap_left.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Initialize background subtractors for both cameras
            back_sub_left = cv2.createBackgroundSubtractorMOG2()
            back_sub_right = cv2.createBackgroundSubtractorMOG2()
            
            frame_idx = 0
            
            while self.stereo_processing:
                ret_left, frame_left = cap_left.read()
                ret_right, frame_right = cap_right.read()
                
                if not ret_left or not ret_right:
                    break
                
                frame_idx += 1
                
                # Progress update
                progress = (frame_idx / total_frames) * 100
                self.gui.root.after(0, lambda: self.gui.update_status(
                    f"3D Processing: {progress:.1f}% (Frame {frame_idx}/{total_frames})"
                ))
                
                # Process stereo frame pair
                self._process_stereo_frame_pair(
                    frame_left, frame_right, frame_idx, fps,
                    back_sub_left, back_sub_right
                )
            
            cap_left.release()
            cap_right.release()
            
            # Convert stereo events to 2D-compatible format for existing GUI
            self._convert_stereo_events_to_2d()
            
            self.gui.root.after(0, lambda: self.gui.update_status(
                f"3D Detection completed: {len(self.stereo_events)} stereo events detected"
            ))
            
        except Exception as e:
            self.gui.root.after(0, lambda: self.gui.update_status(f"3D Detection error: {str(e)}"))
        finally:
            self.stereo_processing = False
    
    def _process_stereo_frame_pair(self, frame_left, frame_right, frame_idx, fps, back_sub_left, back_sub_right):
        """Process a synchronized stereo frame pair for 3D detection"""
        # Apply rectification if calibration is available
        if self.calibration:
            # Create rectification maps if not done
            if not hasattr(self, '_map_left_x'):
                h, w = frame_left.shape[:2]
                self._map_left_x, self._map_left_y = cv2.initUndistortRectifyMap(
                    self.calibration.camera_matrix_left,
                    self.calibration.dist_coeffs_left,
                    self.calibration.rectification_left,
                    self.calibration.projection_left,
                    (w, h), cv2.CV_16SC2
                )
                self._map_right_x, self._map_right_y = cv2.initUndistortRectifyMap(
                    self.calibration.camera_matrix_right,
                    self.calibration.dist_coeffs_right,
                    self.calibration.rectification_right,
                    self.calibration.projection_right,
                    (w, h), cv2.CV_16SC2
                )
            
            # Rectify frames
            frame_left = cv2.remap(frame_left, self._map_left_x, self._map_left_y, cv2.INTER_LINEAR)
            frame_right = cv2.remap(frame_right, self._map_right_x, self._map_right_y, cv2.INTER_LINEAR)
        
        # Apply ROI if set (use existing ROI system)
        if self.roi:
            x, y, w, h = self.roi
            roi_left = frame_left[y:y+h, x:x+w]
            roi_right = frame_right[y:y+h, x:x+w]
        else:
            roi_left = frame_left
            roi_right = frame_right
        
        # Convert to grayscale for motion detection
        gray_left = cv2.cvtColor(roi_left, cv2.COLOR_BGR2GRAY)
        gray_right = cv2.cvtColor(roi_right, cv2.COLOR_BGR2GRAY)
        
        # Apply background subtraction
        fgmask_left = back_sub_left.apply(gray_left)
        fgmask_right = back_sub_right.apply(gray_right)
        
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (NOISE_KERNEL, NOISE_KERNEL))
        fgmask_left = cv2.morphologyEx(fgmask_left, cv2.MORPH_OPEN, kernel)
        fgmask_right = cv2.morphologyEx(fgmask_right, cv2.MORPH_OPEN, kernel)
        
        # Find contours in both images
        contours_left, _ = cv2.findContours(fgmask_left, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours_right, _ = cv2.findContours(fgmask_right, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find matching detections between left and right cameras
        stereo_detections = self._match_stereo_detections(
            contours_left, contours_right, frame_idx, fps, gray_left, gray_right
        )
        
        # Store detections
        for detection in stereo_detections:
            self.stereo_events.append(detection)
    
    def _match_stereo_detections(self, contours_left, contours_right, frame_idx, fps, gray_left, gray_right):
        """Match detections between left and right camera views"""
        detections = []
        
        for cnt_left in contours_left:
            area_left = cv2.contourArea(cnt_left)
            if not (MIN_CONTOUR_AREA < area_left < MAX_CONTOUR_AREA):
                continue
            
            # Get centroid of left detection
            M_left = cv2.moments(cnt_left)
            if M_left["m00"] == 0:
                continue
                
            cx_left = int(M_left["m10"] / M_left["m00"])
            cy_left = int(M_left["m01"] / M_left["m00"])
            
            # Look for corresponding detection in right image
            best_match = None
            best_distance = float('inf')
            
            for cnt_right in contours_right:
                area_right = cv2.contourArea(cnt_right)
                if not (MIN_CONTOUR_AREA < area_right < MAX_CONTOUR_AREA):
                    continue
                
                M_right = cv2.moments(cnt_right)
                if M_right["m00"] == 0:
                    continue
                    
                cx_right = int(M_right["m10"] / M_right["m00"])
                cy_right = int(M_right["m01"] / M_right["m00"])
                
                # Check if y-coordinates are similar (epipolar constraint)
                y_diff = abs(cy_left - cy_right)
                if y_diff > 10:  # Allow some tolerance
                    continue
                
                # Check if right detection is to the left of left detection (disparity > 0)
                if cx_right >= cx_left:
                    continue
                
                # Calculate matching score
                area_diff = abs(area_left - area_right) / max(area_left, area_right)
                distance = area_diff + y_diff * 0.1
                
                if distance < best_distance:
                    best_distance = distance
                    best_match = (cx_right, cy_right, area_right)
            
            # If we found a good match, calculate 3D position
            if best_match and best_distance < 0.5:  # Threshold for good match
                cx_right, cy_right, area_right = best_match
                
                # Calculate disparity
                disparity = cx_left - cx_right
                
                if disparity > 0:  # Valid disparity
                    # Calculate 3D position if calibration is available
                    position_3d = None
                    if self.calibration:
                        position_3d = self._calculate_3d_position(cx_left, cy_left, disparity)
                    
                    # Create stereo event
                    stereo_event = StereoEvent(
                        entry=frame_idx / fps,
                        exit=frame_idx / fps,  # Will be updated when tracking
                        duration=0.0,
                        frame_idx=frame_idx,
                        bat_center=(cx_left, cy_left),  # 2D compatibility
                        position_3d=position_3d,
                        trajectory_3d=[],
                        depth_confidence=1.0 / (1.0 + best_distance),
                        stereo_disparity=disparity,
                        detection_mode="3d",
                        stereo_frame_pair=(gray_left.copy(), gray_right.copy())
                    )
                    
                    detections.append(stereo_event)
        
        return detections
    
    def _calculate_3d_position(self, x, y, disparity) -> Point3D:
        """Calculate 3D world coordinates from disparity"""
        if not self.calibration or disparity <= 0:
            return None
        
        # Convert to homogeneous coordinates
        point_2d = np.array([x, y, disparity, 1.0])
        
        # Transform to 3D using disparity-to-depth matrix
        point_3d_homogeneous = self.calibration.disparity_to_depth_matrix.dot(point_2d)
        
        # Convert from homogeneous coordinates
        if point_3d_homogeneous[3] != 0:
            point_3d = point_3d_homogeneous[:3] / point_3d_homogeneous[3]
            
            return Point3D(
                x=float(point_3d[0]),
                y=float(point_3d[1]),
                z=float(point_3d[2]),
                confidence=1.0,
                timestamp=0.0,
                frame_idx=0
            )
        
        return None
    
    def _convert_stereo_events_to_2d(self):
        """Convert stereo events to 2D format for compatibility with existing GUI"""
        # Clear existing events and replace with stereo events
        self.base_detector.events = []
        
        for stereo_event in self.stereo_events:
            # Create 2D-compatible event
            event_2d = {
                "entry": stereo_event.entry,
                "einflugzeit": stereo_event.entry,
                "exit": stereo_event.exit,
                "ausflugzeit": stereo_event.exit,
                "duration": stereo_event.duration,
                "dauer": stereo_event.duration,
                "frame_idx": stereo_event.frame_idx,
                "bat_center": stereo_event.bat_center,
                "event_id": len(self.base_detector.events),
                
                # Add 3D metadata without breaking 2D interface
                "position_3d": stereo_event.position_3d.__dict__ if stereo_event.position_3d else None,
                "depth_confidence": stereo_event.depth_confidence,
                "stereo_disparity": stereo_event.stereo_disparity,
                "detection_mode": stereo_event.detection_mode
            }
            
            self.base_detector.events.append(event_2d)
    
    def get_3d_trajectory_data(self) -> List[Dict]:
        """Get 3D trajectory data for visualization"""
        trajectory_data = []
        
        for event in self.stereo_events:
            if event.position_3d:
                trajectory_data.append({
                    'frame_idx': event.frame_idx,
                    'timestamp': event.entry,
                    'x': event.position_3d.x,
                    'y': event.position_3d.y, 
                    'z': event.position_3d.z,
                    'confidence': event.depth_confidence
                })
        
        return trajectory_data
    
    def export_3d_data(self, output_path: str, format_type: str = "json"):
        """Export 3D detection data in various formats"""
        if format_type == "json":
            self._export_3d_json(output_path)
        elif format_type == "ply":
            self._export_3d_ply(output_path)
        elif format_type == "csv":
            self._export_3d_csv(output_path)
    
    def _export_3d_json(self, output_path: str):
        """Export 3D data as JSON"""
        data = {
            "metadata": {
                "detection_mode": self.mode,
                "left_video": self.left_video_path,
                "right_video": self.right_video_path,
                "calibration_loaded": self.calibration is not None,
                "export_timestamp": datetime.now().isoformat(),
                "total_events": len(self.stereo_events)
            },
            "events": []
        }
        
        for i, event in enumerate(self.stereo_events):
            event_data = {
                "event_id": i,
                "entry_time": event.entry,
                "exit_time": event.exit,
                "duration": event.duration,
                "frame_idx": event.frame_idx,
                "detection_2d": {
                    "x": event.bat_center[0],
                    "y": event.bat_center[1]
                },
                "detection_3d": None,
                "depth_confidence": event.depth_confidence,
                "stereo_disparity": event.stereo_disparity
            }
            
            if event.position_3d:
                event_data["detection_3d"] = {
                    "x": event.position_3d.x,
                    "y": event.position_3d.y,
                    "z": event.position_3d.z,
                    "confidence": event.position_3d.confidence
                }
            
            data["events"].append(event_data)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _export_3d_csv(self, output_path: str):
        """Export 3D data as CSV"""
        import csv
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Event_ID', 'Entry_Time', 'Exit_Time', 'Duration', 'Frame_Idx',
                'X_2D', 'Y_2D', 'X_3D', 'Y_3D', 'Z_3D', 'Depth_Confidence', 'Disparity'
            ])
            
            # Data rows
            for i, event in enumerate(self.stereo_events):
                row = [
                    i, event.entry, event.exit, event.duration, event.frame_idx,
                    event.bat_center[0], event.bat_center[1]
                ]
                
                if event.position_3d:
                    row.extend([
                        event.position_3d.x, event.position_3d.y, event.position_3d.z
                    ])
                else:
                    row.extend([None, None, None])
                
                row.extend([event.depth_confidence, event.stereo_disparity])
                writer.writerow(row)
    
    def _export_3d_ply(self, output_path: str):
        """Export 3D point cloud as PLY file"""
        points_3d = []
        
        for event in self.stereo_events:
            if event.position_3d:
                points_3d.append([
                    event.position_3d.x,
                    event.position_3d.y, 
                    event.position_3d.z
                ])
        
        if not points_3d:
            return
        
        with open(output_path, 'w') as f:
            f.write("ply\n")
            f.write("format ascii 1.0\n")
            f.write(f"element vertex {len(points_3d)}\n")
            f.write("property float x\n")
            f.write("property float y\n")
            f.write("property float z\n")
            f.write("end_header\n")
            
            for point in points_3d:
                f.write(f"{point[0]} {point[1]} {point[2]}\n")
