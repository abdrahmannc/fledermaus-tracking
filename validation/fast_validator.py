#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Fast Validation System for Bat Tracking Application
Provides motion visualization and interactive thumbnails for rapid event validation
"""

import cv2
import numpy as np
import tkinter as tk
from datetime import datetime

def is_valid_frame(frame):
    """Safely check if frame is a valid numpy array"""
    return frame is not None and hasattr(frame, 'shape') and frame.size > 0
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
from datetime import datetime


class MotionAnalyzer:
    """Analyzes motion patterns and generates heatmaps for events"""
    
    def __init__(self, video_path):
        self.video_path = video_path
        self.motion_cache = {}
        
    def analyze_event_motion(self, event, roi_areas=None):
        """Analyze motion patterns for a specific event"""
        try:
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                return None
                
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            
            # Safe handling of entry/exit times
            start_time = event.get('entry') or event.get('einflugzeit') or 0
            end_time = event.get('exit') or event.get('ausflugzeit')
            
            # Handle missing exit time
            if end_time is None:
                end_time = start_time + 1  # Default 1 second duration
                
            start_frame = int(start_time * fps)
            end_frame = int(end_time * fps)
            
            # Initialize motion detection
            motion_data = {
                'heatmap': None,
                'motion_intensity': 0,
                'movement_path': [],
                'key_frames': [],
                'has_valid_times': start_time is not None and end_time is not None
            }
            
            # Background subtractor for motion detection
            backSub = cv2.createBackgroundSubtractorMOG2()
            
            # Motion accumulation heatmap
            motion_accumulator = None
            frame_count = 0
            
            for frame_idx in range(start_frame, min(end_frame + 1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if not ret:
                    break
                    
                frame_count += 1
                
                # Apply ROI mask if specified
                if roi_areas:
                    mask = self.create_roi_mask(frame.shape[:2], roi_areas)
                    frame_masked = cv2.bitwise_and(frame, frame, mask=mask)
                else:
                    frame_masked = frame
                
                # Detect motion
                fg_mask = backSub.apply(frame_masked)
                
                # Initialize motion accumulator
                if motion_accumulator is None:
                    motion_accumulator = np.zeros(fg_mask.shape, dtype=np.float32)
                
                # Accumulate motion
                motion_accumulator += fg_mask.astype(np.float32) / 255.0
                
                # Store key frames (start, middle, end)
                if frame_idx in [start_frame, (start_frame + end_frame) // 2, end_frame]:
                    motion_data['key_frames'].append({
                        'frame_idx': frame_idx,
                        'timestamp': frame_idx / fps,
                        'frame': frame.copy()
                    })
                
                # Track movement center
                contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    largest_contour = max(contours, key=cv2.contourArea)
                    if cv2.contourArea(largest_contour) > 5:  # Minimum area threshold
                        M = cv2.moments(largest_contour)
                        if M["m00"] != 0:
                            cx = int(M["m10"] / M["m00"])
                            cy = int(M["m01"] / M["m00"])
                            motion_data['movement_path'].append((cx, cy))
            
            cap.release()
            
            # Generate heatmap
            if motion_accumulator is not None and frame_count > 0:
                # Normalize motion accumulator
                normalized_motion = motion_accumulator / frame_count
                motion_data['heatmap'] = (normalized_motion * 255).astype(np.uint8)
                motion_data['motion_intensity'] = np.mean(normalized_motion)
            
            return motion_data
            
        except Exception as e:
            print(f"[ERROR] Motion analysis failed: {e}")
            return None
    
    def create_roi_mask(self, frame_shape, roi_areas):
        """Create mask from ROI areas (rectangles and polygons)"""
        mask = np.zeros(frame_shape, dtype=np.uint8)
        
        for area in roi_areas:
            if 'type' in area:
                if area['type'] == 'rectangle':
                    x, y, w, h = area['coords']
                    mask[y:y+h, x:x+w] = 255
                elif area['type'] == 'polygon':
                    pts = np.array(area['coords'], np.int32)
                    cv2.fillPoly(mask, [pts], 255)
            else:
                # Legacy ROI format (x, y, w, h)
                x, y, w, h = area
                mask[y:y+h, x:x+w] = 255
        
        return mask
    
    def generate_motion_thumbnail(self, event, motion_data, size=(200, 150)):
        """Generate motion-highlighted thumbnail"""
        try:
            if not motion_data or not motion_data['key_frames']:
                return None
            
            # Use middle frame as base
            middle_frame = motion_data['key_frames'][len(motion_data['key_frames']) // 2]['frame']
            
            # Create motion overlay
            if is_valid_frame(motion_data['heatmap']):
                # Convert heatmap to color
                heatmap_colored = cv2.applyColorMap(motion_data['heatmap'], cv2.COLORMAP_JET)
                
                # Blend with original frame
                alpha = 0.6
                blended = cv2.addWeighted(middle_frame, 1 - alpha, heatmap_colored, alpha, 0)
            else:
                blended = middle_frame
            
            # Draw movement path
            if len(motion_data['movement_path']) > 1:
                for i in range(1, len(motion_data['movement_path'])):
                    pt1 = motion_data['movement_path'][i-1]
                    pt2 = motion_data['movement_path'][i]
                    cv2.line(blended, pt1, pt2, (255, 255, 255), 2)
                    cv2.circle(blended, pt2, 3, (255, 255, 255), -1)
            
            # Resize thumbnail
            thumbnail = cv2.resize(blended, size)
            
            return thumbnail
            
        except Exception as e:
            print(f"[ERROR] Thumbnail generation failed: {e}")
            return None


class FastValidationInterface:
    """Enhanced fast validation interface with motion visualization"""
    
    def __init__(self, main_app):
        self.main_app = main_app
        self.motion_analyzer = MotionAnalyzer(main_app.video_path)
        self.validation_decisions = {}
        self.motion_cache = {}
        
        # Load existing validation decisions from events
        self.load_existing_validation_decisions()
        
    def load_existing_validation_decisions(self):
        """Load existing validation decisions from event data"""
        if not self.main_app.detector or not hasattr(self.main_app.detector, 'events'):
            return
            
        events = self.main_app.detector.events
        for idx, event in enumerate(events):
            # Check if event has validation decision
            if 'validation_decision' in event:
                decision = event['validation_decision']
                if decision in ['approved', 'rejected']:
                    self.validation_decisions[idx] = decision
                    print(f"[INFO] Loaded existing validation for event {idx + 1}: {decision}")
            elif event.get('validated', False):
                # Legacy support: if only 'validated' field exists, assume approved
                self.validation_decisions[idx] = 'approved'
                print(f"[INFO] Loaded legacy validation for event {idx + 1}: approved")
    
    def show_enhanced_validation_overview(self):
        """Show enhanced validation overview with motion analysis"""
        if not self.main_app.detector or not hasattr(self.main_app.detector, 'events') or not self.main_app.detector.events:
            messagebox.showwarning("Keine Ereignisse", "Keine Ereignisse zur Validierung vorhanden.")
            return
        
        # Create main validation window with full responsiveness
        self.validation_window = tk.Toplevel(self.main_app.root)
        self.validation_window.title("Schnelle Ereignisvalidierung")
        self.validation_window.minsize(1200, 700)
        self.validation_window.resizable(True, True)
        self.validation_window.transient(self.main_app.root)
        self.validation_window.grab_set()
        
        # Configure window for proper responsiveness
        self.validation_window.grid_rowconfigure(0, weight=1)
        self.validation_window.grid_columnconfigure(0, weight=1)
        
        # Smart window sizing based on screen size - no fixed height
        screen_width = self.validation_window.winfo_screenwidth()
        screen_height = self.validation_window.winfo_screenheight()
        
        # Use 85% of screen size, but with proper minimum sizes
        window_width = min(max(int(screen_width * 0.85), 1200), screen_width - 100)
        window_height = min(max(int(screen_height * 0.85), 700), screen_height - 100)
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.validation_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Configure window closing
        self.validation_window.protocol("WM_DELETE_WINDOW", self.close_validation)
        
        # Add window resize handler for responsive grid updates
        self.validation_window.bind("<Configure>", self.on_window_resize)
        self._last_window_width = 0  # Track window width changes
        
        # Set up responsive interface
        self.setup_responsive_validation_interface()
        
        # Start motion analysis in background
        self.start_motion_analysis()
    
    def setup_responsive_validation_interface(self):
        """Setup enhanced responsive validation interface with proper scrolling"""
        # Configure main window grid for proper responsiveness
        self.validation_window.grid_rowconfigure(0, weight=1)  # Main content area
        self.validation_window.grid_rowconfigure(1, weight=0)  # Fixed bottom buttons
        self.validation_window.grid_columnconfigure(0, weight=1)
        
        # Create scrollable main content area
        main_container = ttk.Frame(self.validation_window)
        main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))
        main_container.grid_rowconfigure(0, weight=0)  # Header (fixed)
        main_container.grid_rowconfigure(1, weight=1)  # Content (expandable + scrollable)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Header section (fixed, non-scrollable)
        header_frame = ttk.Frame(main_container)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        self.create_professional_header(header_frame)
        
        # Scrollable content area
        self.create_scrollable_content_area(main_container)
        
        # Fixed bottom controls (always visible)
        self.create_fixed_bottom_controls()
    
    def create_scrollable_content_area(self, parent):
        """Create scrollable content area for all dynamic content"""
        # Create scrollable frame container
        scroll_container = ttk.Frame(parent)
        scroll_container.grid(row=1, column=0, sticky="nsew")
        scroll_container.grid_rowconfigure(0, weight=1)
        scroll_container.grid_columnconfigure(0, weight=1)
        
        # Create canvas and scrollbar
        self.content_canvas = tk.Canvas(scroll_container, highlightthickness=0)
        scrollbar_v = ttk.Scrollbar(scroll_container, orient="vertical", command=self.content_canvas.yview)
        scrollbar_h = ttk.Scrollbar(scroll_container, orient="horizontal", command=self.content_canvas.xview)
        
        # Create scrollable frame
        self.scrollable_content = ttk.Frame(self.content_canvas)
        
        # Configure scrolling
        self.scrollable_content.bind(
            "<Configure>",
            lambda e: self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))
        )
        
        # Create window in canvas
        self.content_canvas.create_window((0, 0), window=self.scrollable_content, anchor="nw")
        self.content_canvas.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        # Grid layout for scrollable area
        self.content_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar_v.grid(row=0, column=1, sticky="ns")
        scrollbar_h.grid(row=1, column=0, sticky="ew")
        
        # Configure scrollbar visibility
        scroll_container.grid_rowconfigure(0, weight=1)
        scroll_container.grid_columnconfigure(0, weight=1)
        
        # Add mouse wheel support
        self.bind_mousewheel_to_content()
        
        # Setup main content tabs in scrollable area
        self.setup_main_content_area(self.scrollable_content)
    
    def bind_mousewheel_to_content(self):
        """Bind mouse wheel scrolling to content area"""
        def _on_mousewheel(event):
            self.content_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def _bind_to_mousewheel(event):
            self.content_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            self.content_canvas.unbind_all("<MouseWheel>")
        
        # Bind enter/leave events
        self.content_canvas.bind('<Enter>', _bind_to_mousewheel)
        self.content_canvas.bind('<Leave>', _unbind_from_mousewheel)
    
    def update_content_scroll_region(self):
        """Update scroll region when content changes"""
        if hasattr(self, 'content_canvas') and hasattr(self, 'scrollable_content'):
            self.validation_window.update_idletasks()
            self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))
    
    def create_fixed_bottom_controls(self):
        """Create fixed bottom control panel that's always visible"""
        # Bottom controls frame (fixed at bottom of window)
        bottom_frame = ttk.Frame(self.validation_window)
        bottom_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 20))
        bottom_frame.grid_columnconfigure(1, weight=1)  # Spacer column
        
        # Add separator line
        separator = ttk.Separator(bottom_frame, orient='horizontal')
        separator.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 15))
        
        # Control buttons with professional styling
        self.create_enhanced_validation_controls(bottom_frame)
    
    def setup_main_content_area(self, parent):
        """Setup main content area with responsive tabs (now in scrollable area)"""
        # Configure parent for responsive behavior
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        
        # Create notebook with enhanced styling
        style = ttk.Style()
        style.configure('Enhanced.TNotebook.Tab', padding=[15, 10])
        
        self.notebook = ttk.Notebook(parent, style='Enhanced.TNotebook')
        self.notebook.grid(row=0, column=0, sticky="nsew", pady=(0, 20))
        
        # Enhanced tabs with better organization
        self.setup_enhanced_grid_tab()
        self.setup_enhanced_frames_tab() 
        self.setup_enhanced_motion_tab()
        self.setup_enhanced_timeline_tab()
        
        # Bind tab change events for better UX
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def create_professional_header(self, parent):
        """Create professional header with clear event overview"""
        # Title section
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Main title with professional styling
        title_label = ttk.Label(title_frame, text="🦇 Ereignis-Validierung", 
                               font=('Segoe UI', 20, 'bold'), foreground="#1f4788")
        title_label.pack(side=tk.LEFT)
        
        # Status indicator
        self.status_label = ttk.Label(title_frame, text="⚡ Bereit für Validierung", 
                                     font=('Segoe UI', 11), foreground="#28a745")
        self.status_label.pack(side=tk.RIGHT)
        
        # Statistics panel with professional layout
        stats_frame = ttk.LabelFrame(parent, text="📊 Ereignis-Übersicht", padding=15)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Calculate statistics
        events = self.main_app.detector.events
        total_duration = sum(event.get('duration', 0) for event in events if event.get('duration'))
        avg_duration = total_duration / len(events) if events else 0
        
        # Create responsive statistics grid
        stats_container = ttk.Frame(stats_frame)
        stats_container.pack(fill=tk.X)
        
        # Statistics cards in a grid layout
        stats_data = [
            ("🔍", "Gefundene Ereignisse", str(len(events)), "#1f4788"),
            ("⏱️", "Gesamtdauer", f"{total_duration:.1f}s", "#6610f2"),
            ("📊", "Durchschnittsdauer", f"{avg_duration:.1f}s", "#fd7e14"),
            ("✅", "Validiert", f"{len(self.validation_decisions)}/{len(events)}", "#28a745")
        ]
        
        for i, (icon, label, value, color) in enumerate(stats_data):
            card_frame = ttk.Frame(stats_container)
            card_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15 if i < 3 else 0))
            
            # Icon and value
            value_frame = ttk.Frame(card_frame)
            value_frame.pack(anchor=tk.W)
            
            ttk.Label(value_frame, text=icon, font=('Segoe UI', 16)).pack(side=tk.LEFT, padx=(0, 8))
            ttk.Label(value_frame, text=value, font=('Segoe UI', 16, 'bold'), 
                     foreground=color).pack(side=tk.LEFT)
            
            # Label
            ttk.Label(card_frame, text=label, font=('Segoe UI', 10), 
                     foreground="#6c757d").pack(anchor=tk.W)
        
        # Progress bar with validation status
        progress_frame = ttk.Frame(stats_frame)
        progress_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Label(progress_frame, text="Validierungsfortschritt:", 
                 font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           length=400, mode='determinate', style='success.Horizontal.TProgressbar')
        self.progress_bar.pack(anchor=tk.W)
    

    def setup_enhanced_grid_tab(self):
        """Setup enhanced interactive grid view tab"""
        # Create main frame for grid tab
        grid_main = ttk.Frame(self.notebook)
        self.notebook.add(grid_main, text="📊 Ereignis-Raster")
        
        # Configure responsive layout
        grid_main.columnconfigure(0, weight=1)
        grid_main.rowconfigure(1, weight=1)
        
        # Control panel at top
        control_panel = ttk.Frame(grid_main)
        control_panel.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        # View options
        view_frame = ttk.LabelFrame(control_panel, text="🎛️ Ansichtsoptionen", padding=10)
        view_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Grid size control
        ttk.Label(view_frame, text="Raster-Größe:").pack(side=tk.LEFT, padx=(0, 5))
        self.grid_size_var = tk.StringVar(value="medium")
        size_combo = ttk.Combobox(view_frame, textvariable=self.grid_size_var, 
                                 values=["klein", "mittel", "groß"], state="readonly", width=10)
        size_combo.pack(side=tk.LEFT, padx=(0, 15))
        size_combo.bind("<<ComboboxSelected>>", self.update_grid_layout)
        
        # Sort options
        ttk.Label(view_frame, text="Sortierung:").pack(side=tk.LEFT, padx=(0, 5))
        self.sort_var = tk.StringVar(value="time")
        sort_combo = ttk.Combobox(view_frame, textvariable=self.sort_var,
                                 values=["Zeit", "Dauer", "Bewegung"], state="readonly", width=12)
        sort_combo.pack(side=tk.LEFT)
        sort_combo.bind("<<ComboboxSelected>>", self.update_grid_layout)
        
        # Create scrollable grid area
        grid_canvas = tk.Canvas(grid_main, bg='#f8f9fa')
        grid_scrollbar = ttk.Scrollbar(grid_main, orient="vertical", command=grid_canvas.yview)
        self.scrollable_grid = ttk.Frame(grid_canvas)
        
        # Enhanced scrolling configuration
        self.scrollable_grid.bind("<Configure>", 
                                 lambda e: grid_canvas.configure(scrollregion=grid_canvas.bbox("all")))
        
        grid_canvas.create_window((0, 0), window=self.scrollable_grid, anchor="nw")
        grid_canvas.configure(yscrollcommand=grid_scrollbar.set)
        
        # Enhanced mouse wheel scrolling
        def _on_grid_mousewheel(event):
            grid_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_mousewheel(event):
            grid_canvas.bind_all("<MouseWheel>", _on_grid_mousewheel)
        
        def _unbind_mousewheel(event):
            grid_canvas.unbind_all("<MouseWheel>")
            
        grid_canvas.bind('<Enter>', _bind_mousewheel)
        grid_canvas.bind('<Leave>', _unbind_mousewheel)
        
        # Grid layout
        grid_canvas.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=(0, 10))
        grid_scrollbar.grid(row=1, column=1, sticky="ns", pady=(0, 10))
        
        # Loading indicator
        self.grid_loading_label = ttk.Label(self.scrollable_grid, 
                                           text="🔄 Lade Ereignis-Raster...\nBitte warten Sie, während die Ereignisse analysiert werden.", 
                                           font=('Segoe UI', 12), justify=tk.CENTER)
        self.grid_loading_label.pack(pady=50)
    
    def setup_enhanced_frames_tab(self):
        """Setup enhanced captured frames viewer tab"""
        frames_main = ttk.Frame(self.notebook)
        self.notebook.add(frames_main, text="🎬 Erfasste Frames")
        
        # Configure responsive layout
        frames_main.columnconfigure(0, weight=1)
        frames_main.rowconfigure(1, weight=1)
        
        # Frame controls
        frame_control = ttk.Frame(frames_main)
        frame_control.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        # Frame selection options
        selection_frame = ttk.LabelFrame(frame_control, text="🎯 Frame-Auswahl", padding=10)
        selection_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Event selector
        ttk.Label(selection_frame, text="Ereignis:").pack(side=tk.LEFT, padx=(0, 5))
        self.event_var = tk.StringVar()
        self.event_combo = ttk.Combobox(selection_frame, textvariable=self.event_var, 
                                       state="readonly", width=15)
        self.event_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.event_combo.bind("<<ComboboxSelected>>", self.load_event_frames)
        
        # Frame type selector
        ttk.Label(selection_frame, text="Frame-Typ:").pack(side=tk.LEFT, padx=(0, 5))
        self.frame_type_var = tk.StringVar(value="all")
        frame_type_combo = ttk.Combobox(selection_frame, textvariable=self.frame_type_var,
                                       values=["Alle", "Schlüssel-Frames", "Bewegung"], 
                                       state="readonly", width=12)
        frame_type_combo.pack(side=tk.LEFT)
        frame_type_combo.bind("<<ComboboxSelected>>", self.filter_frames)
        
        # Scrollable frames area
        frames_canvas = tk.Canvas(frames_main, bg='#f8f9fa')
        frames_scrollbar = ttk.Scrollbar(frames_main, orient="vertical", command=frames_canvas.yview)
        self.scrollable_frames = ttk.Frame(frames_canvas)
        
        self.scrollable_frames.bind("<Configure>", 
                                   lambda e: frames_canvas.configure(scrollregion=frames_canvas.bbox("all")))
        
        frames_canvas.create_window((0, 0), window=self.scrollable_frames, anchor="nw")
        frames_canvas.configure(yscrollcommand=frames_scrollbar.set)
        
        # Enhanced mouse wheel scrolling for frames
        def _on_frames_mousewheel(event):
            frames_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_frames_mousewheel(event):
            frames_canvas.bind_all("<MouseWheel>", _on_frames_mousewheel)
        
        def _unbind_frames_mousewheel(event):
            frames_canvas.unbind_all("<MouseWheel>")
            
        frames_canvas.bind('<Enter>', _bind_frames_mousewheel)
        frames_canvas.bind('<Leave>', _unbind_frames_mousewheel)
        
        # Layout
        frames_canvas.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=(0, 10))
        frames_scrollbar.grid(row=1, column=1, sticky="ns", pady=(0, 10))
        
        # Loading indicator
        self.frames_loading_label = ttk.Label(self.scrollable_frames, 
                                             text="🔄 Lade erfasste Frames...\nEreignis auswählen zum Anzeigen der Frames", 
                                             font=('Segoe UI', 12), justify=tk.CENTER)
        self.frames_loading_label.pack(pady=50)
    
    def setup_enhanced_motion_tab(self):
        """Setup enhanced motion analysis tab"""
        motion_main = ttk.Frame(self.notebook)
        self.notebook.add(motion_main, text="🔥 Bewegungsanalyse")
        
        # Configure responsive layout
        motion_main.columnconfigure(0, weight=1)
        motion_main.rowconfigure(1, weight=1)
        
        # Motion analysis controls
        motion_control = ttk.Frame(motion_main)
        motion_control.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        # Analysis options
        analysis_frame = ttk.LabelFrame(motion_control, text="🎛️ Analyse-Optionen", padding=10)
        analysis_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Motion sensitivity
        ttk.Label(analysis_frame, text="Empfindlichkeit:").pack(side=tk.LEFT, padx=(0, 5))
        self.motion_sensitivity = tk.StringVar(value="medium")
        sensitivity_combo = ttk.Combobox(analysis_frame, textvariable=self.motion_sensitivity,
                                        values=["niedrig", "mittel", "hoch"], state="readonly", width=10)
        sensitivity_combo.pack(side=tk.LEFT, padx=(0, 15))
        
        # Visualization type
        ttk.Label(analysis_frame, text="Darstellung:").pack(side=tk.LEFT, padx=(0, 5))
        self.visualization_type = tk.StringVar(value="heatmap")
        viz_combo = ttk.Combobox(analysis_frame, textvariable=self.visualization_type,
                                values=["Heatmap", "Pfade", "Kombiniert"], state="readonly", width=12)
        viz_combo.pack(side=tk.LEFT)
        
        # Scrollable motion analysis area
        motion_canvas = tk.Canvas(motion_main, bg='#f8f9fa')
        motion_scrollbar = ttk.Scrollbar(motion_main, orient="vertical", command=motion_canvas.yview)
        self.scrollable_motion = ttk.Frame(motion_canvas)
        
        self.scrollable_motion.bind("<Configure>", 
                                   lambda e: motion_canvas.configure(scrollregion=motion_canvas.bbox("all")))
        
        motion_canvas.create_window((0, 0), window=self.scrollable_motion, anchor="nw")
        motion_canvas.configure(yscrollcommand=motion_scrollbar.set)
        
        # Enhanced mouse wheel scrolling for motion
        def _on_motion_mousewheel(event):
            motion_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_motion_mousewheel(event):
            motion_canvas.bind_all("<MouseWheel>", _on_motion_mousewheel)
        
        def _unbind_motion_mousewheel(event):
            motion_canvas.unbind_all("<MouseWheel>")
            
        motion_canvas.bind('<Enter>', _bind_motion_mousewheel)
        motion_canvas.bind('<Leave>', _unbind_motion_mousewheel)
        
        # Layout
        motion_canvas.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=(0, 10))
        motion_scrollbar.grid(row=1, column=1, sticky="ns", pady=(0, 10))
        
        # Loading indicator
        self.motion_loading_label = ttk.Label(self.scrollable_motion, 
                                             text="🔄 Analysiere Bewegungsmuster...\nDies kann einen Moment dauern", 
                                             font=('Segoe UI', 12), justify=tk.CENTER)
        self.motion_loading_label.pack(pady=50)
    
    def setup_enhanced_timeline_tab(self):
        """Setup enhanced timeline view tab"""
        timeline_main = ttk.Frame(self.notebook)
        self.notebook.add(timeline_main, text="📈 Zeitachse")
        
        # Configure responsive layout
        timeline_main.columnconfigure(0, weight=1)
        timeline_main.rowconfigure(1, weight=1)
        
        # Timeline controls
        timeline_control = ttk.Frame(timeline_main)
        timeline_control.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        # Timeline options
        timeline_options = ttk.LabelFrame(timeline_control, text="📊 Timeline-Optionen", padding=10)
        timeline_options.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Zoom level
        ttk.Label(timeline_options, text="Zoom:").pack(side=tk.LEFT, padx=(0, 5))
        self.timeline_zoom = tk.StringVar(value="1x")
        zoom_combo = ttk.Combobox(timeline_options, textvariable=self.timeline_zoom,
                                 values=["0.5x", "1x", "2x", "5x"], state="readonly", width=8)
        zoom_combo.pack(side=tk.LEFT, padx=(0, 15))
        zoom_combo.bind("<<ComboboxSelected>>", self.update_timeline)
        
        # Show details
        self.show_details = tk.BooleanVar(value=True)
        ttk.Checkbutton(timeline_options, text="Details anzeigen", 
                       variable=self.show_details, command=self.update_timeline).pack(side=tk.LEFT)
        
        # Scrollable timeline area
        timeline_canvas = tk.Canvas(timeline_main, bg='white', height=400)
        timeline_h_scroll = ttk.Scrollbar(timeline_main, orient="horizontal", command=timeline_canvas.xview)
        timeline_v_scroll = ttk.Scrollbar(timeline_main, orient="vertical", command=timeline_canvas.yview)
        
        timeline_canvas.configure(xscrollcommand=timeline_h_scroll.set, yscrollcommand=timeline_v_scroll.set)
        
        # Layout with dual scrollbars
        timeline_canvas.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=(0, 0))
        timeline_v_scroll.grid(row=1, column=1, sticky="ns", pady=(0, 0))
        timeline_h_scroll.grid(row=2, column=0, sticky="ew", padx=(10, 0), pady=(0, 10))
        
        # Enhanced timeline drawing
        self.timeline_canvas = timeline_canvas
        self.draw_enhanced_timeline()
    
    def on_tab_changed(self, event):
        """Handle tab change events for better UX"""
        selected_tab = event.widget.tab('current')['text']
        self.status_label.config(text=f"⚡ Anzeige: {selected_tab}")
        
        # Trigger specific loading for selected tab if needed
        if "Erfasste Frames" in selected_tab and not hasattr(self, 'frames_loaded'):
            self.load_initial_event_frames()
        elif "Bewegungsanalyse" in selected_tab and not hasattr(self, 'motion_loaded'):
            self.update_motion_display()
    
    def start_motion_analysis(self):
        """Start motion analysis in background thread"""
        def analyze_all_events():
            events = self.main_app.detector.events
            
            # Collect ROI information
            roi_areas = []
            if hasattr(self.main_app, 'roi') and self.main_app.roi:
                roi_areas.append({
                    'type': 'rectangle',
                    'coords': self.main_app.roi
                })
            
            if hasattr(self.main_app, 'polygon_areas') and self.main_app.polygon_areas:
                for polygon in self.main_app.polygon_areas:
                    if len(polygon) >= 3:
                        roi_areas.append({
                            'type': 'polygon',
                            'coords': polygon
                        })
            
            for idx, event in enumerate(events):
                try:
                    # Update progress
                    progress = (idx / len(events)) * 100
                    self.validation_window.after(0, lambda p=progress: self.update_analysis_progress(p))
                    
                    # Analyze motion for this event
                    motion_data = self.motion_analyzer.analyze_event_motion(event, roi_areas)
                    self.motion_cache[idx] = motion_data
                    
                    # Update UI with new data
                    self.validation_window.after(0, lambda i=idx: self.update_event_display(i))
                    
                except Exception as e:
                    print(f"[ERROR] Motion analysis failed for event {idx}: {e}")
            
            # Analysis complete
            self.validation_window.after(0, self.analysis_complete)
        
        # Start analysis thread
        analysis_thread = threading.Thread(target=analyze_all_events, daemon=True)
        analysis_thread.start()
    
    def update_analysis_progress(self, progress):
        """Update analysis progress indicator"""
        self.progress_var.set(progress)
        
    def update_event_display(self, event_idx):
        """Update display for a specific event after motion analysis"""
        try:
            # Update grid view if this is the first event
            if event_idx == 0:
                self.populate_grid_view()
            
            # Add motion visualization if available
            if event_idx in self.motion_cache:
                self.add_motion_visualization(event_idx)
                
        except Exception as e:
            print(f"[ERROR] Display update failed for event {event_idx}: {e}")
    
    def analysis_complete(self):
        """Called when motion analysis is complete"""
        self.progress_var.set(100)
        
        # Remove loading messages
        if hasattr(self, 'grid_loading_label'):
            self.grid_loading_label.destroy()
        if hasattr(self, 'frames_loading_label'):
            self.frames_loading_label.destroy()
        if hasattr(self, 'motion_loading_label'):
            self.motion_loading_label.destroy()
        
        # Populate all views
        self.populate_frames_view()
        self.populate_motion_view()
        
        print("[INFO] Motion analysis complete")
    

    def draw_position_visualization(self, canvas):
        """Draw position visualization on canvas"""
        try:
            # Clear canvas
            canvas.delete("all")
            
            # Canvas dimensions
            canvas_width = 750
            canvas_height = 450
            
            # Draw coordinate grid
            for i in range(0, canvas_width, 50):
                canvas.create_line(i, 0, i, canvas_height, fill="#333333", width=1)
            for i in range(0, canvas_height, 50):
                canvas.create_line(0, i, canvas_width, i, fill="#333333", width=1)
            
            # Draw ROI if available
            if hasattr(self.main_app, 'roi') and self.main_app.roi:
                roi = self.main_app.roi
                # Scale ROI to canvas
                scale_x = canvas_width / 640  # Assume 640x480 video
                scale_y = canvas_height / 480
                
                roi_x = roi[0] * scale_x
                roi_y = roi[1] * scale_y
                roi_w = roi[2] * scale_x
                roi_h = roi[3] * scale_y
                
                canvas.create_rectangle(roi_x, roi_y, roi_x + roi_w, roi_y + roi_h,
                                      outline="yellow", width=3, fill="", stipple="gray25")
                canvas.create_text(roi_x + 10, roi_y + 20, text="ROI", 
                                 fill="yellow", font=('Arial', 12, 'bold'))
            
            # Draw polygon areas if available
            if hasattr(self.main_app, 'polygon_areas') and self.main_app.polygon_areas:
                colors = ['cyan', 'magenta', 'lime', 'orange']
                for i, polygon in enumerate(self.main_app.polygon_areas):
                    if len(polygon) >= 3:
                        # Scale polygon to canvas
                        scaled_polygon = [(x * canvas_width / 640, y * canvas_height / 480) 
                                        for x, y in polygon]
                        
                        # Flatten coordinates for tkinter
                        coords = []
                        for x, y in scaled_polygon:
                            coords.extend([x, y])
                        
                        color = colors[i % len(colors)]
                        canvas.create_polygon(coords, outline=color, width=2, 
                                            fill="", stipple="gray12")
                        
                        # Label
                        center_x = sum(x for x, y in scaled_polygon) / len(scaled_polygon)
                        center_y = sum(y for x, y in scaled_polygon) / len(scaled_polygon)
                        canvas.create_text(center_x, center_y, text=f"Polygon {i+1}", 
                                         fill=color, font=('Arial', 10, 'bold'))
            
            # Draw event positions
            events = self.main_app.detector.events
            position_colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown']
            
            events_with_positions = 0
            for idx, event in enumerate(events):
                bat_center = event.get('bat_center')
                if bat_center and len(bat_center) == 2:
                    # Scale position to canvas
                    pos_x = bat_center[0] * canvas_width / 640
                    pos_y = bat_center[1] * canvas_height / 480
                    
                    color = position_colors[idx % len(position_colors)]
                    
                    # Draw position marker
                    canvas.create_oval(pos_x - 10, pos_y - 10, pos_x + 10, pos_y + 10,
                                     fill=color, outline="white", width=2)
                    
                    # Event label
                    canvas.create_text(pos_x, pos_y - 20, text=f"E{idx+1}", 
                                     fill="white", font=('Arial', 10, 'bold'))
                    
                    # Show validation status
                    if event.get('validated', False):
                        validation_decision = event.get('validation_decision', 'unknown')
                        if validation_decision == 'approved':
                            status_marker = "✓"
                            status_color = "lime"
                        elif validation_decision == 'rejected':
                            status_marker = "✗"
                            status_color = "red"
                        else:
                            status_marker = "?"
                            status_color = "yellow"
                        
                        canvas.create_text(pos_x + 15, pos_y - 15, text=status_marker, 
                                         fill=status_color, font=('Arial', 12, 'bold'))
                    
                    events_with_positions += 1
            
            # Add legend and info
            canvas.create_text(10, 20, text="🗺️ Ereignis-Positionen", 
                             fill="white", font=('Arial', 14, 'bold'), anchor="nw")
            
            info_text = f"📊 {events_with_positions}/{len(events)} Ereignisse mit Positionsdaten"
            canvas.create_text(10, 45, text=info_text, 
                             fill="white", font=('Arial', 11), anchor="nw")
            
            # Legend
            if events_with_positions > 0:
                legend_y = 70
                canvas.create_text(10, legend_y, text="Legende:", 
                                 fill="white", font=('Arial', 10, 'bold'), anchor="nw")
                canvas.create_text(10, legend_y + 20, text="✓ = Genehmigt", 
                                 fill="lime", font=('Arial', 9), anchor="nw")
                canvas.create_text(10, legend_y + 35, text="✗ = Abgelehnt", 
                                 fill="red", font=('Arial', 9), anchor="nw")
                canvas.create_text(10, legend_y + 50, text="⚪ = Ausstehend", 
                                 fill="yellow", font=('Arial', 9), anchor="nw")
            
        except Exception as e:
            print(f"[ERROR] Position visualization failed: {e}")
            canvas.create_text(375, 225, text=f"Fehler: {str(e)}", 
                             fill="red", font=('Arial', 12))
    
    def export_position_data(self):
        """Export position data to JSON file"""
        try:
            import json
            from datetime import datetime
            
            events = self.main_app.detector.events
            position_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_events': len(events),
                'roi': getattr(self.main_app, 'roi', None),
                'polygon_areas': getattr(self.main_app, 'polygon_areas', []),
                'events': []
            }
            
            for idx, event in enumerate(events):
                if event.get('bat_center'):
                    event_data = {
                        'event_id': idx + 1,
                        'position': event['bat_center'],
                        'entry_time': event.get('entry', 0),
                        'exit_time': event.get('exit', 0),
                        'duration': event.get('duration', 0),
                        'validated': event.get('validated', False),
                        'validation_decision': event.get('validation_decision', 'pending')
                    }
                    position_data['events'].append(event_data)
            
            # Save to file
            filename = f"event_positions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(position_data, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("Export erfolgreich", 
                              f"Positionsdaten erfolgreich exportiert:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Export-Fehler", f"Fehler beim Exportieren: {str(e)}")

    def populate_grid_view(self):
        """Populate the grid view with event thumbnails using responsive horizontal layout"""
        # Clear loading message
        if hasattr(self, 'grid_loading_label'):
            self.grid_loading_label.destroy()
        
        events = self.main_app.detector.events
        
        # Calculate responsive number of columns based on window width
        cols = self.calculate_responsive_grid_columns()
        
        # Create grid container with better horizontal spacing
        grid_container = ttk.Frame(self.scrollable_grid, padding=(20, 15))
        grid_container.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid container for full width usage
        for col in range(cols):
            grid_container.grid_columnconfigure(col, weight=1, minsize=200)
        
        for idx, event in enumerate(events):
            row = idx // cols
            col = idx % cols
            
            # Create event card with improved sizing
            event_card = self.create_event_card(grid_container, event, idx)
            event_card.grid(row=row, column=col, padx=12, pady=10, sticky="nsew")
            
            # Configure row weight for better vertical distribution
            grid_container.grid_rowconfigure(row, weight=1)
        
        # Update scroll region after populating content
        self.update_content_scroll_region()
    
    def calculate_responsive_grid_columns(self):
        """Calculate optimal number of columns based on window width"""
        try:
            # Get current window width
            window_width = self.validation_window.winfo_width()
            
            # If window hasn't been rendered yet, use default
            if window_width <= 1:
                window_width = 1200  # Default width
            
            # Calculate optimal columns based on window width
            # Minimum card width: 220px, ideal: 280px, padding: 40px per card
            ideal_card_width = 280
            min_card_width = 220
            total_padding = 80  # Account for window padding and card spacing
            
            # Calculate how many cards can fit comfortably
            available_width = window_width - total_padding
            
            # Try ideal width first
            ideal_cols = max(1, available_width // (ideal_card_width + 24))  # +24 for padx
            
            # If less than 3 columns with ideal width, try minimum width
            if ideal_cols < 3:
                min_cols = max(1, available_width // (min_card_width + 24))
                cols = min(min_cols, 6)  # Cap at 6 columns maximum
            else:
                cols = min(ideal_cols, 6)  # Cap at 6 columns maximum
            
            # Ensure minimum of 2 columns for better layout
            cols = max(2, cols)
            
            return cols
            
        except Exception:
            # Fallback to responsive default based on typical screen sizes
            return 5
    
    def populate_frames_view(self):
        """Populate the captured frames view"""
        # Clear loading message
        if hasattr(self, 'frames_loading_label'):
            self.frames_loading_label.destroy()
        
        events = self.main_app.detector.events
        
        # Create frames container
        frames_container = ttk.Frame(self.scrollable_frames, padding=15)
        frames_container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(frames_container, text="🎬 Erfasste Frames pro Ereignis", 
                 font=('Arial', 16, 'bold')).pack(anchor=tk.W, pady=(0, 15))
        
        for idx, event in enumerate(events):
            # Create enhanced event section with Einflug/Ausflug information
            event_section = ttk.LabelFrame(frames_container, text=f"🎯 Ereignis {idx + 1} - Frame-Sequenz", padding=15)
            event_section.pack(fill=tk.X, pady=(0, 15))
            
            # Enhanced event timing information with safe handling
            start_time = event.get('entry') or event.get('einflugzeit')
            end_time = event.get('exit') or event.get('ausflugzeit')
            duration = event.get('duration') or event.get('dauer')
            
            # Handle missing times safely
            if start_time is None:
                start_time = 0
            if end_time is None:
                if duration is not None:
                    end_time = start_time + duration
                else:
                    end_time = start_time + 1  # Default duration
            if duration is None:
                duration = max(0, end_time - start_time)
            
            # Enhanced timing display with precise frame information
            timing_frame = ttk.Frame(event_section)
            timing_frame.pack(fill=tk.X, pady=(0, 10))
            
            # Calculate precise frame numbers
            fps = getattr(self.main_app.detector, 'fps', 30) or 30
            entry_frame = int(start_time * fps)
            exit_frame = int(end_time * fps)
            duration_frames = exit_frame - entry_frame
            
            # Check if event is incomplete
            is_incomplete = event.get('incomplete', False)
            warning_indicator = " ⚠ (unvollständig)" if is_incomplete else ""
            
            # Einflugzeit information with frame number
            einflug_info = ttk.Frame(timing_frame)
            einflug_info.pack(side=tk.LEFT, padx=(0, 25))
            ttk.Label(einflug_info, text="🟢 Einflugzeit:", font=('Arial', 9, 'bold'), 
                     foreground="#28a745").pack(anchor=tk.W)
            
            if event.get('entry') is not None or event.get('einflugzeit') is not None:
                ttk.Label(einflug_info, text=f"{start_time:.3f}s", font=('Arial', 9)).pack(anchor=tk.W)
            else:
                ttk.Label(einflug_info, text="unbekannt", font=('Arial', 9), 
                         foreground="#dc3545").pack(anchor=tk.W)
            
            ttk.Label(einflug_info, text=f"Frame {entry_frame}", font=('Arial', 8), 
                     foreground="#666666").pack(anchor=tk.W)
            
            # Ausflugzeit information with frame number
            ausflug_info = ttk.Frame(timing_frame)
            ausflug_info.pack(side=tk.LEFT, padx=(0, 25))
            ttk.Label(ausflug_info, text=f"🔴 Ausflugzeit{warning_indicator}:", font=('Arial', 9, 'bold'), 
                     foreground="#dc3545").pack(anchor=tk.W)
            
            if event.get('exit') is not None or event.get('ausflugzeit') is not None:
                ttk.Label(ausflug_info, text=f"{end_time:.3f}s", font=('Arial', 9)).pack(anchor=tk.W)
            else:
                ttk.Label(ausflug_info, text="unbekannt", font=('Arial', 9), 
                         foreground="#dc3545").pack(anchor=tk.W)
                         
            ttk.Label(ausflug_info, text=f"Frame {exit_frame}", font=('Arial', 8), 
                     foreground="#666666").pack(anchor=tk.W)
            
            # Dauer information with frame count
            dauer_info = ttk.Frame(timing_frame)
            dauer_info.pack(side=tk.LEFT, padx=(0, 25))
            ttk.Label(dauer_info, text="⏱️ Dauer:", font=('Arial', 9, 'bold'), 
                     foreground="#0066CC").pack(anchor=tk.W)
            
            if duration > 0:
                ttk.Label(dauer_info, text=f"{duration:.3f}s", font=('Arial', 9)).pack(anchor=tk.W)
                ttk.Label(dauer_info, text=f"{duration_frames} Frames", font=('Arial', 8), 
                         foreground="#666666").pack(anchor=tk.W)
            else:
                ttk.Label(dauer_info, text="unbekannt", font=('Arial', 9), 
                         foreground="#dc3545").pack(anchor=tk.W)
            
            # Add polygon information if available
            if 'polygon_area' in event:
                polygon_info = ttk.Frame(timing_frame)
                polygon_info.pack(side=tk.LEFT)
                ttk.Label(polygon_info, text="📍 Polygon:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
                ttk.Label(polygon_info, text=f"#{event['polygon_area'] + 1}", 
                         font=('Arial', 9), foreground="#8B4513").pack(anchor=tk.W)
            
            # Get frame data
            frame_data = None
            if hasattr(self.main_app.detector, 'extract_event_frame_sequence'):
                frame_data = self.main_app.detector.extract_event_frame_sequence(idx, num_frames=8)
            
            if frame_data and frame_data.get('frames'):
                # Create frame viewer for this event
                self.create_event_frame_viewer(event_section, frame_data, idx)
            else:
                # No frames available
                no_frames_frame = ttk.Frame(event_section)
                no_frames_frame.pack(fill=tk.X, pady=20)
                ttk.Label(no_frames_frame, text="⚠️ Keine erfassten Frames verfügbar", 
                         foreground="orange", font=('Arial', 10)).pack()
    
    def create_event_frame_viewer(self, parent, frame_data, event_idx):
        """Create a frame viewer for a specific event"""
        frames = frame_data.get('frames', [])
        if not frames:
            return
        
        # Enhanced frame info with entry/exit indicators
        source_info = frame_data.get('source', 'unknown')
        frame_info_text = f"📹 {len(frames)} Frames ({source_info}) - Einflug bis Ausflug Sequenz"
        ttk.Label(parent, text=frame_info_text, 
                 font=('Arial', 9), foreground="blue").pack(anchor=tk.W, pady=(0, 10))
        
        # Create frame thumbnails container with enhanced layout
        thumbs_frame = ttk.Frame(parent)
        thumbs_frame.pack(fill=tk.X)
        
        # Add entry/exit frame legend
        legend_frame = ttk.Frame(thumbs_frame)
        legend_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(legend_frame, text="🟢 = Einflug-Frame", font=('Arial', 8), 
                 foreground="#28a745").pack(side=tk.LEFT, padx=(0, 15))
        ttk.Label(legend_frame, text="🔴 = Ausflug-Frame", font=('Arial', 8), 
                 foreground="#dc3545").pack(side=tk.LEFT, padx=(0, 15))
        ttk.Label(legend_frame, text="⚪ = Zwischenframe", font=('Arial', 8), 
                 foreground="#666666").pack(side=tk.LEFT)
        
        # Create canvas for horizontal scrolling
        thumbs_canvas = tk.Canvas(thumbs_frame, height=140)
        thumbs_scrollbar = ttk.Scrollbar(thumbs_frame, orient="horizontal", command=thumbs_canvas.xview)
        thumbs_content = ttk.Frame(thumbs_canvas)
        
        thumbs_content.bind(
            "<Configure>",
            lambda e: thumbs_canvas.configure(scrollregion=thumbs_canvas.bbox("all"))
        )
        
        thumbs_canvas.create_window((0, 0), window=thumbs_content, anchor="nw")
        thumbs_canvas.configure(xscrollcommand=thumbs_scrollbar.set)
        
        # Pack scrolling elements
        thumbs_canvas.pack(side="top", fill="x")
        thumbs_scrollbar.pack(side="bottom", fill="x")
        
        # Get event timing for entry/exit detection
        event = self.main_app.detector.events[event_idx]
        entry_time = event.get('entry', 0)
        exit_time = event.get('exit', entry_time + 1)
        
        # Create enhanced thumbnails for each frame
        for frame_idx, frame_info in enumerate(frames):
            self.create_enhanced_frame_thumbnail(thumbs_content, frame_info, frame_idx, event_idx, 
                                               entry_time, exit_time)
        
        # Validation buttons for this event
        val_frame = ttk.Frame(parent)
        val_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(val_frame, text="✅ Genehmigen", 
                  command=lambda: self.validate_event(event_idx, 'approved')).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(val_frame, text="❌ Ablehnen", 
                  command=lambda: self.validate_event(event_idx, 'rejected')).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(val_frame, text="🔍 Details", 
                  command=lambda: self.show_detailed_event_view(self.main_app.detector.events[event_idx], event_idx)).pack(side=tk.RIGHT)
    
    def create_enhanced_frame_thumbnail(self, parent, frame_info, frame_idx, event_idx, entry_time, exit_time):
        """Create enhanced clickable thumbnail for a frame with entry/exit highlighting"""
        try:
            # Get frame
            frame = frame_info.get('marked_frame', frame_info.get('frame'))
            if frame is None:
                return
            
            # Determine frame type (entry, exit, or intermediate)
            timestamp = frame_info.get('timestamp', 0)
            frame_type = 'intermediate'
            border_color = "#cccccc"
            type_indicator = "⚪"
            
            # Check if this is entry or exit frame (within 0.1s tolerance)
            if abs(timestamp - entry_time) < 0.1:
                frame_type = 'entry'
                border_color = "#28a745"
                type_indicator = "🟢"
            elif abs(timestamp - exit_time) < 0.1:
                frame_type = 'exit'
                border_color = "#dc3545"
                type_indicator = "🔴"
            
            # Create frame container
            frame_container = ttk.Frame(parent, padding=2)
            frame_container.pack(side=tk.LEFT, padx=2)
            
            # Enhance frame for validation display
            enhanced_frame = self.enhance_frame_for_validation(frame, frame_info)
            
            # Create thumbnail
            thumbnail = cv2.resize(enhanced_frame, (100, 75))
            
            # Add frame type indicator overlay
            cv2.putText(thumbnail, type_indicator, (5, 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # Convert to display format
            thumbnail_rgb = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(thumbnail_rgb)
            
            # Add colored border based on frame type
            if frame_type != 'intermediate':
                border_width = 3
                new_width = pil_image.width + 2 * border_width
                new_height = pil_image.height + 2 * border_width
                
                if frame_type == 'entry':
                    border_rgb = (40, 167, 69)  # Green
                else:  # exit
                    border_rgb = (220, 53, 69)  # Red
                
                bordered = Image.new('RGB', (new_width, new_height), border_rgb)
                bordered.paste(pil_image, (border_width, border_width))
                pil_image = bordered
            
            photo = ImageTk.PhotoImage(pil_image)
            
            # Create clickable thumbnail
            thumb_label = tk.Label(frame_container, image=photo, cursor="hand2")
            thumb_label.image = photo  # Keep reference
            thumb_label.pack()
            
            # Frame information
            info_text = f"{type_indicator} {timestamp:.2f}s"
            frame_number = frame_info.get('frame_index', 0)
            info_text += f"\nFrame {frame_number}"
            
            info_label = ttk.Label(frame_container, text=info_text, 
                                  font=('Arial', 7), justify=tk.CENTER)
            info_label.pack()
            
            # Click handler for detailed view
            def show_frame_detail():
                self.show_frame_detail_view(frame_info, frame_idx, event_idx, frame_type)
            
            thumb_label.bind("<Button-1>", lambda e: show_frame_detail())
            
        except Exception as e:
            print(f"[ERROR] Enhanced frame thumbnail creation failed: {e}")
    
    def show_frame_detail_view(self, frame_info, frame_idx, event_idx, frame_type):
        """Show detailed view of a specific frame"""
        detail_window = tk.Toplevel(self.validation_window)
        detail_window.title(f"🔍 Frame Detail - Ereignis {event_idx + 1}")
        detail_window.transient(self.validation_window)
        
        # Responsive sizing
        screen_width = detail_window.winfo_screenwidth()
        screen_height = detail_window.winfo_screenheight()
        window_width = min(800, int(screen_width * 0.75))
        window_height = min(600, int(screen_height * 0.75))
        detail_window.geometry(f"{window_width}x{window_height}")
        detail_window.minsize(600, 450)
        detail_window.resizable(True, True)
        
        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        detail_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        main_frame = ttk.Frame(detail_window, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame type header
        type_labels = {
            'entry': "🟢 Einflug-Frame",
            'exit': "🔴 Ausflug-Frame", 
            'intermediate': "⚪ Zwischenframe"
        }
        
        header_text = type_labels.get(frame_type, "Frame Detail")
        ttk.Label(main_frame, text=header_text, 
                 font=('Arial', 14, 'bold')).pack(pady=(0, 15))
        
        # Frame information
        info_frame = ttk.LabelFrame(main_frame, text="Frame-Information", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        timestamp = frame_info.get('timestamp', 0)
        frame_index = frame_info.get('frame_index', 0)
        
        ttk.Label(info_frame, text=f"Zeitstempel: {timestamp:.3f}s").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Frame Index: {frame_index}").pack(anchor=tk.W)
        
        # Bat center info
        bat_center = frame_info.get('bat_center')
        if bat_center:
            ttk.Label(info_frame, text=f"Fledermaus-Position: ({bat_center[0]}, {bat_center[1]})").pack(anchor=tk.W)
        
        # Frame display
        frame_display = ttk.LabelFrame(main_frame, text="Frame-Ansicht", padding=10)
        frame_display.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create canvas for frame
        frame_canvas = tk.Canvas(frame_display, bg='black')
        frame_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Display frame
        frame = frame_info.get('marked_frame', frame_info.get('frame'))
        if is_valid_frame(frame):
            # Enhance and resize frame
            enhanced_frame = self.enhance_frame_for_validation(frame, frame_info)
            display_frame = cv2.resize(enhanced_frame, (750, 400))
            display_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(display_rgb)
            photo = ImageTk.PhotoImage(pil_image)
            
            frame_canvas.create_image(375, 200, image=photo)
            frame_canvas.image = photo  # Keep reference
        
        # Controls
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X)
        
        ttk.Button(control_frame, text="Schließen", 
                  command=detail_window.destroy).pack(side=tk.RIGHT)
    
    def show_frame_detail(self, frame_info, frame_idx, event_idx):
        """Show detailed view of a single frame"""
        detail_window = tk.Toplevel(self.validation_window)
        detail_window.title(f"Frame {frame_idx + 1} - Ereignis {event_idx + 1}")
        detail_window.transient(self.validation_window)
        
        # Responsive sizing
        screen_width = detail_window.winfo_screenwidth()
        screen_height = detail_window.winfo_screenheight()
        window_width = min(800, int(screen_width * 0.75))
        window_height = min(600, int(screen_height * 0.75))
        detail_window.geometry(f"{window_width}x{window_height}")
        detail_window.minsize(600, 450)
        detail_window.resizable(True, True)
        
        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        detail_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        main_frame = ttk.Frame(detail_window, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame info
        timestamp = frame_info.get('timestamp', 0)
        frame_index = frame_info.get('frame_index', 0)
        
        info_frame = ttk.LabelFrame(main_frame, text="Frame-Information", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(info_frame, text=f"Ereignis: {event_idx + 1}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Frame Nr.: {frame_idx + 1}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Zeitstempel: {timestamp:.3f} Sekunden").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Frame Index: {frame_index}").pack(anchor=tk.W)
        
        # Bat center info
        bat_center = frame_info.get('bat_center')
        if bat_center:
            ttk.Label(info_frame, text=f"Fledermaus-Position: ({bat_center[0]}, {bat_center[1]})").pack(anchor=tk.W)
        
        # Frame display
        frame_display = ttk.LabelFrame(main_frame, text="Frame-Ansicht", padding=10)
        frame_display.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create canvas for frame
        frame_canvas = tk.Canvas(frame_display, bg='black')
        frame_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Display frame
        frame = frame_info.get('marked_frame', frame_info.get('frame'))
        if is_valid_frame(frame):
            # Resize to fit canvas
            display_frame = cv2.resize(frame, (750, 400))
            display_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(display_rgb)
            photo = ImageTk.PhotoImage(pil_image)
            
            frame_canvas.create_image(375, 200, image=photo)
            frame_canvas.image = photo  # Keep reference
        
        # Controls
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X)
        
        ttk.Button(control_frame, text="Schließen", 
                  command=detail_window.destroy).pack(side=tk.RIGHT)
    
    def create_event_card(self, parent, event, event_idx):
        """Create an optimized interactive event card for horizontal layout"""
        # Event frame with enhanced styling and better proportions
        card_frame = ttk.LabelFrame(parent, text=f"🎯 Ereignis {event_idx + 1}", padding=10)
        
        # Configure card to use available space efficiently
        card_frame.grid_rowconfigure(1, weight=1)  # Info section can expand
        card_frame.grid_columnconfigure(0, weight=1)
        
        # Load actual captured frames
        frame_data = None
        if hasattr(self.main_app.detector, 'extract_event_frame_sequence'):
            frame_data = self.main_app.detector.extract_event_frame_sequence(event_idx, num_frames=3)
        
        if frame_data and frame_data.get('frames'):
            # Create multi-frame thumbnail showing detection sequence
            thumbnail = self.create_multi_frame_thumbnail(frame_data['frames'])
            
            # Add detection info overlay
            source_info = frame_data.get('source', 'unknown')
            frame_count = len(frame_data['frames'])
            
        else:
            # Fallback to single frame thumbnail
            thumbnail = self.get_event_thumbnail(event, event_idx)
            source_info = "extracted"
            frame_count = 1
        
        # Thumbnail section with better sizing
        thumbnail_frame = ttk.Frame(card_frame)
        thumbnail_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        
        if is_valid_frame(thumbnail):
            # Convert to PhotoImage with optimal sizing for horizontal layout
            thumbnail_rgb = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(thumbnail_rgb)
            
            # Scale image to fit better in horizontal layout
            optimal_width = 180  # Slightly smaller for better grid fit
            optimal_height = 120
            pil_image = pil_image.resize((optimal_width, optimal_height), Image.Resampling.LANCZOS)
            
            # Add motion indicator border
            if event_idx in self.motion_cache:
                motion_intensity = self.motion_cache[event_idx].get('motion_intensity', 0)
                if motion_intensity > 0.1:  # High motion
                    # Add colored border for high motion
                    border_color = (255, 100, 100) if motion_intensity > 0.3 else (255, 200, 100)
                    pil_image = self.add_colored_border(pil_image, border_color, 3)
            
            photo = ImageTk.PhotoImage(pil_image)
            
            # Thumbnail label with click handler
            thumb_label = tk.Label(thumbnail_frame, image=photo, cursor="hand2")
            thumb_label.image = photo  # Keep reference
            thumb_label.pack()
            
            # Click to show detailed view
            thumb_label.bind("<Button-1>", lambda e: self.show_detailed_event_view(event, event_idx))
            
            # Add frame info in smaller text
            frame_info = f"📹 {frame_count} Frames ({source_info})"
            ttk.Label(thumbnail_frame, text=frame_info, font=('Arial', 7), foreground="blue").pack()
        
        # Compact event information section
        info_frame = ttk.Frame(card_frame)
        info_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        info_frame.grid_columnconfigure(0, weight=1)
        
        # Enhanced event information with precise Einflugzeit/Ausflugzeit/Dauer
        start_time = event.get('entry', 0)
        end_time = event.get('exit', start_time + 1)
        duration = event.get('duration', end_time - start_time)
        
        # Calculate precise frame numbers
        fps = getattr(self.main_app.detector, 'fps', 30) or 30
        entry_frame = int(start_time * fps)
        exit_frame = int(end_time * fps)
        duration_frames = exit_frame - entry_frame
        
        # Compact timing information - horizontal layout for space efficiency
        timing_container = ttk.Frame(info_frame)
        timing_container.pack(fill=tk.X)
        
        # Entry time - more compact format
        entry_label = ttk.Label(timing_container, text=f"🟢 {start_time:.2f}s (F{entry_frame})", 
                               font=('Arial', 8), foreground="#28a745")
        entry_label.pack(anchor=tk.W)
        
        # Exit time 
        exit_label = ttk.Label(timing_container, text=f"🔴 {end_time:.2f}s (F{exit_frame})", 
                              font=('Arial', 8), foreground="#dc3545")
        exit_label.pack(anchor=tk.W)
        
        # Duration
        duration_label = ttk.Label(timing_container, text=f"⏱️ {duration:.2f}s ({duration_frames}F)", 
                                  font=('Arial', 8), foreground="#0066CC")
        duration_label.pack(anchor=tk.W)
        
        # Additional info in compact format
        extra_info_frame = ttk.Frame(info_frame)
        extra_info_frame.pack(fill=tk.X, pady=(2, 0))
        
        # Add polygon area info if available
        if 'polygon_area' in event:
            poly_label = ttk.Label(extra_info_frame, text=f"📍 Polygon #{event['polygon_area'] + 1}", 
                                  font=('Arial', 8), foreground="#8B4513")
            poly_label.pack(anchor=tk.W)
        
        # Add motion info if available
        if event_idx in self.motion_cache:
            motion_data = self.motion_cache[event_idx]
            motion_intensity = motion_data.get('motion_intensity', 0)
            motion_label = ttk.Label(extra_info_frame, text=f"🔥 Bewegung: {motion_intensity:.1%}", 
                                   font=('Arial', 8), foreground="#FF6600")
            motion_label.pack(anchor=tk.W)
        
        # Validation state and action buttons - compact layout
        controls_frame = ttk.Frame(card_frame)
        controls_frame.grid(row=2, column=0, sticky="ew")
        controls_frame.grid_columnconfigure(1, weight=1)  # Spacer
        
        # Validation state indicator
        if event_idx in self.validation_decisions:
            decision = self.validation_decisions[event_idx]
            if decision == 'approved':
                status_text = "✅ Genehmigt"
                status_color = "#28a745"
            else:
                status_text = "❌ Abgelehnt"
                status_color = "#dc3545"
            
            status_label = tk.Label(controls_frame, text=status_text, 
                                  fg=status_color, font=('Arial', 9, 'bold'))
            status_label.grid(row=0, column=0, columnspan=3, pady=(0, 4))
        
        # Compact action buttons in horizontal layout
        approve_btn = ttk.Button(controls_frame, text="✅", width=3,
                               command=lambda: self.validate_event(event_idx, 'approved'))
        approve_btn.grid(row=1, column=0, padx=(0, 2))
        
        reject_btn = ttk.Button(controls_frame, text="❌", width=3,
                              command=lambda: self.validate_event(event_idx, 'rejected'))
        reject_btn.grid(row=1, column=2, padx=(2, 0))
        
        detail_btn = ttk.Button(controls_frame, text="🔍", width=3,
                              command=lambda: self.show_detailed_event_view(event, event_idx))
        detail_btn.grid(row=1, column=3, padx=(4, 0))
        
        return card_frame
    
    def create_multi_frame_thumbnail(self, frames, size=(200, 150)):
        """Create enhanced thumbnail showing multiple frames with motion highlighting in ROI/polygons"""
        try:
            if not frames:
                return None
            
            num_frames = min(len(frames), 3)  # Show max 3 frames
            if num_frames == 1:
                frame = frames[0].get('marked_frame', frames[0].get('frame'))
                if is_valid_frame(frame):
                    enhanced_frame = self.enhance_frame_for_validation(frame, frames[0])
                    return cv2.resize(enhanced_frame, size)
                return None
            
            # Create side-by-side thumbnail with enhanced motion highlighting
            frame_width = size[0] // num_frames
            frame_height = size[1]
            
            thumbnail = np.zeros((frame_height, size[0], 3), dtype=np.uint8)
            
            for i in range(num_frames):
                frame_data = frames[i]
                frame = frame_data.get('marked_frame', frame_data.get('frame'))
                
                if is_valid_frame(frame):
                    # Enhance frame for validation display
                    enhanced_frame = self.enhance_frame_for_validation(frame, frame_data)
                    
                    # Resize frame to fit
                    resized = cv2.resize(enhanced_frame, (frame_width, frame_height))
                    
                    # Add precise timestamp and frame info
                    timestamp = frame_data.get('timestamp', 0)
                    frame_index = frame_data.get('frame_index', 0)
                    
                    # Timestamp overlay
                    cv2.putText(resized, f"{timestamp:.2f}s", (2, 15),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
                    
                    # Frame number overlay
                    cv2.putText(resized, f"F#{frame_index}", (2, frame_height - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.25, (200, 200, 200), 1)
                    
                    # Place in thumbnail
                    x_start = i * frame_width
                    x_end = x_start + frame_width
                    thumbnail[:, x_start:x_end] = resized
                    
                    # Add frame separator with motion indicator
                    if i < num_frames - 1:
                        # Color separator based on motion intensity
                        bat_center = frame_data.get('bat_center')
                        separator_color = (0, 255, 0) if bat_center else (100, 100, 100)
                        cv2.line(thumbnail, (x_end - 1, 0), (x_end - 1, frame_height), separator_color, 2)
            
            # Add overall motion indicator border
            if any(frame.get('bat_center') for frame in frames):
                cv2.rectangle(thumbnail, (0, 0), (size[0] - 1, frame_height - 1), (0, 255, 0), 2)
            
            return thumbnail
            
        except Exception as e:
            print(f"[ERROR] Enhanced multi-frame thumbnail creation failed: {e}")
            return None
    
    def enhance_frame_for_validation(self, frame, frame_data):
        """Enhance frame for validation by highlighting motion in ROI/polygons"""
        try:
            enhanced = frame.copy()
            
            # Highlight ROI if available
            if hasattr(self.main_app.detector, 'roi') and self.main_app.detector.roi:
                x, y, w, h = self.main_app.detector.roi
                # Draw ROI with enhanced visibility
                cv2.rectangle(enhanced, (x, y), (x + w, y + h), (0, 255, 255), 2)
                
                # Add ROI label
                cv2.putText(enhanced, "ROI", (x + 5, y + 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            
            # Highlight polygons if available
            if hasattr(self.main_app, 'polygon_areas') and self.main_app.polygon_areas:
                for poly_idx, polygon in enumerate(self.main_app.polygon_areas):
                    if len(polygon) >= 3:
                        pts = np.array(polygon, np.int32)
                        # Draw polygon with semi-transparent fill
                        overlay = enhanced.copy()
                        cv2.fillPoly(overlay, [pts], (0, 255, 0))
                        cv2.addWeighted(enhanced, 0.8, overlay, 0.2, 0, enhanced)
                        
                        # Draw polygon outline
                        cv2.polylines(enhanced, [pts], True, (0, 255, 0), 2)
                        
                        # Add polygon number
                        if len(polygon) > 0:
                            center_x = int(sum(p[0] for p in polygon) / len(polygon))
                            center_y = int(sum(p[1] for p in polygon) / len(polygon))
                            cv2.putText(enhanced, f"#{poly_idx + 1}", (center_x - 10, center_y),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Highlight bat detection with enhanced visibility
            bat_center = frame_data.get('bat_center')
            if bat_center:
                # Main detection circle
                cv2.circle(enhanced, bat_center, 15, (255, 0, 0), 3)
                cv2.circle(enhanced, bat_center, 5, (255, 255, 255), -1)
                
                # Motion trail indicator
                cv2.circle(enhanced, bat_center, 25, (255, 100, 100), 1)
                
                # Add detection label
                cv2.putText(enhanced, "BAT", (bat_center[0] + 20, bat_center[1] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Highlight motion area around detection
                motion_roi = (max(0, bat_center[0] - 30), max(0, bat_center[1] - 30),
                             min(enhanced.shape[1], bat_center[0] + 30), 
                             min(enhanced.shape[0], bat_center[1] + 30))
                cv2.rectangle(enhanced, (motion_roi[0], motion_roi[1]), 
                             (motion_roi[2], motion_roi[3]), (255, 200, 0), 1)
            
            return enhanced
            
        except Exception as e:
            print(f"[WARNING] Frame enhancement failed: {e}")
            return frame
    
    def add_frame_capture_thumbnail(self, parent, event, event_idx, frame_type):
        """Add entry or exit frame capture thumbnail to detailed view"""
        try:
            # Get frame data for this event
            frame_data = None
            if hasattr(self.main_app.detector, 'get_event_frames'):
                frame_data = self.main_app.detector.get_event_frames(event.get('event_id'))
            
            if not frame_data:
                # Fallback: extract frame from video
                frame_data = self.extract_specific_frame(event, frame_type)
            
            if frame_data:
                if frame_type == 'entry':
                    frame = frame_data.get('trigger_frame')
                    if frame is None:
                        frame = frame_data.get('marked_frame')
                else:  # exit
                    frame = frame_data.get('exit_frame')
                    if frame is None:
                        frame = frame_data.get('exit_marked_frame')
                
                if is_valid_frame(frame):
                    # Enhance frame for validation
                    enhanced_frame = self.enhance_frame_for_validation(frame, {
                        'bat_center': event.get('bat_center'),
                        'timestamp': event.get('entry' if frame_type == 'entry' else 'exit', 0)
                    })
                    
                    # Create thumbnail
                    thumbnail = cv2.resize(enhanced_frame, (120, 90))
                    thumbnail_rgb = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(thumbnail_rgb)
                    photo = ImageTk.PhotoImage(pil_image)
                    
                    # Create thumbnail label
                    thumb_label = tk.Label(parent, image=photo, relief="solid", borderwidth=1)
                    thumb_label.image = photo  # Keep reference
                    thumb_label.pack(pady=(5, 0))
                    
                    # Add frame type label
                    frame_label = f"{'Einflug' if frame_type == 'entry' else 'Ausflug'}-Frame"
                    ttk.Label(parent, text=frame_label, font=('Arial', 7), 
                             foreground="#666666").pack()
                    
                    return
            
            # Fallback: show placeholder
            placeholder = tk.Label(parent, text="📷\nKein Frame\nverfügbar", 
                                  width=15, height=6, bg="#f0f0f0", relief="solid", borderwidth=1)
            placeholder.pack(pady=(5, 0))
            
        except Exception as e:
            print(f"[ERROR] Frame capture thumbnail failed: {e}")
            # Show error placeholder with thread safety
            try:
                error_label = tk.Label(parent, text="⚠️\nFehler", width=15, height=6, 
                                     bg="#ffe6e6", relief="solid", borderwidth=1)
                error_label.pack(pady=(5, 0))
            except Exception as gui_error:
                print(f"[ERROR] GUI error in frame capture thumbnail: {gui_error}")
            error_label.pack(pady=(5, 0))
    
    def extract_specific_frame(self, event, frame_type):
        """Extract specific entry or exit frame from video"""
        try:
            if not hasattr(self.main_app.detector, 'video_path') or not self.main_app.detector.video_path:
                return None
                
            cap = cv2.VideoCapture(self.main_app.detector.video_path)
            if not cap.isOpened():
                return None
                
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            
            if frame_type == 'entry':
                target_time = event.get('entry', 0)
            else:  # exit
                target_time = event.get('exit', event.get('entry', 0) + 1)
            
            target_frame = int(target_time * fps)
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                return {
                    'trigger_frame' if frame_type == 'entry' else 'exit_frame': frame,
                    'marked_frame' if frame_type == 'entry' else 'exit_marked_frame': frame
                }
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Frame extraction failed: {e}")
            return None
            return None
    
    def get_event_thumbnail(self, event, event_idx):
        """Get thumbnail for an event using actual captured frames"""
        try:
            # First try to get stored detection frames
            if hasattr(self.main_app.detector, 'get_event_frames'):
                stored_frames = self.main_app.detector.get_event_frames(event.get('event_id'))
                if stored_frames and 'marked_frame' in stored_frames:
                    # Use the actual marked frame that triggered detection
                    marked_frame = stored_frames['marked_frame']
                    return cv2.resize(marked_frame, (200, 150))
            
            # Try to get frame sequence
            if hasattr(self.main_app.detector, 'extract_event_frame_sequence'):
                frame_data = self.main_app.detector.extract_event_frame_sequence(event_idx, num_frames=3)
                if frame_data and frame_data.get('frames'):
                    # Use the middle frame or trigger frame
                    if frame_data.get('trigger_frame'):
                        trigger_frame = frame_data['trigger_frame']
                        if isinstance(trigger_frame, dict) and 'marked_frame' in trigger_frame:
                            frame = trigger_frame['marked_frame']
                        else:
                            frame = trigger_frame
                    else:
                        # Use first available frame
                        first_frame = frame_data['frames'][0]
                        frame = first_frame.get('marked_frame', first_frame.get('frame'))
                    
                    if is_valid_frame(frame):
                        return cv2.resize(frame, (200, 150))
            
            # Use motion thumbnail if available
            if event_idx in self.motion_cache:
                motion_data = self.motion_cache[event_idx]
                thumbnail = self.motion_analyzer.generate_motion_thumbnail(event, motion_data)
                if is_valid_frame(thumbnail):
                    return thumbnail
            
            # Fallback to basic thumbnail
            return self.generate_basic_thumbnail(event)
            
        except Exception as e:
            print(f"[ERROR] Thumbnail generation failed: {e}")
            return None
    
    def generate_basic_thumbnail(self, event):
        """Generate basic thumbnail without motion analysis"""
        try:
            cap = cv2.VideoCapture(self.main_app.video_path)
            if not cap.isOpened():
                return None
            
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            start_time = event.get('entry', 0)
            end_time = event.get('exit', start_time + 1)
            mid_time = (start_time + end_time) / 2
            
            # Get middle frame
            mid_frame = int(mid_time * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Apply highlighting
                highlighted = self.highlight_detection_areas(frame, event)
                return cv2.resize(highlighted, (200, 150))
            
        except Exception as e:
            print(f"[ERROR] Basic thumbnail failed: {e}")
        
        return None
    
    def highlight_detection_areas(self, frame, event):
        """Highlight ROI and detection areas on frame"""
        highlighted = frame.copy()
        
        try:
            # Draw ROI if available
            if hasattr(self.main_app, 'roi') and self.main_app.roi:
                x, y, w, h = self.main_app.roi
                cv2.rectangle(highlighted, (x, y), (x + w, y + h), (0, 255, 255), 2)
            
            # Draw polygons if available
            if hasattr(self.main_app, 'polygon_areas') and self.main_app.polygon_areas:
                for polygon in self.main_app.polygon_areas:
                    if len(polygon) >= 3:
                        pts = np.array(polygon, np.int32)
                        cv2.polylines(highlighted, [pts], True, (0, 255, 0), 2)
            
            # Highlight bat center if available
            if 'bat_center' in event and event['bat_center']:
                center = event['bat_center']
                cv2.circle(highlighted, center, 12, (255, 0, 0), 2)
                cv2.circle(highlighted, center, 4, (255, 255, 255), -1)
            
        except Exception as e:
            print(f"[WARNING] Highlighting failed: {e}")
        
        return highlighted
    
    def add_colored_border(self, pil_image, color, width):
        """Add colored border to PIL image"""
        try:
            # Create new image with border
            new_width = pil_image.width + 2 * width
            new_height = pil_image.height + 2 * width
            
            bordered = Image.new('RGB', (new_width, new_height), color)
            bordered.paste(pil_image, (width, width))
            
            return bordered
        except Exception as e:
            print(f"[WARNING] Border addition failed: {e}")
            return pil_image
    
    def validate_event(self, event_idx, decision):
        """Validate an event with given decision"""
        self.validation_decisions[event_idx] = decision
        
        # Immediately update the event in the main app to persist the decision
        if hasattr(self.main_app.detector, 'events') and event_idx < len(self.main_app.detector.events):
            event = self.main_app.detector.events[event_idx]
            event['validated'] = (decision == 'approved')
            event['validation_decision'] = decision
            event['validation_timestamp'] = datetime.now().isoformat()
        
        # Update progress
        events = self.main_app.detector.events
        progress = (len(self.validation_decisions) / len(events)) * 100
        self.progress_var.set(progress)
        
        # Update statistics and UI
        self.update_validation_statistics()
        
        # Refresh the grid view to show validation status
        self.refresh_event_card(event_idx)
        
        print(f"[INFO] Event {event_idx + 1} marked as {decision}")
        print(f"[INFO] Progress: {len(self.validation_decisions)}/{len(events)} events validated")
    
    def refresh_event_card(self, event_idx):
        """Refresh a specific event card to show validation status"""
        # This would update the specific card, for now just log
    
    def show_detailed_event_view(self, event, event_idx):
        """Show detailed view with video segment"""
        detail_window = tk.Toplevel(self.validation_window)
        detail_window.title(f"🔍 Ereignis {event_idx + 1} - Detailansicht")
        detail_window.transient(self.validation_window)
        
        # Responsive sizing
        screen_width = detail_window.winfo_screenwidth()
        screen_height = detail_window.winfo_screenheight()
        window_width = min(900, int(screen_width * 0.85))
        window_height = min(700, int(screen_height * 0.85))
        detail_window.geometry(f"{window_width}x{window_height}")
        detail_window.minsize(700, 500)
        detail_window.resizable(True, True)
        
        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        detail_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Setup detailed view interface
        self.setup_detailed_view(detail_window, event, event_idx)
    
    def setup_detailed_view(self, window, event, event_idx):
        """Setup the enhanced detailed event view interface with scrollable content and fixed buttons"""
        # Configure window for responsive layout
        window.grid_rowconfigure(0, weight=1)  # Main content area (scrollable)
        window.grid_rowconfigure(1, weight=0)  # Fixed bottom buttons
        window.grid_columnconfigure(0, weight=1)
        
        # Create scrollable main content area
        self.create_scrollable_detail_content(window, event, event_idx)
        
        # Create fixed bottom control buttons
        self.create_fixed_detail_controls(window, event, event_idx)
    
    def create_scrollable_detail_content(self, window, event, event_idx):
        """Create scrollable content area for detailed event information"""
        # Main scrollable container
        scroll_container = ttk.Frame(window)
        scroll_container.grid(row=0, column=0, sticky="nsew", padx=15, pady=(15, 10))
        scroll_container.grid_rowconfigure(0, weight=1)
        scroll_container.grid_columnconfigure(0, weight=1)
        
        # Create canvas and scrollbar for scrolling
        detail_canvas = tk.Canvas(scroll_container, highlightthickness=0)
        detail_scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=detail_canvas.yview)
        
        # Scrollable content frame
        scrollable_detail = ttk.Frame(detail_canvas)
        
        # Configure scrolling
        scrollable_detail.bind(
            "<Configure>",
            lambda e: detail_canvas.configure(scrollregion=detail_canvas.bbox("all"))
        )
        
        detail_canvas.create_window((0, 0), window=scrollable_detail, anchor="nw")
        detail_canvas.configure(yscrollcommand=detail_scrollbar.set)
        
        # Grid layout for canvas and scrollbar
        detail_canvas.grid(row=0, column=0, sticky="nsew")
        detail_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Add mouse wheel support
        def _on_detail_mousewheel(event):
            detail_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def _bind_detail_mousewheel(event):
            detail_canvas.bind_all("<MouseWheel>", _on_detail_mousewheel)
        
        def _unbind_detail_mousewheel(event):
            detail_canvas.unbind_all("<MouseWheel>")
        
        detail_canvas.bind('<Enter>', _bind_detail_mousewheel)
        detail_canvas.bind('<Leave>', _unbind_detail_mousewheel)
        
        # Create all the content in the scrollable frame
        self.populate_detailed_content(scrollable_detail, event, event_idx)
        
        # Store references for scroll region updates
        self.detail_canvas = detail_canvas
        self.scrollable_detail = scrollable_detail
    
    def populate_detailed_content(self, parent, event, event_idx):
        """Populate the scrollable detailed content"""
        main_frame = ttk.Frame(parent, padding=(10, 0))
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Enhanced event info header with structured Einflug/Ausflug/Dauer layout
        info_frame = ttk.LabelFrame(main_frame, text="📋 Ereignis-Information", padding=15)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        start_time = event.get('entry', 0)
        end_time = event.get('exit', start_time + 1)
        duration = event.get('duration', end_time - start_time)
        
        # Create enhanced information grid with clear sections
        header_frame = ttk.Frame(info_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header_frame, text=f"Ereignis {event_idx + 1}", 
                 font=('Arial', 14, 'bold'), foreground="#2B5D8A").pack(anchor=tk.W)
        
        # Enhanced Einflugzeit/Ausflugzeit section with frame captures
        timing_frame = ttk.LabelFrame(info_frame, text="⏱️ Präzise Zeitangaben", padding=15)
        timing_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Calculate precise frame information
        fps = getattr(self.main_app.detector, 'fps', 30) or 30
        entry_frame = int(start_time * fps)
        exit_frame = int(end_time * fps)
        duration_frames = exit_frame - entry_frame
        
        # Create enhanced three-column layout with frame captures
        timing_grid = ttk.Frame(timing_frame)
        timing_grid.pack(fill=tk.X)
        
        # Einflugzeit column with frame capture
        einflug_frame = ttk.Frame(timing_grid)
        einflug_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))
        
        einflug_header = ttk.Label(einflug_frame, text="🟢 Einflugzeit", 
                                  font=('Arial', 11, 'bold'), foreground="#28a745")
        einflug_header.pack(anchor=tk.W)
        
        ttk.Label(einflug_frame, text=f"Zeitstempel: {start_time:.3f}s", 
                 font=('Arial', 9)).pack(anchor=tk.W)
        ttk.Label(einflug_frame, text=f"Frame-Nr.: {entry_frame}", 
                 font=('Arial', 9)).pack(anchor=tk.W)
        
        # Entry frame capture thumbnail
        self.add_frame_capture_thumbnail(einflug_frame, event, event_idx, 'entry')
        
        # Ausflugzeit column with frame capture
        ausflug_frame = ttk.Frame(timing_grid)
        ausflug_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))
        
        ausflug_header = ttk.Label(ausflug_frame, text="🔴 Ausflugzeit", 
                                  font=('Arial', 11, 'bold'), foreground="#dc3545")
        ausflug_header.pack(anchor=tk.W)
        
        ttk.Label(ausflug_frame, text=f"Zeitstempel: {end_time:.3f}s", 
                 font=('Arial', 9)).pack(anchor=tk.W)
        ttk.Label(ausflug_frame, text=f"Frame-Nr.: {exit_frame}", 
                 font=('Arial', 9)).pack(anchor=tk.W)
        
        # Exit frame capture thumbnail
        self.add_frame_capture_thumbnail(ausflug_frame, event, event_idx, 'exit')
        
        # Dauer column with enhanced information
        dauer_frame = ttk.Frame(timing_grid)
        dauer_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        dauer_header = ttk.Label(dauer_frame, text="⏱️ Dauer", 
                                font=('Arial', 11, 'bold'), foreground="#0066CC")
        dauer_header.pack(anchor=tk.W)
        
        ttk.Label(dauer_frame, text=f"Zeit: {duration:.3f}s", 
                 font=('Arial', 9)).pack(anchor=tk.W)
        ttk.Label(dauer_frame, text=f"Frames: {duration_frames}", 
                 font=('Arial', 9)).pack(anchor=tk.W)
        
        # Add motion intensity if available
        if event_idx in self.motion_cache:
            motion_intensity = self.motion_cache[event_idx].get('motion_intensity', 0)
            ttk.Label(dauer_frame, text=f"Bewegung: {motion_intensity:.1%}", 
                     font=('Arial', 8), foreground="#FF6600").pack(anchor=tk.W)
        
        # Additional event details
        details_frame = ttk.LabelFrame(info_frame, text="📍 Zusätzliche Details", padding=10)
        details_frame.pack(fill=tk.X, pady=(0, 10))
        
        details_grid = ttk.Frame(details_frame)
        details_grid.pack(fill=tk.X)
        
        # Polygon information
        if 'polygon_area' in event:
            poly_info_frame = ttk.Frame(details_grid)
            poly_info_frame.pack(fill=tk.X, pady=2)
            ttk.Label(poly_info_frame, text="📍 Polygon-Bereich:", 
                     font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
            ttk.Label(poly_info_frame, text=f"#{event['polygon_area'] + 1}", 
                     font=('Arial', 9), foreground="#8B4513").pack(side=tk.LEFT, padx=(10, 0))
        
        # Bat center coordinates
        if 'bat_center' in event and event['bat_center']:
            center = event['bat_center']
            coord_info_frame = ttk.Frame(details_grid)
            coord_info_frame.pack(fill=tk.X, pady=2)
            ttk.Label(coord_info_frame, text="🎯 Position:", 
                     font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
            ttk.Label(coord_info_frame, text=f"X: {center[0]}, Y: {center[1]}", 
                     font=('Arial', 9)).pack(side=tk.LEFT, padx=(10, 0))
        
        # Motion analysis information
        if event_idx in self.motion_cache:
            motion_data = self.motion_cache[event_idx]
            motion_intensity = motion_data.get('motion_intensity', 0)
            path_length = len(motion_data.get('movement_path', []))
            
            motion_info_frame = ttk.Frame(details_grid)
            motion_info_frame.pack(fill=tk.X, pady=2)
            ttk.Label(motion_info_frame, text="🔥 Bewegungsanalyse:", 
                     font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
            ttk.Label(motion_info_frame, text=f"Intensität: {motion_intensity:.1%}, Pfad: {path_length} Punkte", 
                     font=('Arial', 9), foreground="#FF6600").pack(side=tk.LEFT, padx=(10, 0))
        
        # Frame capture information
        frame_data = None
        if hasattr(self.main_app.detector, 'extract_event_frame_sequence'):
            frame_data = self.main_app.detector.extract_event_frame_sequence(event_idx, num_frames=3)
        
        if frame_data:
            frame_info_frame = ttk.Frame(details_grid)
            frame_info_frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame_info_frame, text="📹 Erfasste Frames:", 
                     font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
            frame_count = len(frame_data.get('frames', []))
            source = frame_data.get('source', 'unbekannt')
            ttk.Label(frame_info_frame, text=f"{frame_count} Frames ({source})", 
                     font=('Arial', 9), foreground="#0066FF").pack(side=tk.LEFT, padx=(10, 0))
        
        # Video preview (scrollable)
        video_frame = ttk.LabelFrame(main_frame, text="🎥 Video-Vorschau", padding=10)
        video_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Video canvas with responsive sizing
        canvas = tk.Canvas(video_frame, bg='black', width=700, height=400)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Load video preview
        self.load_detailed_preview(canvas, event, event_idx)
        
        # Update scroll region after adding content
        self.update_detail_scroll_region()
    
    def create_fixed_detail_controls(self, window, event, event_idx):
        """Create fixed bottom control buttons that are always visible"""
        # Fixed bottom control frame
        control_container = ttk.Frame(window)
        control_container.grid(row=1, column=0, sticky="ew", padx=15, pady=(10, 15))
        control_container.grid_columnconfigure(1, weight=1)  # Spacer column
        
        # Add separator line above buttons
        separator = ttk.Separator(control_container, orient='horizontal')
        separator.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 15))
        
        # Left side buttons (validation)
        validation_frame = ttk.Frame(control_container)
        validation_frame.grid(row=1, column=0, sticky="w")
        
        ttk.Button(validation_frame, text="✅ Genehmigen", 
                  command=lambda: [self.validate_event(event_idx, 'approved'), window.destroy()],
                  style='Accent.TButton',
                  width=15).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(validation_frame, text="❌ Ablehnen", 
                  command=lambda: [self.validate_event(event_idx, 'rejected'), window.destroy()],
                  width=15).pack(side=tk.LEFT, padx=(0, 10))
        
        # Right side buttons (actions)
        action_frame = ttk.Frame(control_container)
        action_frame.grid(row=1, column=3, sticky="e")
        
        ttk.Button(action_frame, text="🎬 Video-Segment", 
                  command=lambda: self.play_event_segment(event),
                  width=16).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(action_frame, text="❌ Schließen", 
                  command=window.destroy,
                  width=12).pack(side=tk.LEFT)
    
    def update_detail_scroll_region(self):
        """Update scroll region for detailed view"""
        if hasattr(self, 'detail_canvas') and hasattr(self, 'scrollable_detail'):
            # Update after a brief delay to ensure content is rendered
            def update_scroll():
                try:
                    self.detail_canvas.update_idletasks()
                    self.detail_canvas.configure(scrollregion=self.detail_canvas.bbox("all"))
                except:
                    pass
            
            # Schedule update
            if hasattr(self, 'validation_window'):
                self.validation_window.after(100, update_scroll)
    
    def load_detailed_preview(self, canvas, event, event_idx):
        """Load detailed preview with actual captured frames"""
        try:
            # Try to get the actual frame sequence that triggered detection
            frame_data = None
            if hasattr(self.main_app.detector, 'extract_event_frame_sequence'):
                frame_data = self.main_app.detector.extract_event_frame_sequence(event_idx, num_frames=5)
            
            if frame_data and frame_data.get('frames'):
                # Create a frame montage showing the detection sequence
                preview_image = self.create_frame_montage(frame_data['frames'])
                
                if is_valid_frame(preview_image):
                    # Convert and display
                    preview_rgb = cv2.cvtColor(preview_image, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(preview_rgb)
                    photo = ImageTk.PhotoImage(pil_image)
                    
                    canvas.create_image(400, 225, image=photo)
                    canvas.image = photo  # Keep reference
                    
                    # Add frame sequence info
                    info_text = f"Captured Frames: {len(frame_data['frames'])} | Source: {frame_data.get('source', 'unknown')}"
                    canvas.create_text(400, 450, text=info_text, fill="white", font=('Arial', 10))
                    return
            
            # Fallback to motion-enhanced preview
            if event_idx in self.motion_cache:
                motion_data = self.motion_cache[event_idx]
                preview_image = self.motion_analyzer.generate_motion_thumbnail(event, motion_data, size=(800, 450))
            else:
                preview_image = self.generate_basic_thumbnail(event)
                if is_valid_frame(preview_image):
                    preview_image = cv2.resize(preview_image, (800, 450))
            
            if is_valid_frame(preview_image):
                # Convert and display
                preview_rgb = cv2.cvtColor(preview_image, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(preview_rgb)
                photo = ImageTk.PhotoImage(pil_image)
                
                canvas.create_image(400, 225, image=photo)
                canvas.image = photo  # Keep reference
            else:
                canvas.create_text(400, 225, text="Vorschau nicht verfügbar", 
                                 fill="white", font=('Arial', 14))
        except Exception as e:
            print(f"[ERROR] Detailed preview failed: {e}")
            canvas.create_text(400, 225, text=f"Fehler: {str(e)}", 
                             fill="red", font=('Arial', 12))
    
    def create_frame_montage(self, frames, target_width=800, target_height=450):
        """Create a montage of multiple frames for detailed view"""
        try:
            if not frames:
                return None
            
            num_frames = len(frames)
            if num_frames == 1:
                frame = frames[0].get('marked_frame', frames[0].get('frame'))
                return cv2.resize(frame, (target_width, target_height))
            
            # Calculate grid layout
            if num_frames <= 3:
                cols = num_frames
                rows = 1
            elif num_frames <= 6:
                cols = 3
                rows = 2
            else:
                cols = 3
                rows = 3
                frames = frames[:9]  # Limit to 9 frames
            
            # Calculate individual frame size
            frame_width = target_width // cols
            frame_height = target_height // rows
            
            # Create montage canvas
            montage = np.zeros((target_height, target_width, 3), dtype=np.uint8)
            
            for idx, frame_data in enumerate(frames):
                if idx >= rows * cols:
                    break
                    
                row = idx // cols
                col = idx % cols
                
                # Get frame (prefer marked frame)
                frame = frame_data.get('marked_frame', frame_data.get('frame'))
                if frame is None:
                    continue
                
                # Resize frame
                resized_frame = cv2.resize(frame, (frame_width, frame_height))
                
                # Add timestamp overlay
                timestamp = frame_data.get('timestamp', 0)
                cv2.putText(resized_frame, f"{timestamp:.2f}s", (5, 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Add frame number
                cv2.putText(resized_frame, f"#{idx + 1}", (5, frame_height - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
                
                # Place in montage
                y_start = row * frame_height
                y_end = y_start + frame_height
                x_start = col * frame_width
                x_end = x_start + frame_width
                
                montage[y_start:y_end, x_start:x_end] = resized_frame
                
                # Add border
                cv2.rectangle(montage, (x_start, y_start), (x_end - 1, y_end - 1), (100, 100, 100), 1)
            
            # Add title
            cv2.putText(montage, "Detection Frame Sequence", (10, target_height - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            return montage
            
        except Exception as e:
            print(f"[ERROR] Frame montage creation failed: {e}")
            return None
    
    def play_event_segment(self, event):
        """Play the video segment for this event"""
        try:
            from validation.manual_validator import SmoothValidationWindow
            
            start_time = event.get('entry', 0)
            end_time = event.get('exit', start_time + 1)
            fps = 30  # Default FPS
            
            if hasattr(self.main_app.detector, 'cap') and self.main_app.detector.cap:
                fps = self.main_app.detector.cap.get(cv2.CAP_PROP_FPS) or 30
            
            start_frame = int(start_time * fps)
            end_frame = int(end_time * fps)
            
            # Get ROI for validation
            roi = None
            if hasattr(self.main_app, 'roi') and self.main_app.roi:
                roi = self.main_app.roi
            
            bat_center = event.get('bat_center', None)
            
            # Create validation window
            validator = SmoothValidationWindow(
                self.main_app.video_path, 
                start_frame, 
                end_frame, 
                roi=roi, 
                bat_center=bat_center
            )
            
            # Run validation
            result = validator.run_validation()
            print(f"[INFO] Event validation result: {result}")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Video-Segment konnte nicht abgespielt werden: {str(e)}")
    
    def populate_motion_view(self):
        """Populate the motion analysis view"""
        # Clear loading message
        if hasattr(self, 'motion_loading_label'):
            self.motion_loading_label.destroy()
        
        # Get the motion tab from the notebook
        motion_tab = None
        for tab_id in self.notebook.tabs():
            tab_text = self.notebook.tab(tab_id, "text")
            if "Bewegungsanalyse" in tab_text:
                motion_tab = self.notebook.nametowidget(tab_id)
                break
        
        if motion_tab is None:
            print("[ERROR] Motion tab not found")
            return
        
        # Create motion analysis interface (using grid to match tab layout)
        motion_frame = ttk.Frame(motion_tab, padding=15)
        motion_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Configure motion_tab grid if not already done
        motion_tab.grid_rowconfigure(1, weight=1)
        motion_tab.grid_columnconfigure(0, weight=1)
        
        # Motion summary
        ttk.Label(motion_frame, text="🔥 Bewegungsanalyse", 
                 font=('Segoe UI', 16, 'bold')).pack(anchor=tk.W, pady=(0, 15))
        
        # Create motion overview canvas
        motion_canvas = tk.Canvas(motion_frame, bg='white', height=400)
        motion_canvas.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Draw motion summary visualization
        self.draw_motion_overview(motion_canvas)
        
        # Motion statistics
        stats_frame = ttk.LabelFrame(motion_frame, text="📊 Bewegungsstatistiken", padding=10)
        stats_frame.pack(fill=tk.X)
        
        self.display_motion_statistics(stats_frame)
        
        # Update scroll region after populating content
        self.update_content_scroll_region()
    
    def draw_motion_overview(self, canvas):
        """Draw motion overview visualization"""
        try:
            events = self.main_app.detector.events
            canvas_width = 800
            canvas_height = 400
            
            if not events:
                return
            
            # Calculate timeline
            min_time = min(event.get('entry', 0) for event in events)
            max_time = max(event.get('exit', min_time + 1) for event in events)
            time_range = max_time - min_time
            
            if time_range <= 0:
                return
            
            # Draw timeline
            margin = 50
            timeline_y = canvas_height - 100
            
            # Draw time axis
            canvas.create_line(margin, timeline_y, canvas_width - margin, timeline_y, width=2)
            
            # Draw events with motion intensity
            for idx, event in enumerate(events):
                start_time = event.get('entry', 0)
                end_time = event.get('exit', start_time + 1)
                
                # Calculate positions
                start_x = margin + ((start_time - min_time) / time_range) * (canvas_width - 2 * margin)
                end_x = margin + ((end_time - min_time) / time_range) * (canvas_width - 2 * margin)
                
                # Get motion intensity
                motion_intensity = 0
                if idx in self.motion_cache:
                    motion_intensity = self.motion_cache[idx].get('motion_intensity', 0)
                
                # Color based on motion intensity
                if motion_intensity > 0.3:
                    color = "#ff4444"  # High motion - red
                elif motion_intensity > 0.1:
                    color = "#ffaa44"  # Medium motion - orange
                else:
                    color = "#44aa44"  # Low motion - green
                
                # Draw event bar
                bar_height = 20 + int(motion_intensity * 50)  # Height based on intensity
                canvas.create_rectangle(start_x, timeline_y - bar_height, end_x, timeline_y, 
                                      fill=color, outline="black", width=1)
                
                # Event label
                canvas.create_text((start_x + end_x) / 2, timeline_y - bar_height - 15, 
                                 text=f"E{idx + 1}", font=('Arial', 8, 'bold'))
            
            # Add legend
            legend_y = 50
            canvas.create_text(canvas_width / 2, 20, text="Bewegungsintensität pro Ereignis", 
                             font=('Arial', 14, 'bold'))
            
            # Legend items
            legend_items = [
                ("Niedrig", "#44aa44"),
                ("Mittel", "#ffaa44"),
                ("Hoch", "#ff4444")
            ]
            
            legend_x = 100
            for label, color in legend_items:
                canvas.create_rectangle(legend_x, legend_y, legend_x + 20, legend_y + 15, 
                                      fill=color, outline="black")
                canvas.create_text(legend_x + 30, legend_y + 7, text=label, anchor="w")
                legend_x += 100
            
        except Exception as e:
            print(f"[ERROR] Motion overview drawing failed: {e}")
    
    def display_motion_statistics(self, parent):
        """Display motion analysis statistics"""
        try:
            events = self.main_app.detector.events
            
            # Calculate statistics
            total_events = len(events)
            analyzed_events = len(self.motion_cache)
            
            high_motion_count = 0
            medium_motion_count = 0
            low_motion_count = 0
            
            total_intensity = 0
            
            for idx, motion_data in self.motion_cache.items():
                intensity = motion_data.get('motion_intensity', 0)
                total_intensity += intensity
                
                if intensity > 0.3:
                    high_motion_count += 1
                elif intensity > 0.1:
                    medium_motion_count += 1
                else:
                    low_motion_count += 1
            
            avg_intensity = total_intensity / max(analyzed_events, 1)
            
            # Display statistics
            stats = [
                f"Analysierte Ereignisse: {analyzed_events}/{total_events}",
                f"Durchschnittliche Bewegungsintensität: {avg_intensity:.1%}",
                f"Hohe Bewegung: {high_motion_count} ({high_motion_count/max(analyzed_events,1)*100:.1f}%)",
                f"Mittlere Bewegung: {medium_motion_count} ({medium_motion_count/max(analyzed_events,1)*100:.1f}%)",
                f"Niedrige Bewegung: {low_motion_count} ({low_motion_count/max(analyzed_events,1)*100:.1f}%)"
            ]
            
            for stat in stats:
                ttk.Label(parent, text=stat).pack(anchor=tk.W, pady=2)
            
        except Exception as e:
            print(f"[ERROR] Statistics display failed: {e}")
    

    def create_enhanced_validation_controls(self, parent):
        """Create enhanced validation controls that stay fixed at bottom"""
        # Main controls container with professional styling
        controls_container = ttk.Frame(parent)
        controls_container.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(0, 0))
        controls_container.grid_columnconfigure(1, weight=1)  # Middle section expands
        
        # Left section: Batch validation actions
        batch_frame = ttk.LabelFrame(controls_container, text="⚡ Schnell-Aktionen", padding=12)
        batch_frame.grid(row=0, column=0, sticky="w", padx=(0, 15))
        
        # Batch action buttons with enhanced styling
        actions_row1 = ttk.Frame(batch_frame)
        actions_row1.pack(fill=tk.X, pady=(0, 6))
        
        ttk.Button(actions_row1, text="✅ Alle genehmigen", 
                  command=self.approve_all_events,
                  style='Accent.TButton',
                  width=16).pack(side=tk.LEFT, padx=(0, 8))
        
        ttk.Button(actions_row1, text="❌ Alle ablehnen", 
                  command=self.reject_all_events,
                  width=16).pack(side=tk.LEFT)
        
        actions_row2 = ttk.Frame(batch_frame)
        actions_row2.pack(fill=tk.X)
        
        ttk.Button(actions_row2, text="🔄 Zurücksetzen", 
                  command=self.reset_validations,
                  width=16).pack(side=tk.LEFT, padx=(0, 8))
        
        ttk.Button(actions_row2, text="🎯 Nur unvalidierte", 
                  command=self.show_unvalidated_only,
                  width=16).pack(side=tk.LEFT)
        
        # Center section: Validation progress and statistics
        progress_frame = ttk.LabelFrame(controls_container, text="📊 Fortschritt", padding=12)
        progress_frame.grid(row=0, column=1, sticky="ew", padx=(0, 15))
        
        # Progress information
        self.validation_stats = ttk.Frame(progress_frame)
        self.validation_stats.pack(fill=tk.X, pady=(0, 8))
        
        # Statistics labels that update dynamically
        self.stats_approved = ttk.Label(self.validation_stats, text="✅ Genehmigt: 0", 
                                       font=('Segoe UI', 9, 'bold'), foreground="#28a745")
        self.stats_approved.pack(side=tk.LEFT, padx=(0, 12))
        
        self.stats_rejected = ttk.Label(self.validation_stats, text="❌ Abgelehnt: 0", 
                                       font=('Segoe UI', 9, 'bold'), foreground="#dc3545")
        self.stats_rejected.pack(side=tk.LEFT, padx=(0, 12))
        
        self.stats_pending = ttk.Label(self.validation_stats, text="⏳ Ausstehend: 0", 
                                      font=('Segoe UI', 9, 'bold'), foreground="#ffc107")
        self.stats_pending.pack(side=tk.LEFT)
        
        # Enhanced progress bar
        progress_container = ttk.Frame(progress_frame)
        progress_container.pack(fill=tk.X)
        
        ttk.Label(progress_container, text="Gesamtfortschritt:", 
                 font=('Segoe UI', 8)).pack(anchor=tk.W)
        
        self.progress_var = tk.DoubleVar()
        self.main_progress_bar = ttk.Progressbar(progress_container, variable=self.progress_var, 
                                               length=250, mode='determinate')
        self.main_progress_bar.pack(fill=tk.X, pady=(2, 0))
        
        # Right section: Primary actions
        action_frame = ttk.LabelFrame(controls_container, text="💾 Aktionen", padding=12)
        action_frame.grid(row=0, column=2, sticky="e")
        
        # Primary action buttons
        primary_actions = ttk.Frame(action_frame)
        primary_actions.pack()
        
        ttk.Button(primary_actions, text="💾 Speichern & Schließen", 
                  command=self.save_and_close,
                  style='Accent.TButton',
                  width=18).pack(pady=(0, 6))
        
        ttk.Button(primary_actions, text="📋 Exportieren", 
                  command=self.export_validation_results,
                  width=18).pack(pady=(0, 6))
        
        ttk.Button(primary_actions, text="❌ Abbrechen", 
                  command=self.close_validation,
                  width=18).pack()
        
        # Update statistics initially
        self.update_validation_statistics()
    
    def update_validation_statistics(self):
        """Update validation statistics in real-time"""
        events = self.main_app.detector.events if hasattr(self.main_app.detector, 'events') else []
        total_events = len(events)
        
        # Count validation decisions
        approved = len([idx for idx, decision in self.validation_decisions.items() if decision == 'approved'])
        rejected = len([idx for idx, decision in self.validation_decisions.items() if decision == 'rejected'])
        pending = total_events - len(self.validation_decisions)
        
        # Update labels
        self.stats_approved.config(text=f"✅ Genehmigt: {approved}")
        self.stats_rejected.config(text=f"❌ Abgelehnt: {rejected}")
        self.stats_pending.config(text=f"⏳ Ausstehend: {pending}")
        
        # Update progress bar
        if total_events > 0:
            progress_percentage = (len(self.validation_decisions) / total_events) * 100
            self.progress_var.set(progress_percentage)
        
        # Update status based on progress
        if len(self.validation_decisions) == total_events:
            self.status_label.config(text="✅ Validierung abgeschlossen", foreground="#28a745")
        elif len(self.validation_decisions) > 0:
            self.status_label.config(text=f"⚡ In Bearbeitung ({len(self.validation_decisions)}/{total_events})", 
                                   foreground="#fd7e14")
        else:
            self.status_label.config(text="⚡ Bereit für Validierung", foreground="#28a745")
    
    def show_unvalidated_only(self):
        """Filter to show only unvalidated events"""
        messagebox.showinfo("Filter", "Zeige nur noch nicht validierte Ereignisse an.")
        # Implementation would filter the display to show only unvalidated events
        
    def export_validation_results(self):
        """Export validation results to file"""
        try:
            from tkinter import filedialog
            import json
            
            # Choose save location
            filename = filedialog.asksaveasfilename(
                title="Validierungsergebnisse exportieren",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                # Prepare export data
                export_data = {
                    'validation_session': {
                        'timestamp': datetime.now().isoformat(),
                        'video_path': self.main_app.video_path,
                        'total_events': len(self.main_app.detector.events),
                        'validation_decisions': self.validation_decisions
                    },
                    'events': []
                }
                
                # Add event details
                for idx, event in enumerate(self.main_app.detector.events):
                    event_data = event.copy()
                    if idx in self.validation_decisions:
                        event_data['validation_decision'] = self.validation_decisions[idx]
                        event_data['validation_timestamp'] = datetime.now().isoformat()
                    export_data['events'].append(event_data)
                
                # Save to file
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("Export erfolgreich", 
                                  f"Validierungsergebnisse wurden erfolgreich exportiert:\n{filename}")
                
        except Exception as e:
            messagebox.showerror("Export-Fehler", f"Fehler beim Exportieren: {str(e)}")
    
    def approve_all_events(self):
        """Approve all events and update statistics"""
        events = self.main_app.detector.events
        for idx in range(len(events)):
            self.validation_decisions[idx] = 'approved'
            # Immediately update each event
            event = events[idx]
            event['validated'] = True
            event['validation_decision'] = 'approved'
            event['validation_timestamp'] = datetime.now().isoformat()
        
        # Update progress
        progress = (len(self.validation_decisions) / len(events)) * 100
        self.progress_var.set(progress)
        
        self.update_validation_statistics()
        print(f"[INFO] All {len(events)} events approved")
        messagebox.showinfo("Alle genehmigt", f"Alle {len(events)} Ereignisse wurden genehmigt.")
    
    def reject_all_events(self):
        """Reject all events and update statistics"""
        events = self.main_app.detector.events
        for idx in range(len(events)):
            self.validation_decisions[idx] = 'rejected'
            # Immediately update each event
            event = events[idx]
            event['validated'] = False
            event['validation_decision'] = 'rejected'
            event['validation_timestamp'] = datetime.now().isoformat()
        
        # Update progress
        progress = (len(self.validation_decisions) / len(events)) * 100
        self.progress_var.set(progress)
        
        self.update_validation_statistics()
        print(f"[INFO] All {len(events)} events rejected")
        messagebox.showinfo("Alle abgelehnt", f"Alle {len(events)} Ereignisse wurden abgelehnt.")
    
    def reset_validations(self):
        """Reset all validation decisions and update statistics"""
        self.validation_decisions.clear()
        
        # Clear validation data from all events
        events = self.main_app.detector.events
        for event in events:
            event['validated'] = False
            event.pop('validation_decision', None)
            event.pop('validation_timestamp', None)
        
        # Reset progress
        self.progress_var.set(0)
        
        self.update_validation_statistics()
        print(f"[INFO] All validation decisions reset")
        messagebox.showinfo("Zurückgesetzt", "Alle Validierungsentscheidungen wurden zurückgesetzt.")
    
    def update_grid_layout(self, event=None):
        """Update grid layout based on user preferences"""
        try:
            # Get current filter and sort settings
            grid_size = getattr(self, 'grid_size_var', None)
            sort_option = getattr(self, 'sort_var', None)
            
            if grid_size:
                grid_size_value = grid_size.get()
            else:
                grid_size_value = "medium"
            
            if sort_option:
                sort_value = sort_option.get()
            else:
                sort_value = "time"
            
            # Clear existing grid content
            if hasattr(self, 'scrollable_grid'):
                for widget in self.scrollable_grid.winfo_children():
                    widget.destroy()
            
            # Repopulate grid with new layout
            self.populate_grid_view()
            
            print(f"[INFO] Grid layout updated: size={grid_size_value}, sort={sort_value}")
            
        except Exception as e:
            print(f"[ERROR] Grid layout update failed: {e}")
    
    def update_timeline(self, event=None):
        """Update timeline display based on user preferences"""
        # Implementation for updating timeline
    
    def load_event_frames(self, event=None):
        """Load frames for selected event"""
        # Implementation for loading event frames
    
    def filter_frames(self, event=None):
        """Filter frames based on type selection"""
        try:
            # Get filter settings
            if hasattr(self, 'frame_type_var'):
                filter_type = self.frame_type_var.get()
            else:
                filter_type = "all"
            
            # Apply filter logic
            if filter_type == "validated":
                # Show only validated events
                self.current_filter = "validated"
            elif filter_type == "unvalidated":
                # Show only unvalidated events  
                self.current_filter = "unvalidated"
            else:
                # Show all events
                self.current_filter = "all"
            
            # Refresh display
            self.populate_grid_view()
            
            print(f"[INFO] Frame filter applied: {filter_type}")
            
        except Exception as e:
            print(f"[ERROR] Frame filtering failed: {e}")
    
    def load_initial_event_frames(self):
        """Load initial event frames"""
        # Mark as loaded to prevent duplicate loading
        self.frames_loaded = True
    
    def update_motion_display(self):
        """Update motion analysis display"""
        # Mark as loaded to prevent duplicate loading
        self.motion_loaded = True
    
    def draw_enhanced_timeline(self):
        """Draw enhanced timeline with better visualization"""
        if hasattr(self, 'timeline_canvas'):
            events = self.main_app.detector.events
            canvas = self.timeline_canvas
            
            # Clear canvas
            canvas.delete("all")
            
            if not events:
                canvas.create_text(400, 200, text="Keine Ereignisse vorhanden", 
                                 font=('Segoe UI', 12), fill="#6c757d")
                return
            
            # Draw timeline
            margin = 50
            canvas_width = 1200
            canvas_height = 300
            
            # Calculate time range
            times = []
            for event in events:
                entry_time = event.get('entry') or event.get('einflugzeit') or 0
                exit_time = event.get('exit') or event.get('ausflugzeit')
                if exit_time is None:
                    exit_time = entry_time + 1
                times.extend([entry_time, exit_time])
            
            if not times:
                return
                
            min_time = min(times)
            max_time = max(times)
            time_range = max_time - min_time
            
            if time_range == 0:
                time_range = 1
            
            # Draw time axis
            y_axis = canvas_height - margin
            canvas.create_line(margin, y_axis, canvas_width - margin, y_axis, width=2, fill="#2B5D8A")
            
            # Draw events
            event_height = 30
            for idx, event in enumerate(events):
                entry_time = event.get('entry') or event.get('einflugzeit') or 0
                exit_time = event.get('exit') or event.get('ausflugzeit')
                if exit_time is None:
                    exit_time = entry_time + 1
                
                # Calculate positions
                x1 = margin + ((entry_time - min_time) / time_range) * (canvas_width - 2 * margin)
                x2 = margin + ((exit_time - min_time) / time_range) * (canvas_width - 2 * margin)
                y1 = y_axis - 50 - (idx % 5) * (event_height + 5)
                y2 = y1 + event_height
                
                # Event color based on validation status
                if idx in self.validation_decisions:
                    if self.validation_decisions[idx] == 'approved':
                        color = "#28a745"
                    else:
                        color = "#dc3545"
                else:
                    color = "#ffc107"
                
                # Draw event bar
                canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#2B5D8A", width=1)
                
                # Event label
                duration = exit_time - entry_time
                label = f"E{idx+1} ({duration:.1f}s)"
                canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=label, 
                                 font=('Segoe UI', 8), fill="white")
            
            # Update canvas scroll region
            canvas.configure(scrollregion=canvas.bbox("all"))
    
    def save_and_close(self):
        """Save validation decisions and close"""
        try:
            # Apply validation decisions to events
            events = self.main_app.detector.events
            validated_events = []
            
            for idx, event in enumerate(events):
                if idx in self.validation_decisions:
                    decision = self.validation_decisions[idx]
                    event['validated'] = (decision == 'approved')
                    event['validation_decision'] = decision
                    event['validation_timestamp'] = datetime.now().isoformat()
                    print(f"[INFO] Applied validation decision for event {idx + 1}: {decision}")
                else:
                    # Unvalidated events are kept as pending
                    event['validated'] = False
                    # Remove old validation data for consistency
                    event.pop('validation_decision', None)
                    event.pop('validation_timestamp', None)
                
                # Add ALL events to the final list, not just approved ones
                validated_events.append(event)
            
            # Update main app with all events (including rejected ones)
            self.main_app.detector.events = validated_events
            
            # Update UI
            validated_count = len([e for e in validated_events if e.get('validated', False)])
            rejected_count = len([idx for idx, decision in self.validation_decisions.items() if decision == 'rejected'])
            
            messagebox.showinfo("Validierung gespeichert", 
                              f"Validierung abgeschlossen!\n\n"
                              f"✅ Genehmigt: {validated_count}\n"
                              f"❌ Abgelehnt: {rejected_count}\n"
                              f"📊 Gesamt: {len(events)}")
            
            self.close_validation()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {str(e)}")
    
    def close_validation(self):
        """Close validation window"""
        try:
            self.validation_window.destroy()
        except:
            pass
    
    def on_window_resize(self, event=None):
        """Handle window resize to update grid layout responsively"""
        try:
            # Only handle resize events for the main validation window
            if event and event.widget != self.validation_window:
                return
                
            # Get current window width
            current_width = self.validation_window.winfo_width()
            
            # Only update if width changed significantly (more than 50px)
            if abs(current_width - self._last_window_width) > 50:
                self._last_window_width = current_width
                
                # Delay the grid update slightly to avoid too frequent updates
                self.validation_window.after(300, self.update_grid_layout_responsive)
                
        except Exception:
            pass  # Fail silently to avoid interrupting user experience
    
    def update_grid_layout_responsive(self):
        """Update grid layout when window is resized"""
        try:
            # Only update if we have events and the grid exists
            if (hasattr(self, 'main_app') and 
                hasattr(self.main_app, 'detector') and 
                hasattr(self.main_app.detector, 'events') and
                self.main_app.detector.events and
                hasattr(self, 'scrollable_grid')):
                
                print(f"[INFO] Updating grid layout for window width: {self._last_window_width}px")
                
                # Clear current grid content
                for widget in self.scrollable_grid.winfo_children():
                    widget.destroy()
                
                # Repopulate with new column layout
                self.populate_grid_view()
                
        except Exception as e:
            print(f"[WARNING] Grid layout update failed: {e}")
    
    def add_motion_visualization(self, event_idx):
        """Add motion visualization for specific event (called after analysis)"""
        # This could update specific UI elements if needed



if __name__ == "__main__":
    print("Enhanced Fast Validation System for Bat Tracking")
    print("This module provides motion visualization and interactive thumbnails")
    print("for rapid event validation without watching full videos.")
