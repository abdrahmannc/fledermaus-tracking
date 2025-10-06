import tkinter as tk
from tkinter import ttk
from gui import parameter_and_ui_helpers as ui_helpers

# Simple tooltip class
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
    
    def on_enter(self, event=None):
        if self.tooltip_window is not None:
            return
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify='left',
                        background="#ffffe0", relief='solid', borderwidth=1,
                        font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)
    
    def on_leave(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

# Fix matplotlib font issues on Windows

# At the top of gui_main.py

# Check for 3D Stereo Extension availability
try:
    STEREO_3D_AVAILABLE = True
except ImportError:
    STEREO_3D_AVAILABLE = False



def create_scrollable_control_panel(self, parent):
        """Creates a scrollable control panel optimized for 14-inch screens"""
        # Control panel container
        control_container = ttk.Frame(parent)
        parent.add(control_container, weight=0)
        
        # Create scrollable frame for controls
        self.control_canvas = tk.Canvas(control_container, bg='#f0f0f0', highlightthickness=0)
        
        # Scrollbar for control panel
        control_scrollbar = ttk.Scrollbar(control_container, orient="vertical", command=self.control_canvas.yview)
        self.scrollable_control_frame = ttk.Frame(self.control_canvas)
        
        # Configure scrolling
        self.scrollable_control_frame.bind(
            "<Configure>",
            lambda e: self.control_canvas.configure(scrollregion=self.control_canvas.bbox("all"))
        )
        
        # Create the scrollable window
        self.control_canvas.create_window((0, 0), window=self.scrollable_control_frame, anchor="nw")
        self.control_canvas.configure(yscrollcommand=control_scrollbar.set)
        
        # Pack scrollable elements
        self.control_canvas.pack(side="left", fill="both", expand=True)
        control_scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel scrolling
        self.control_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_control_frame.bind("<MouseWheel>", self._on_mousewheel)
        
        # Create compact control sections in scrollable frame
        control_frame = ttk.LabelFrame(self.scrollable_control_frame, text="Steuerung", padding=5)  # Reduced from 10
        control_frame.pack(fill=tk.X, padx=3, pady=3)  
        
        # Create all control sections with compact spacing
        self.create_file_controls(control_frame)
        self.create_detection_controls(control_frame)
        self.create_parameter_controls(control_frame)
        self.create_export_controls(control_frame)
        self.create_3d_controls(control_frame)
        
        # Initialize 3D button state
        self.initialize_3d_button_state()
        
        # Optimized width for 14-inch screens
        screen_width = self.root.winfo_screenwidth()
        if screen_width <= 1366:
            # 14-inch screens: narrower control panel
            control_width = 280
            canvas_width = 260
        else:
            # Larger screens: standard width
            control_width = 320
            canvas_width = 300
            
        control_container.configure(width=control_width)
        self.control_canvas.configure(width=canvas_width)
    
def create_display_panel(self, parent):
        """Creates the video display and results panel optimized for 14-inch screens"""
        display_frame = ttk.Frame(parent)
        parent.add(display_frame, weight=1)
        
        # Vertical layout for display panel
        display_paned = ttk.PanedWindow(display_frame, orient=tk.VERTICAL)
        display_paned.pack(fill=tk.BOTH, expand=True)
        
        # Video display area (top)
        self.create_video_area(display_paned)
        
        # Results area (bottom)
        self.create_results_area(display_paned)
        
        # Configure display panel sizing for optimal video control visibility on 14-inch screens
        screen_height = self.root.winfo_screenheight()
        if screen_height <= 768:
            # 14-inch screens: allocate more space for video area to ensure controls are fully visible
            self.root.after(100, lambda: display_paned.sashpos(0, 320))  # Increased from 280
        elif screen_height <= 900:
            # Medium height screens
            self.root.after(100, lambda: display_paned.sashpos(0, 360))  # Increased from 320
        else:
            # Large screens: more video space
            self.root.after(100, lambda: display_paned.sashpos(0, 420))  # Increased from 400
    
def create_video_area(self, parent):
        """Creates responsive video display area optimized for 14-inch screens"""
        video_container = ttk.Frame(parent)
        parent.add(video_container, weight=1)
        
        # Video frame with reduced padding
        video_frame = ttk.LabelFrame(video_container, text="Video-Anzeige", padding=3)  
        video_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=(0, 3))  # Reduced padding
        
        # Responsive canvas size optimized for 14-inch screens
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        if screen_width <= 1366:
            # 14-inch screens: ensure adequate space for video controls below canvas
            canvas_width = min(640, screen_width - 350)
            canvas_height = min(280, screen_height - 400) 
        elif screen_width <= 1600:
            # Medium screens: slightly larger
            canvas_width = min(720, screen_width - 400)
            canvas_height = min(330, screen_height - 420)  
        else:
            # Large screens: full size
            canvas_width = 800
            canvas_height = 420  # Reduced from 450 to ensure controls fit
        
        self.canvas = tk.Canvas(video_frame, bg='#222', 
                               width=canvas_width, height=canvas_height, 
                               highlightthickness=1, relief=tk.SUNKEN)
        self.canvas.pack(expand=True, fill=tk.BOTH, pady=(0, 3))  
        
        # Bind mouse events for polygon drawing
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Motion>", self.on_canvas_motion)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)
        
        # Bind keyboard events for polygon drawing
        self.canvas.bind("<KeyPress-Escape>", self.on_escape_key)
        # Make canvas focusable to receive key events
        self.canvas.config(highlightthickness=1)
        self.canvas.focus_set()
        
        # Video controls (always visible at bottom of video area)
        self.create_video_controls(video_frame)
    
def create_video_controls(self, parent):
        """Creates comprehensive video controls fully optimized for 14-inch screens"""
        video_controls = ttk.Frame(parent)
        video_controls.pack(fill=tk.X, pady=(0, 0))
        
        # Get screen width for responsive adjustments
        screen_width = self.root.winfo_screenwidth()
        
        # Timeline/Progress bar section - ultra-compact for 14-inch screens
        timeline_frame = ttk.Frame(video_controls)
        timeline_frame.pack(fill=tk.X, pady=(0, 2))  # Further reduced from 3
        
        # Timeline label - minimal width
        if screen_width <= 1366:
            timeline_label = ttk.Label(timeline_frame, text="Time:", font=("Arial", 7), width=4)
        else:
            timeline_label = ttk.Label(timeline_frame, text="Timeline:", font=("Arial", 8), width=6)
        timeline_label.pack(side=tk.LEFT, padx=(0, 2))  # Further reduced from 3
        
        # Timeline scale - fully responsive width
        self.timeline_var = tk.DoubleVar(value=0)
        
        # Calculate optimal timeline length based on available space
        if screen_width <= 1366:
            # 14-inch screens: maximize timeline width for full visibility
            timeline_length = min(400, screen_width - 450)  # Ensure timeline extends fully
        elif screen_width <= 1600:
            timeline_length = 450
        else:
            timeline_length = 500
            
        self.timeline_scale = tk.Scale(timeline_frame, 
                                      from_=0, to=100, 
                                      orient=tk.HORIZONTAL,
                                      variable=self.timeline_var,
                                      showvalue=0,
                                      command=self.on_timeline_change,
                                      length=timeline_length)
        self.timeline_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))  # Further reduced from 5
        
        # Time display - compact but fully visible
        self.time_var = tk.StringVar(value="00:00:00 / 00:00:00")
        if screen_width <= 1366:
            time_label = ttk.Label(timeline_frame, textvariable=self.time_var, width=13, font=('Consolas', 7))
        else:
            time_label = ttk.Label(timeline_frame, textvariable=self.time_var, width=15, font=('Consolas', 8))
        time_label.pack(side=tk.LEFT)
        
        # Primary controls row - ultra-compact layout for 14-inch screens
        controls_row1 = ttk.Frame(video_controls)
        controls_row1.pack(fill=tk.X, pady=(0, 1))
        
        # Playback controls - minimal button width for 14-inch screens
        button_width = 2 if screen_width <= 1366 else 3
        button_padding = 0 if screen_width <= 1366 else 1
        
        self.btn_step_back = ttk.Button(controls_row1, text="⏮", command=self.step_backward, 
                                       state=tk.DISABLED, width=button_width, 
                                       style="Video.TButton")
        self.btn_step_back.pack(side=tk.LEFT, padx=button_padding)
        
        self.btn_play = ttk.Button(controls_row1, text="▶", command=self.play_video, 
                                  state=tk.DISABLED, width=button_width,
                                  style="Video.TButton")
        self.btn_play.pack(side=tk.LEFT, padx=button_padding)
        
        self.btn_pause = ttk.Button(controls_row1, text="⏸", command=self.pause_video, 
                                   state=tk.DISABLED, width=button_width,
                                   style="Video.TButton")
        self.btn_pause.pack(side=tk.LEFT, padx=button_padding)
        
        self.btn_stop_video = ttk.Button(controls_row1, text="⏹", command=self.stop_video, 
                                        state=tk.DISABLED, width=button_width,
                                        style="Video.TButton")
        self.btn_stop_video.pack(side=tk.LEFT, padx=button_padding)
        
        self.btn_step_forward = ttk.Button(controls_row1, text="⏭", command=self.step_forward, 
                                          state=tk.DISABLED, width=button_width,
                                          style="Video.TButton")
        self.btn_step_forward.pack(side=tk.LEFT, padx=button_padding)
        
        # Separator - minimal for 14-inch screens
        separator_padx = 3 if screen_width <= 1366 else 5
        ttk.Separator(controls_row1, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=separator_padx)
        
        # Frame navigation - ultra-compact for 14-inch screens
        if screen_width <= 1366:
            ttk.Label(controls_row1, text="Fr:", font=("Arial", 7)).pack(side=tk.LEFT, padx=(0, 1))
            frame_width = 5
        else:
            ttk.Label(controls_row1, text="Frame:", font=("Arial", 8)).pack(side=tk.LEFT, padx=(0, 1))
            frame_width = 6
            
        self.frame_var = tk.StringVar(value="0")
        self.frame_entry = ttk.Entry(controls_row1, textvariable=self.frame_var, width=frame_width, font=("Arial", 7 if screen_width <= 1366 else 8))
        self.frame_entry.pack(side=tk.LEFT, padx=(0, 1))
        self.frame_entry.bind("<Return>", self.goto_frame)
        
        ttk.Button(controls_row1, text="Go", command=self.goto_frame, width=2).pack(side=tk.LEFT, padx=1)
        
        # Speed and time controls (second row) - ultra-compact for 14-inch screens
        controls_row2 = ttk.Frame(video_controls)
        controls_row2.pack(fill=tk.X)
        
        # Speed control - minimal width
        if screen_width <= 1366:
            ttk.Label(controls_row2, text="Spd:", font=("Arial", 7)).pack(side=tk.LEFT, padx=(0, 1))
            speed_width = 4
            speed_font = ("Arial", 7)
        else:
            ttk.Label(controls_row2, text="Speed:", font=("Arial", 8)).pack(side=tk.LEFT, padx=(0, 1))
            speed_width = 5
            speed_font = ("Arial", 8)
            
        self.speed_var = tk.StringVar(value="1.0x")
        self.speed_options = ["0.25x", "0.5x", "1.0x", "1.5x", "2.0x", "3.0x"]
        self.speed_box = ttk.Combobox(controls_row2, textvariable=self.speed_var, 
                                     values=self.speed_options, width=speed_width, state="readonly", font=speed_font)
        self.speed_box.pack(side=tk.LEFT, padx=(0, 3 if screen_width <= 1366 else 5))
        self.speed_box.bind("<<ComboboxSelected>>", self.set_speed)
        
        # Quick jump controls - ultra-compact for 14-inch screens
        jump_label_padx = (3, 1) if screen_width <= 1366 else (5, 1)
        jump_button_width = 3 if screen_width <= 1366 else 4
        
        if screen_width <= 1366:
            ttk.Label(controls_row2, text="Jmp:", font=("Arial", 7)).pack(side=tk.LEFT, padx=jump_label_padx)
        else:
            ttk.Label(controls_row2, text="Jump:", font=("Arial", 8)).pack(side=tk.LEFT, padx=jump_label_padx)
            
        ttk.Button(controls_row2, text="-10s", command=lambda: self.jump_seconds(-10), width=jump_button_width).pack(side=tk.LEFT, padx=0 if screen_width <= 1366 else 1)
        ttk.Button(controls_row2, text="-5s", command=lambda: self.jump_seconds(-5), width=jump_button_width).pack(side=tk.LEFT, padx=0 if screen_width <= 1366 else 1)
        ttk.Button(controls_row2, text="+5s", command=lambda: self.jump_seconds(5), width=jump_button_width).pack(side=tk.LEFT, padx=0 if screen_width <= 1366 else 1)
        ttk.Button(controls_row2, text="+10s", command=lambda: self.jump_seconds(10), width=jump_button_width).pack(side=tk.LEFT, padx=0 if screen_width <= 1366 else 1)
        
        # Initialize timeline variables
        self.seeking = False  # Flag to prevent recursive updates during seeking
    
def create_results_area(self, parent):
        """Creates scrollable results area optimized for 14-inch screens"""
        results_container = ttk.Frame(parent)
        parent.add(results_container, weight=0)
        
        results_frame = ttk.LabelFrame(results_container, text="Erkennungsergebnisse", padding=3)  
        results_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)  
        
        # Results table with scrollbar - more compact
        self.tree = ttk.Treeview(results_frame, columns=('Einflug', 'Ausflug', 'Dauer'), 
                                show='headings', height=4)  # Reduced from 6 for 14-inch screens
        self.tree.heading('Einflug', text='Einflugzeit')
        self.tree.heading('Ausflug', text='Ausflugzeit')
        self.tree.heading('Dauer', text='Dauer')
        
        # Optimize column widths for small screens
        self.tree.column('Einflug', width=100, anchor=tk.CENTER)   
        self.tree.column('Ausflug', width=100, anchor=tk.CENTER)   
        self.tree.column('Dauer', width=80, anchor=tk.CENTER)   
        
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
    
          
def create_file_controls(self, parent):
        """Dateiverwaltungs-Steuerelemente erstellen - kompakt für 14-inch Bildschirme"""
        file_frame = ttk.LabelFrame(parent, text="📁 Datei-Operationen", padding=5)  # Reduced from 8
        file_frame.pack(fill=tk.X, pady=(0, 5))  # Reduced from 8
        
        # Primary file operations
        primary_frame = ttk.Frame(file_frame)
        primary_frame.pack(fill=tk.X, pady=(0, 3))  
        
        self.btn_load = ttk.Button(primary_frame, text="📹 Video laden", 
                                  command=self.load_video, style="PDF.TButton")
        self.btn_load.pack(fill=tk.X, pady=1)
        
        # ROI and polygon controls - more compact layout
        roi_frame = ttk.LabelFrame(file_frame, text="Bereich", padding=2)  
        roi_frame.pack(fill=tk.X, pady=(0, 3))  
        
        # Use grid layout for more compact arrangement
        self.btn_select_roi = ttk.Button(roi_frame, text="🎯 ROI", 
                                        state=tk.DISABLED, command=self.on_select_roi)
        self.btn_select_roi.grid(row=0, column=0, sticky="ew", padx=(0,1), pady=1)
        
        self.btn_toggle_drawing = ttk.Button(roi_frame, text="✏️ Polygon", 
                                           state=tk.DISABLED, command=self.toggle_drawing_mode)
        self.btn_toggle_drawing.grid(row=0, column=1, sticky="ew", padx=1, pady=1)
        
        self.btn_clear_polygons = ttk.Button(roi_frame, text="🗑️ Löschen", 
                                           state=tk.DISABLED, command=self.delete_drawings)
        self.btn_clear_polygons.grid(row=1, column=0, columnspan=2, sticky="ew", pady=1)
        
        # Configure grid weights for ROI buttons
        roi_frame.columnconfigure(0, weight=1)
        roi_frame.columnconfigure(1, weight=1)
        
        # Add tooltip for the clear shapes button
        ToolTip(self.btn_clear_polygons, "Löscht alle gezeichneten Bereiche (ROI oder Polygon).")
        
        # Results access - more compact
        results_frame = ttk.LabelFrame(file_frame, text="Ergebnisse", padding=2)  
        results_frame.pack(fill=tk.X)
        
        # Use grid for results buttons too
        self.btn_previous_results = ttk.Button(results_frame, text="📊 Vorherige", 
                                             command=self.load_previous_video_results)
        self.btn_previous_results.grid(row=0, column=0, sticky="ew", padx=(0,1), pady=1)
        
        self.btn_access_results = ttk.Button(results_frame, text="📂 Öffnen", 
                                           command=self.show_results_access_panel,
                                           style="Accent.TButton")
        self.btn_access_results.grid(row=0, column=1, sticky="ew", padx=1, pady=1)
        
        # Configure grid weights for results buttons
        results_frame.columnconfigure(0, weight=1)
        results_frame.columnconfigure(1, weight=1)
        
        
        
def create_detection_controls(self, parent):
        """Erkennungs-Steuerelemente erstellen - kompakt für 14-inch Bildschirme"""
        detect_frame = ttk.LabelFrame(parent, text="🎯 Erkennung", padding=5)  # Reduced from 8
        detect_frame.pack(fill=tk.X, pady=(0, 5))  # Reduced from 8
        
        # Critical action buttons section - more compact
        critical_frame = ttk.LabelFrame(detect_frame, text="Hauptaktionen", padding=3)  
        critical_frame.pack(fill=tk.X, pady=(0, 3))  
        
        # Use grid for main action buttons to save space
        self.btn_start = ttk.Button(critical_frame, text="🚀 Start", 
                                   state=tk.DISABLED, command=self.start_detection,
                                   style="PDF.TButton")
        self.btn_start.grid(row=0, column=0, sticky="ew", padx=(0,1), pady=1)
        
        self.btn_stop = ttk.Button(critical_frame, text="⏹ Stop", 
                                  state=tk.DISABLED, command=self.stop_detection)
        self.btn_stop.grid(row=0, column=1, sticky="ew", padx=1, pady=1)
        
        # Configure grid weights
        critical_frame.columnconfigure(0, weight=1)
        critical_frame.columnconfigure(1, weight=1)
        
        # 3D Analysis button - full width below main actions
        if STEREO_3D_AVAILABLE:
            self.btn_3d_teil3 = ttk.Button(critical_frame, text="🚀 3D Analyse", 
                                         state=tk.DISABLED, command=self.open_3d_analysis_gui,
                                         style="PDF.TButton")
            self.btn_3d_teil3.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3,1))
        
        # Initialize processing mode variable (default to live mode, no GUI selection)
        self.processing_mode = tk.StringVar(value="live")

        # Window visibility control - more compact
        window_frame = ttk.LabelFrame(detect_frame, text="Fenster", padding=3)  
        window_frame.pack(fill=tk.X, pady=(3, 3))  
        
        # Initialize show_window variable
        self.show_window = tk.BooleanVar(value=True)
        
        self.show_window_checkbox = ttk.Checkbutton(window_frame, 
                                                   text="🖥️ Video-Fenster anzeigen", 
                                                   variable=self.show_window)
        self.show_window_checkbox.pack(anchor="w", pady=1)
        
        window_tooltip = ToolTip(self.show_window_checkbox, 
                                "Aktiviert: Zeigt 'Fledermaus-Erkennung' Fenster mit Video\n"
                                "Deaktiviert: Verarbeitung ohne Video-Anzeige\n"
                                "Erkennungsalgorithmen bleiben identisch")
        
        # Simplified explanation
        window_info_label = ttk.Label(window_frame, 
                                     text="Für Hintergrundverarbeitung deaktivieren",
                                     font=("Arial", 7), foreground="gray")  # Smaller font
        window_info_label.pack(pady=(1, 0))
        
        # Separator
        ttk.Separator(detect_frame, orient='horizontal').pack(fill=tk.X, pady=3)  
        
        # Validation and analysis section - more compact
        analysis_frame = ttk.LabelFrame(detect_frame, text="Analyse", padding=3)  
        analysis_frame.pack(fill=tk.X, pady=(0, 3))  
        
        # Use grid for validation buttons
        self.btn_validate = ttk.Button(analysis_frame, text="✅ Validieren", 
                                     state=tk.DISABLED, command=self.validate_events_gui)
        self.btn_validate.grid(row=0, column=0, sticky="ew", padx=(0,1), pady=1)
        
        self.btn_replay_validation = ttk.Button(analysis_frame, text="▶ Replay", 
                                              state=tk.DISABLED, command=self.replay_validation)
        self.btn_replay_validation.grid(row=0, column=1, sticky="ew", padx=1, pady=1)
        
        # Configure grid weights for validation buttons
        analysis_frame.columnconfigure(0, weight=1)
        analysis_frame.columnconfigure(1, weight=1)
        
        
        
def create_parameter_controls(self, parent):
        """Erkennungsparameter-Steuerelemente erstellen - kompakt für 14-inch Bildschirme"""
        param_frame = ttk.LabelFrame(parent, text="⚙️ Parameter", padding=5)  # Reduced from 8
        param_frame.pack(fill=tk.X, pady=(0, 5))  # Reduced from 8
        
        # Compact parameter layout - 2x2 grid for small screens
        params_grid = ttk.Frame(param_frame)
        params_grid.pack(fill=tk.X)
        
        # Create compact parameter entries in 2x2 grid
        ui_helpers.add_compact_parameter_entry(self, params_grid, "Bewegung:", self.MOTION_THRESHOLD, "threshold", row=0, col=0)
        ui_helpers.add_compact_parameter_entry(self, params_grid, "Abkling:", self.COOLDOWN_FRAMES, "cooldown", row=0, col=1)
        ui_helpers.add_compact_parameter_entry(self, params_grid, "Min. Fläche:", self.MIN_CONTOUR_AREA, "min_area", row=1, col=0)
        ui_helpers.add_compact_parameter_entry(self, params_grid, "Max. Fläche:", self.MAX_CONTOUR_AREA, "max_area", row=1, col=1)
        
        # Configure grid weights for even distribution
        params_grid.columnconfigure(0, weight=1)
        params_grid.columnconfigure(1, weight=1)

    
    
    
    
    

        
def create_export_controls(self, parent):
        """Export-Steuerelemente erstellen - kompakt für 14-inch Bildschirme"""
        export_frame = ttk.LabelFrame(parent, text="📤 Export", padding=5)  # Reduced from 8
        export_frame.pack(fill=tk.X, pady=(0, 5))  # Reduced from 8
        
        # Primary exports - use grid layout for compactness
        primary_export = ttk.LabelFrame(export_frame, text="Berichte", padding=2)  
        primary_export.pack(fill=tk.X, pady=(0, 3))  
        
        self.btn_export_csv = ttk.Button(primary_export, text="📊 CSV", 
                                       state=tk.DISABLED, command=self.export_results)
        self.btn_export_csv.grid(row=0, column=0, sticky="ew", padx=(0,1), pady=1)
        
        self.btn_export_pdf = ttk.Button(primary_export, text="📄 PDF", 
                                       state=tk.DISABLED, command=self.export_pdf_report)
        self.btn_export_pdf.grid(row=0, column=1, sticky="ew", padx=1, pady=1)
        
        # Configure grid weights
        primary_export.columnconfigure(0, weight=1)
        primary_export.columnconfigure(1, weight=1)
        
        # Visualization exports
        viz_export = ttk.LabelFrame(export_frame, text="Visualisierung", padding=2) 
        viz_export.pack(fill=tk.X)
        
        self.btn_export_flightMap = ttk.Button(viz_export, text="🗺️ Flugkarte", 
                                             state=tk.DISABLED, command=self.export_flightMap)
        self.btn_export_flightMap.pack(fill=tk.X, pady=1)
        
def create_3d_controls(self, parent):
        """3D Stereo-Steuerelemente erstellen - kompakt für 14-inch Bildschirme"""
        if not STEREO_3D_AVAILABLE:
            return
            
        # Compact 3D controls frame
        stereo_frame = ttk.LabelFrame(parent, text="🎯 3D Modus", padding=5)  # Reduced from 8
        stereo_frame.pack(fill=tk.X, pady=(0, 5))  # Reduced from 8
        
        # Mode selection - more compact layout
        self.mode_var = tk.StringVar(value="2D")
        
        mode_frame = ttk.Frame(stereo_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 3))  
        
        ttk.Label(mode_frame, text="Modus:", font=("Arial", 8)).pack(side=tk.LEFT)
        
        self.btn_mode_2d = ttk.Radiobutton(mode_frame, text="2D", 
                                          variable=self.mode_var, value="2D",
                                          command=self.switch_to_2d_mode)
        self.btn_mode_2d.pack(side=tk.LEFT, padx=(5, 3))  # Reduced padding
        
        self.btn_mode_3d = ttk.Radiobutton(mode_frame, text="3D", 
                                          variable=self.mode_var, value="3D",
                                          command=self.switch_to_3d_mode)
        self.btn_mode_3d.pack(side=tk.LEFT, padx=3)  # Reduced padding
        
        # 3D specific controls (initially hidden) - more compact
        self.stereo_3d_frame = ttk.LabelFrame(stereo_frame, text="3D Einstellungen", padding=3)  
        
        # Stereo mode selection - compact
        stereo_mode_frame = ttk.Frame(self.stereo_3d_frame)
        stereo_mode_frame.pack(fill=tk.X, pady=(0, 2))  
        
        ttk.Label(stereo_mode_frame, text="Stereo:", font=("Arial", 8)).pack(side=tk.LEFT)
        self.stereo_mode_var = tk.StringVar(value="side_by_side")
        stereo_combo = ttk.Combobox(stereo_mode_frame, textvariable=self.stereo_mode_var,
                                   values=["side_by_side", "top_bottom"], width=10, state="readonly")
        stereo_combo.pack(side=tk.RIGHT)
        
        # Calibration and visualization - use grid for compactness
        controls_grid = ttk.Frame(self.stereo_3d_frame)
        controls_grid.pack(fill=tk.X, pady=2)  
        
        self.btn_calibrate = ttk.Button(controls_grid, text="📐 Kalibrieren", 
                                       command=self.start_stereo_calibration)
        self.btn_calibrate.grid(row=0, column=0, sticky="ew", padx=(0,1), pady=1)
        
        self.btn_3d_viz = ttk.Button(controls_grid, text="🎬 3D Viz", 
                                    state=tk.DISABLED, command=self.show_3d_visualization)
        self.btn_3d_viz.grid(row=0, column=1, sticky="ew", padx=1, pady=1)
        
        # Configure grid weights
        controls_grid.columnconfigure(0, weight=1)
        controls_grid.columnconfigure(1, weight=1)
    
    
    
    
    
class helpers: 
    def _on_mousewheel(self, event):
            """Handle mouse wheel scrolling in control panel"""
            if self.control_canvas.winfo_exists():
                self.control_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
  
    