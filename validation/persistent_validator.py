"""
Enhanced ValidationManager for persistent, repeatable manual validation
Supports multiple validation sessions per video with persistent state
"""

import os
import json
import csv
from datetime import datetime


class PersistentValidationManager:
    """
    Manages persistent validation state for repeatable manual validation sessions
    """
    
    def __init__(self, video_path, events=None):
        self.video_path = video_path
        self.events = events or []
        self.current_index = 0
        self.decisions = {}
        self.in_progress = False
        self.session_data = {}
        
        # Set up persistent storage
        self.setup_persistent_storage()
        
    def setup_persistent_storage(self):
        """Set up persistent storage files in video folder"""
        try:
            from utils.result_organizer import create_video_result_structure
            structure = create_video_result_structure(self.video_path)
            self.video_folder = structure["base"]
            
            # Define persistent files
            self.validation_state_file = os.path.join(self.video_folder, "validation_state.json")
            self.event_points_file = os.path.join(self.video_folder, "event_points.json")
            self.validation_log_file = os.path.join(self.video_folder, "validation_log.csv")
            
            # Load existing state if available
            self.load_validation_state()
            
        except Exception as e:
            print(f"[WARNING] Could not set up persistent storage: {e}")
            self.video_folder = None
    
    def load_validation_state(self):
        """Load validation state from persistent storage"""
        if os.path.exists(self.validation_state_file):
            try:
                with open(self.validation_state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.decisions = state.get('decisions', {})
                    self.session_data = state.get('session_data', {})
                    print(f"[INFO] Loaded validation state with {len(self.decisions)} decisions")
            except Exception as e:
                print(f"[WARNING] Could not load validation state: {e}")
    
    def save_validation_state(self):
        """Save current validation state to persistent storage"""
        if not self.video_folder:
            return
            
        try:
            state = {
                'decisions': self.decisions,
                'session_data': self.session_data,
                'last_updated': datetime.now().isoformat(),
                'video_path': self.video_path,
                'total_events': len(self.events)
            }
            
            with open(self.validation_state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"[WARNING] Could not save validation state: {e}")
    
    def load_event_points(self):
        """Load event points for fast replay"""
        if os.path.exists(self.event_points_file):
            try:
                with open(self.event_points_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARNING] Could not load event points: {e}")
        return {}
    
    def save_event_points(self, event_points):
        """Save event points for fast replay"""
        if not self.video_folder:
            return
            
        try:
            with open(self.event_points_file, 'w', encoding='utf-8') as f:
                json.dump(event_points, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[WARNING] Could not save event points: {e}")
    
    def log_validation_decision(self, event_index, decision, timestamp=None):
        """Log validation decision to CSV log"""
        if not self.video_folder:
            return
            
        timestamp = timestamp or datetime.now().isoformat()
        
        try:
            # Check if log file exists, create header if not
            write_header = not os.path.exists(self.validation_log_file)
            
            with open(self.validation_log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                if write_header:
                    writer.writerow([
                        'Timestamp', 'Event_Index', 'Decision', 'Start_Time', 
                        'End_Time', 'Duration', 'Center_X', 'Center_Y'
                    ])
                
                if event_index < len(self.events):
                    event = self.events[event_index]
                    writer.writerow([
                        timestamp,
                        event_index,
                        decision,
                        event.get('start_time', ''),
                        event.get('end_time', ''),
                        event.get('end_time', 0) - event.get('start_time', 0),
                        event.get('center_x', ''),
                        event.get('center_y', '')
                    ])
                    
        except Exception as e:
            print(f"[WARNING] Could not log validation decision: {e}")
    
    def start_validation_session(self, events=None):
        """Start a new validation session"""
        if events:
            self.events = events
            
        self.in_progress = True
        self.current_index = 0
        
        # Create new session entry
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_data[session_id] = {
            'start_time': datetime.now().isoformat(),
            'total_events': len(self.events),
            'validated_count': 0
        }
        
        print(f"[INFO] Started validation session {session_id} with {len(self.events)} events")
        return session_id
    
    def end_validation_session(self, session_id):
        """End current validation session"""
        self.in_progress = False
        
        if session_id in self.session_data:
            self.session_data[session_id]['end_time'] = datetime.now().isoformat()
            self.session_data[session_id]['validated_count'] = len(self.decisions)
        
        # Save state
        self.save_validation_state()
        print(f"[INFO] Ended validation session {session_id}")
    
    def reset_session_state(self):
        """Reset session state without clearing events or decisions"""
        self.current_index = 0
        self.in_progress = False
        print("[INFO] Reset validation session state")
    
    def get_validation_progress(self):
        """Get current validation progress"""
        total = len(self.events)
        validated = len(self.decisions)
        
        return {
            'total_events': total,
            'validated_events': validated,
            'remaining_events': total - validated,
            'progress_percent': (validated / total * 100) if total > 0 else 0,
            'current_index': self.current_index
        }
    
    def load_events_from_csv(self, csv_path=None):
        """Load events from CSV file if available"""
        if not csv_path and self.video_folder:
            # Look for CSV files in video folder
            csv_files = [f for f in os.listdir(self.video_folder) if f.endswith('.csv') and 'detections' in f]
            if csv_files:
                csv_path = os.path.join(self.video_folder, csv_files[0])
        
        if csv_path and os.path.exists(csv_path):
            try:
                events = []
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get('Start_Time') and row.get('End_Time'):
                            event = {
                                'start_time': float(row['Start_Time']),
                                'end_time': float(row['End_Time']),
                                'center_x': row.get('Center_X', ''),
                                'center_y': row.get('Center_Y', ''),
                                'duration': float(row.get('Duration', 0))
                            }
                            events.append(event)
                
                if events:
                    self.events = events
                    print(f"[INFO] Loaded {len(events)} events from CSV")
                    return True
                    
            except Exception as e:
                print(f"[WARNING] Could not load events from CSV: {e}")
        
        return False
    
    def export_validation_summary(self):
        """Export validation summary to video folder"""
        if not self.video_folder:
            return None
            
        summary_file = os.path.join(self.video_folder, "validation_summary.json")
        
        try:
            progress = self.get_validation_progress()
            
            summary = {
                'video_path': self.video_path,
                'validation_progress': progress,
                'decisions_summary': {
                    'total_decisions': len(self.decisions),
                    'approved': len([d for d in self.decisions.values() if d == 'approved']),
                    'rejected': len([d for d in self.decisions.values() if d == 'rejected']),
                    'skipped': len([d for d in self.decisions.values() if d == 'skipped'])
                },
                'session_history': self.session_data,
                'export_timestamp': datetime.now().isoformat()
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            return summary_file
            
        except Exception as e:
            print(f"[WARNING] Could not export validation summary: {e}")
            return None


class EventPointCapture:
    """
    Manages event point capture and fast replay functionality
    """
    
    def __init__(self, video_path):
        self.video_path = video_path
        self.setup_storage()
    
    def setup_storage(self):
        """Set up storage for event points"""
        try:
            from utils.result_organizer import create_video_result_structure
            structure = create_video_result_structure(self.video_path)
            self.video_folder = structure["base"]
            self.event_points_file = os.path.join(self.video_folder, "event_points.json")
        except Exception as e:
            print(f"[WARNING] Could not set up event points storage: {e}")
            self.video_folder = None
    
    def capture_event_points(self, events):
        """Capture event points with metadata for fast replay"""
        if not self.video_folder:
            return False
        
        try:
            event_points = {
                'video_path': self.video_path,
                'capture_timestamp': datetime.now().isoformat(),
                'total_events': len(events),
                'events': []
            }
            
            for i, event in enumerate(events):
                point_data = {
                    'index': i,
                    'start_frame': self.time_to_frame(event.get('start_time', 0)),
                    'end_frame': self.time_to_frame(event.get('end_time', 0)),
                    'start_time': event.get('start_time', 0),
                    'end_time': event.get('end_time', 0),
                    'duration': event.get('end_time', 0) - event.get('start_time', 0),
                    'center_x': event.get('center_x'),
                    'center_y': event.get('center_y'),
                    'event_type': event.get('event_type', 'detection'),
                    'metadata': {
                        'einflug_frame': self.time_to_frame(event.get('start_time', 0)),
                        'ausflug_frame': self.time_to_frame(event.get('end_time', 0)),
                        'roi_reference': event.get('roi_id'),
                        'polygon_reference': event.get('polygon_id')
                    }
                }
                event_points['events'].append(point_data)
            
            with open(self.event_points_file, 'w', encoding='utf-8') as f:
                json.dump(event_points, f, indent=2, ensure_ascii=False)
            
            print(f"[INFO] Captured {len(events)} event points")
            return True
            
        except Exception as e:
            print(f"[ERROR] Could not capture event points: {e}")
            return False
    
    def load_event_points(self):
        """Load captured event points for fast replay"""
        if not os.path.exists(self.event_points_file):
            return None
        
        try:
            with open(self.event_points_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Could not load event points: {e}")
            return None
    
    def time_to_frame(self, time_seconds, fps=30):
        """Convert time in seconds to frame number"""
        return int(time_seconds * fps)
    
    def frame_to_time(self, frame_number, fps=30):
        """Convert frame number to time in seconds"""
        return frame_number / fps
    
    def get_event_markers(self):
        """Get event markers for fast navigation"""
        event_points = self.load_event_points()
        if not event_points:
            return []
        
        markers = []
        for event in event_points.get('events', []):
            markers.append({
                'index': event['index'],
                'start_frame': event['start_frame'],
                'end_frame': event['end_frame'],
                'start_time': event['start_time'],
                'end_time': event['end_time'],
                'duration': event['duration'],
                'type': event.get('event_type', 'detection')
            })
        
        return markers
