"""
3D Stereo GUI Extensions

This module extends the existing GUI with 3D stereo capabilities
while preserving all existing 2D functionality.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from detection.stereo_detector import StereoDetector


class StereoGUIExtension:
    """GUI extension for 3D stereo functionality"""
    
    def __init__(self, main_app):
        self.main_app = main_app
        self.stereo_detector = None
        self.stereo_mode = False
        
    def integrate_stereo_controls(self):
        """Integrate stereo controls into existing GUI"""
        # Add 3D tab to existing control panel
        self._add_stereo_tab()
        
        # Extend detection controls
        self._extend_detection_controls()
        
        # Add 3D export options
        self._add_3d_export_options()
        
        # Replace detector with stereo-enabled version
        self._replace_detector()
    
    def _add_stereo_tab(self):
        """Add 3D stereo tab to existing GUI"""
        # Find existing notebook/tabs in main GUI
        # This preserves existing tab structure
        
        # Create new 3D stereo frame
        stereo_frame = ttk.LabelFrame(self.main_app.control_frame, text="3D Stereo Detection", padding=10)
        stereo_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Mode selection
        mode_frame = ttk.Frame(stereo_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(mode_frame, text="Detection Mode:", font=('Segoe UI', 9, 'bold')).pack(anchor=tk.W)
        
        self.detection_mode = tk.StringVar(value="2d")
        
        ttk.Radiobutton(mode_frame, text="🎥 2D (Traditional)", 
                       variable=self.detection_mode, value="2d",
                       command=self._on_mode_change).pack(anchor=tk.W)
        
        ttk.Radiobutton(mode_frame, text="🎭 3D Stereo", 
                       variable=self.detection_mode, value="3d",
                       command=self._on_mode_change).pack(anchor=tk.W)
        
        ttk.Radiobutton(mode_frame, text="🔄 Hybrid (2D+3D)", 
                       variable=self.detection_mode, value="hybrid",
                       command=self._on_mode_change).pack(anchor=tk.W)
        
        # Stereo video loading
        video_frame = ttk.LabelFrame(stereo_frame, text="Stereo Video Pair", padding=5)
        video_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_load_left = ttk.Button(video_frame, text="📹 Load Left Camera", 
                                       command=self._load_left_video, state=tk.DISABLED)
        self.btn_load_left.pack(fill=tk.X, pady=2)
        
        self.btn_load_right = ttk.Button(video_frame, text="📹 Load Right Camera", 
                                        command=self._load_right_video, state=tk.DISABLED)
        self.btn_load_right.pack(fill=tk.X, pady=2)
        
        # Calibration loading
        calib_frame = ttk.LabelFrame(stereo_frame, text="Camera Calibration", padding=5)
        calib_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_load_calibration = ttk.Button(calib_frame, text="📐 Load Calibration", 
                                              command=self._load_calibration, state=tk.DISABLED)
        self.btn_load_calibration.pack(fill=tk.X, pady=2)
        
        self.btn_auto_calibrate = ttk.Button(calib_frame, text="🔧 Auto Calibrate", 
                                            command=self._auto_calibrate, state=tk.DISABLED)
        self.btn_auto_calibrate.pack(fill=tk.X, pady=2)
        
        # Status display
        self.stereo_status = tk.StringVar(value="2D Mode - Traditional detection")
        status_label = ttk.Label(stereo_frame, textvariable=self.stereo_status, 
                                font=('Segoe UI', 8), foreground="#666")
        status_label.pack(anchor=tk.W, pady=(5, 0))
    
    def _extend_detection_controls(self):
        """Extend existing detection controls for 3D"""
        # Modify existing detection button to handle stereo
        if hasattr(self.main_app, 'btn_start_detection'):
            self.main_app.btn_start_detection['command']
            self.main_app.btn_start_detection.configure(command=self._enhanced_start_detection)
    
    def _add_3d_export_options(self):
        """Add 3D export options to existing export menu"""
        # Find existing export frame
        if hasattr(self.main_app, 'create_export_controls'):
            # Add 3D export buttons
            export_frame = None
            
            # Find export frame in GUI hierarchy
            for widget in self.main_app.control_frame.winfo_children():
                if isinstance(widget, ttk.LabelFrame) and "export" in widget['text'].lower():
                    export_frame = widget
                    break
            
            if export_frame:
                # Add separator
                ttk.Separator(export_frame, orient='horizontal').pack(fill=tk.X, pady=5)
                
                # 3D Export section
                ttk.Label(export_frame, text="3D Exports:", 
                         font=('Segoe UI', 9, 'bold')).pack(anchor=tk.W, pady=(5, 2))
                
                self.btn_export_3d_json = ttk.Button(export_frame, text="📊 3D JSON Export", 
                                                    state=tk.DISABLED, command=self._export_3d_json)
                self.btn_export_3d_json.pack(fill=tk.X, pady=1)
                
                self.btn_export_3d_csv = ttk.Button(export_frame, text="📈 3D CSV Export", 
                                                   state=tk.DISABLED, command=self._export_3d_csv)
                self.btn_export_3d_csv.pack(fill=tk.X, pady=1)
                
                self.btn_export_point_cloud = ttk.Button(export_frame, text="☁️ Point Cloud (PLY)", 
                                                        state=tk.DISABLED, command=self._export_point_cloud)
                self.btn_export_point_cloud.pack(fill=tk.X, pady=1)
                
                self.btn_export_3d_visualization = ttk.Button(export_frame, text="🎯 3D Visualization", 
                                                             state=tk.DISABLED, command=self._export_3d_viz)
                self.btn_export_3d_visualization.pack(fill=tk.X, pady=1)
    
    def _replace_detector(self):
        """Replace 2D detector with stereo-enabled detector"""
        # Create stereo detector that wraps existing functionality
        self.stereo_detector = StereoDetector(self.main_app, mode="2d")
        
        # Replace detector reference in main app
        self.main_app.detector = self.stereo_detector
    
    def _on_mode_change(self):
        """Handle detection mode change"""
        mode = self.detection_mode.get()
        
        if mode == "2d":
            # Enable traditional controls, disable stereo
            self.btn_load_left.configure(state=tk.DISABLED)
            self.btn_load_right.configure(state=tk.DISABLED)
            self.btn_load_calibration.configure(state=tk.DISABLED)
            self.btn_auto_calibrate.configure(state=tk.DISABLED)
            self.stereo_status.set("2D Mode - Traditional detection")
            self.stereo_mode = False
            
            # Enable traditional video loading
            if hasattr(self.main_app, 'btn_load_video'):
                self.main_app.btn_load_video.configure(state=tk.NORMAL)
            
        elif mode in ["3d", "hybrid"]:
            # Enable stereo controls
            self.btn_load_left.configure(state=tk.NORMAL)
            self.btn_load_right.configure(state=tk.NORMAL)
            self.btn_load_calibration.configure(state=tk.NORMAL)
            self.btn_auto_calibrate.configure(state=tk.NORMAL)
            self.stereo_status.set(f"{mode.upper()} Mode - Stereo detection enabled")
            self.stereo_mode = True
            
            # Disable traditional video loading in pure 3D mode
            if mode == "3d" and hasattr(self.main_app, 'btn_load_video'):
                self.main_app.btn_load_video.configure(state=tk.DISABLED)
        
        # Update detector mode
        if self.stereo_detector:
            self.stereo_detector.set_detection_mode(mode)
    
    def _load_left_video(self):
        """Load left camera video"""
        file_path = filedialog.askopenfilename(
            title="Select Left Camera Video",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov"), ("All Files", "*.*")]
        )
        
        if file_path:
            self.left_video_path = file_path
            self.main_app.update_status(f"Left camera loaded: {os.path.basename(file_path)}")
            self._check_stereo_ready()
    
    def _load_right_video(self):
        """Load right camera video"""
        file_path = filedialog.askopenfilename(
            title="Select Right Camera Video",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov"), ("All Files", "*.*")]
        )
        
        if file_path:
            self.right_video_path = file_path
            self.main_app.update_status(f"Right camera loaded: {os.path.basename(file_path)}")
            self._check_stereo_ready()
    
    def _load_calibration(self):
        """Load stereo calibration file"""
        file_path = filedialog.askopenfilename(
            title="Select Stereo Calibration File",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        
        if file_path and self.stereo_detector:
            if self.stereo_detector.load_calibration(file_path):
                self.main_app.update_status("Stereo calibration loaded successfully")
                self._check_stereo_ready()
            else:
                messagebox.showerror("Error", "Failed to load stereo calibration")
    
    def _auto_calibrate(self):
        """Open auto-calibration dialog"""
        messagebox.showinfo("Auto Calibration", 
                          "Auto-calibration feature coming soon!\n\n"
                          "For now, please use pre-calibrated stereo parameters or "
                          "external calibration tools like OpenCV's stereo calibration.")
    
    def _check_stereo_ready(self):
        """Check if stereo setup is ready for detection"""
        if hasattr(self, 'left_video_path') and hasattr(self, 'right_video_path'):
            if self.stereo_detector:
                success = self.stereo_detector.load_stereo_videos(
                    self.left_video_path, self.right_video_path
                )
                
                if success:
                    self.stereo_status.set("Stereo videos loaded - Ready for 3D detection")
                    self._enable_3d_controls()
                else:
                    self.stereo_status.set("Error: Stereo videos incompatible")
                    messagebox.showerror("Stereo Error", 
                                       "Stereo videos are not compatible. Please check:\n"
                                       "- Frame counts match\n"
                                       "- Frame rates match\n"
                                       "- Resolutions match")
    
    def _enable_3d_controls(self):
        """Enable 3D-specific controls after successful setup"""
        # Enable detection button for 3D mode
        if hasattr(self.main_app, 'btn_start_detection'):
            self.main_app.btn_start_detection.configure(state=tk.NORMAL)
        
        # Enable 3D export buttons when detection is complete
        # This will be handled in the detection completion callback
    
    def _enhanced_start_detection(self):
        """Enhanced detection start that handles both 2D and 3D modes"""
        mode = self.detection_mode.get()
        
        if mode == "2d":
            # Use traditional 2D detection
            if self.stereo_detector:
                self.stereo_detector.start_detection()
            
        elif mode in ["3d", "hybrid"]:
            # Use stereo detection
            if not hasattr(self, 'left_video_path') or not hasattr(self, 'right_video_path'):
                messagebox.showwarning("Missing Videos", 
                                     "Please load both left and right camera videos for 3D detection.")
                return
            
            if not self.stereo_detector.calibration:
                response = messagebox.askyesno("No Calibration", 
                                             "No stereo calibration loaded. Continue with uncalibrated detection?\n\n"
                                             "Note: Without calibration, 3D positions will be less accurate.")
                if not response:
                    return
            
            # Start stereo detection
            self.stereo_detector.start_stereo_detection()
            
            # Set callback for when detection completes
            self._setup_detection_callback()
    
    def _setup_detection_callback(self):
        """Setup callback for when detection completes"""
        # This would integrate with existing detection completion handling
        # The stereo detector already converts events to 2D-compatible format
        def check_completion():
            if not self.stereo_detector.stereo_processing:
                # Detection completed - enable 3D exports
                self.btn_export_3d_json.configure(state=tk.NORMAL)
                self.btn_export_3d_csv.configure(state=tk.NORMAL)
                self.btn_export_point_cloud.configure(state=tk.NORMAL)
                self.btn_export_3d_visualization.configure(state=tk.NORMAL)
                
                # Enable existing 2D exports (they work with 3D data too)
                if hasattr(self.main_app, 'btn_export_csv'):
                    self.main_app.btn_export_csv.configure(state=tk.NORMAL)
                if hasattr(self.main_app, 'btn_export_pdf'):
                    self.main_app.btn_export_pdf.configure(state=tk.NORMAL)
                
                self.main_app.update_status("3D Detection completed - All exports available")
                return
            
            # Check again in 1 second
            self.main_app.root.after(1000, check_completion)
        
        # Start checking
        self.main_app.root.after(1000, check_completion)
    
    def _export_3d_json(self):
        """Export 3D detection data as JSON"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save 3D Detection Data"
        )
        
        if file_path and self.stereo_detector:
            try:
                self.stereo_detector.export_3d_data(file_path, "json")
                messagebox.showinfo("Export Success", f"3D data exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export 3D data:\n{str(e)}")
    
    def _export_3d_csv(self):
        """Export 3D detection data as CSV"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save 3D Detection CSV"
        )
        
        if file_path and self.stereo_detector:
            try:
                self.stereo_detector.export_3d_data(file_path, "csv")
                messagebox.showinfo("Export Success", f"3D CSV exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export 3D CSV:\n{str(e)}")
    
    def _export_point_cloud(self):
        """Export 3D point cloud as PLY"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".ply",
            filetypes=[("PLY files", "*.ply"), ("All files", "*.*")],
            title="Save Point Cloud"
        )
        
        if file_path and self.stereo_detector:
            try:
                self.stereo_detector.export_3d_data(file_path, "ply")
                messagebox.showinfo("Export Success", f"Point cloud exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export point cloud:\n{str(e)}")
    
    def _export_3d_viz(self):
        """Export 3D visualization"""
        try:
            from visualization.stereo_visualization import create_3d_flight_visualization
            
            if self.stereo_detector:
                trajectory_data = self.stereo_detector.get_3d_trajectory_data()
                
                if not trajectory_data:
                    messagebox.showwarning("No 3D Data", "No 3D trajectory data available for visualization.")
                    return
                
                # Create 3D visualization
                output_path = create_3d_flight_visualization(
                    trajectory_data, 
                    self.left_video_path if hasattr(self, 'left_video_path') else None
                )
                
                if output_path:
                    messagebox.showinfo("Visualization Created", f"3D visualization saved to:\n{output_path}")
                else:
                    messagebox.showerror("Error", "Failed to create 3D visualization")
            
        except ImportError:
            messagebox.showinfo("Feature Coming Soon", 
                              "3D visualization feature is being developed.\n"
                              "Use the PLY export to view point clouds in external tools like CloudCompare or MeshLab.")
        except Exception as e:
            messagebox.showerror("Visualization Error", f"Failed to create 3D visualization:\n{str(e)}")

    def setup_stereo_interface(self, parent_window):
        """Setup the responsive dedicated 3D stereo interface in a separate window"""
        try:
            # Get screen dimensions for responsive design
            screen_width = parent_window.winfo_screenwidth()
            screen_height = parent_window.winfo_screenheight()
            
            # Set responsive window size
            if screen_width <= 1366:
                # Small screen - compact layout
                window_padding = 15
                section_padding = 10
                font_size_title = 14
                font_size_normal = 9
            else:
                # Large screen - spacious layout
                window_padding = 20
                section_padding = 15
                font_size_title = 16
                font_size_normal = 10
            
            # Main container with responsive padding
            main_frame = ttk.Frame(parent_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=window_padding, pady=window_padding)
            
            # Create scrollable container for small screens
            if screen_height <= 768:
                # Create scrollable frame for small screens
                canvas = tk.Canvas(main_frame, highlightthickness=0)
                scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
                scrollable_frame = ttk.Frame(canvas)
                
                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                )
                
                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)
                
                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")
                
                # Mouse wheel scrolling
                canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
                
                container = scrollable_frame
            else:
                container = main_frame
            
            # Title and description - responsive font sizes
            title_frame = ttk.Frame(container)
            title_frame.pack(fill=tk.X, pady=(0, section_padding))
            
            ttk.Label(title_frame, text="🚀 3D Stereo-Flugbahn-Analyse", 
                     font=('Segoe UI', font_size_title, 'bold')).pack(anchor=tk.W)
            ttk.Label(title_frame, text="Laden Sie Stereo-Kamera Videos für 3D-Flugbahn-Extraktion", 
                     font=('Segoe UI', font_size_normal)).pack(anchor=tk.W, pady=(5, 0))
            
            # Video loading section - compact for small screens
            video_frame = ttk.LabelFrame(container, text="Stereo-Video Laden", padding=section_padding)
            video_frame.pack(fill=tk.X, pady=(0, section_padding))
            
            # Left video - compact layout
            left_frame = ttk.Frame(video_frame)
            left_frame.pack(fill=tk.X, pady=(0, 8))
            ttk.Label(left_frame, text="Linke Kamera:", font=('Segoe UI', font_size_normal, 'bold')).pack(anchor=tk.W)
            self.left_video_var = tk.StringVar(value="Keine Datei ausgewählt")
            ttk.Label(left_frame, textvariable=self.left_video_var, foreground='#666', 
                     font=('Segoe UI', font_size_normal-1)).pack(anchor=tk.W, pady=(2, 3))
            ttk.Button(left_frame, text="📹 Linkes Video laden", command=self._load_left_video).pack(anchor=tk.W)
            
            # Right video - compact layout
            right_frame = ttk.Frame(video_frame)
            right_frame.pack(fill=tk.X, pady=(0, 8))
            ttk.Label(right_frame, text="Rechte Kamera:", font=('Segoe UI', font_size_normal, 'bold')).pack(anchor=tk.W)
            self.right_video_var = tk.StringVar(value="Keine Datei ausgewählt")
            ttk.Label(right_frame, textvariable=self.right_video_var, foreground='#666',
                     font=('Segoe UI', font_size_normal-1)).pack(anchor=tk.W, pady=(2, 3))
            ttk.Button(right_frame, text="📹 Rechtes Video laden", command=self._load_right_video).pack(anchor=tk.W)
            
            # Analysis section - responsive layout
            analysis_frame = ttk.LabelFrame(container, text="3D-Analyse", padding=section_padding)
            analysis_frame.pack(fill=tk.X, pady=(0, section_padding))
            
            # Analysis controls - prominent button
            self.analysis_btn = ttk.Button(analysis_frame, text="🚀 3D-Analyse starten", 
                                         command=self._start_stereo_analysis, state=tk.DISABLED,
                                         style="PDF.TButton")
            self.analysis_btn.pack(anchor=tk.W, pady=(0, 8))
            
            # Progress
            self.progress_var = tk.StringVar(value="Bereit für Video-Upload")
            ttk.Label(analysis_frame, textvariable=self.progress_var).pack(anchor=tk.W)
            
            # Results section
            results_frame = ttk.LabelFrame(main_frame, text="3D-Ergebnisse", padding=15)
            results_frame.pack(fill=tk.BOTH, expand=True)
            
            # Results controls
            results_controls = ttk.Frame(results_frame)
            results_controls.pack(fill=tk.X, pady=(0, 10))
            
            self.viz_btn = ttk.Button(results_controls, text="📊 3D-Visualisierung", 
                                    command=self._create_3d_visualization, state=tk.DISABLED)
            self.viz_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            self.export_btn = ttk.Button(results_controls, text="💾 3D-Daten exportieren", 
                                       command=self._export_3d_data, state=tk.DISABLED)
            self.export_btn.pack(side=tk.LEFT, padx=(0, 10))
            
            self.gis_btn = ttk.Button(results_controls, text="🗺️ GIS-Export", 
                                    command=self._export_gis_data, state=tk.DISABLED)
            self.gis_btn.pack(side=tk.LEFT)
            
            # Results display area
            results_text = tk.Text(results_frame, height=10, state=tk.DISABLED, wrap=tk.WORD)
            results_scroll = ttk.Scrollbar(results_frame, orient="vertical", command=results_text.yview)
            results_text.configure(yscrollcommand=results_scroll.set)
            
            results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            results_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.results_text = results_text
            
            # Add initial message
            self._update_results_text("🎬 Willkommen bei der 3D Stereo-Analyse!\n\n"
                                    "1. Laden Sie zuerst die Videos von beiden Kameras\n"
                                    "2. Starten Sie die 3D-Analyse\n"
                                    "3. Visualisieren und exportieren Sie die Ergebnisse\n\n"
                                    "Bereit für den Start...")
            
        except Exception as e:
            messagebox.showerror("GUI Error", f"Fehler beim Erstellen der 3D-Oberfläche: {e}")
    
    def _update_results_text(self, text):
        """Update the results text area"""
        if hasattr(self, 'results_text'):
            self.results_text.config(state=tk.NORMAL)
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, text)
            self.results_text.config(state=tk.DISABLED)
    
    def _load_left_video(self):
        """Load left camera video"""
        filename = filedialog.askopenfilename(
            title="Linkes Kamera-Video auswählen",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )
        if filename:
            self.left_video_path = filename
            self.left_video_var.set(os.path.basename(filename))
            self.progress_var.set("Linkes Video geladen")
            self._check_ready_for_analysis()
    
    def _load_right_video(self):
        """Load right camera video"""
        filename = filedialog.askopenfilename(
            title="Rechtes Kamera-Video auswählen",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )
        if filename:
            self.right_video_path = filename
            self.right_video_var.set(os.path.basename(filename))
            self.progress_var.set("Rechtes Video geladen")
            self._check_ready_for_analysis()
    
    def _check_ready_for_analysis(self):
        """Check if ready for analysis and enable button"""
        if hasattr(self, 'left_video_path') and hasattr(self, 'right_video_path'):
            if self.left_video_path and self.right_video_path:
                self.analysis_btn.config(state=tk.NORMAL)
                self.progress_var.set("Bereit für 3D-Analyse")
                self._update_results_text("✅ Beide Videos geladen!\n\n"
                                        f"Linke Kamera: {os.path.basename(self.left_video_path)}\n"
                                        f"Rechte Kamera: {os.path.basename(self.right_video_path)}\n\n"
                                        "Klicken Sie '3D-Analyse starten' um fortzufahren.")
    
    def _start_stereo_analysis(self):
        """Start stereo analysis"""
        try:
            self.progress_var.set("Starte 3D-Analyse...")
            self._update_results_text("🚀 3D-Analyse gestartet...\n\nDies kann einige Minuten dauern.\nBitte warten Sie...")
            
            # Initialize stereo detector if needed
            if not self.stereo_detector:
                from detection.stereo_detector import StereoDetector
                self.stereo_detector = StereoDetector()
            
            # Load stereo videos
            success = self.stereo_detector.load_stereo_videos(self.left_video_path, self.right_video_path)
            if not success:
                messagebox.showerror("Fehler", "Stereo-Videos konnten nicht geladen werden")
                return
            
            # Run analysis (simplified - in real implementation this would be threaded)
            self.progress_var.set("Analysiere Stereo-Videos...")
            results = self.stereo_detector.run_stereo_analysis()
            
            if results:
                self.progress_var.set("3D-Analyse abgeschlossen!")
                self._update_results_text(f"✅ 3D-Analyse erfolgreich abgeschlossen!\n\n"
                                        f"Erkannte 3D-Ereignisse: {len(results.get('events', []))}\n"
                                        f"3D-Trajektorien-Punkte: {len(results.get('trajectory_3d', []))}\n\n"
                                        "Sie können jetzt die Ergebnisse visualisieren und exportieren.")
                
                # Enable result buttons
                self.viz_btn.config(state=tk.NORMAL)
                self.export_btn.config(state=tk.NORMAL)
                self.gis_btn.config(state=tk.NORMAL)
            else:
                messagebox.showerror("Fehler", "3D-Analyse fehlgeschlagen")
                
        except Exception as e:
            messagebox.showerror("Analyse-Fehler", f"Fehler bei der 3D-Analyse: {e}")
            self.progress_var.set("Analyse fehlgeschlagen")
    
    def _create_3d_visualization(self):
        """Create 3D visualization"""
        try:
            from visualization.stereo_visualization import create_3d_flight_visualization
            
            if self.stereo_detector:
                trajectory_data = self.stereo_detector.get_3d_trajectory_data()
                if trajectory_data:
                    output_path = create_3d_flight_visualization(trajectory_data, self.left_video_path)
                    if output_path:
                        messagebox.showinfo("Visualisierung erstellt", f"3D-Visualisierung gespeichert:\n{output_path}")
                        os.startfile(output_path)  # Open with default application
                    else:
                        messagebox.showerror("Fehler", "Visualisierung konnte nicht erstellt werden")
                else:
                    messagebox.showwarning("Keine Daten", "Keine 3D-Trajektoriendaten verfügbar")
        except Exception as e:
            messagebox.showerror("Visualisierung-Fehler", f"Fehler bei der Visualisierung: {e}")
    
    def _export_3d_data(self):
        """Export 3D data"""
        try:
            if self.stereo_detector:
                filename = filedialog.asksaveasfilename(
                    title="3D-Daten exportieren",
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")]
                )
                if filename:
                    success = self.stereo_detector.export_3d_data(filename)
                    if success:
                        messagebox.showinfo("Export erfolgreich", f"3D-Daten exportiert:\n{filename}")
                    else:
                        messagebox.showerror("Export-Fehler", "3D-Daten konnten nicht exportiert werden")
        except Exception as e:
            messagebox.showerror("Export-Fehler", f"Fehler beim Exportieren: {e}")
    
    def _export_gis_data(self):
        """Export GIS-compatible data"""
        try:
            if self.stereo_detector:
                folder = filedialog.askdirectory(title="GIS-Export Verzeichnis auswählen")
                if folder:
                    from visualization.stereo_visualization import Stereo3DVisualizer
                    trajectory_data = self.stereo_detector.get_3d_trajectory_data()
                    if trajectory_data:
                        visualizer = Stereo3DVisualizer(trajectory_data)
                        files = visualizer.export_gis_compatible_data(folder)
                        if files:
                            file_list = "\n".join([f"• {os.path.basename(f)}" for f in files])
                            messagebox.showinfo("GIS-Export erfolgreich", 
                                              f"GIS-Dateien erstellt:\n{file_list}\n\nIn: {folder}")
                        else:
                            messagebox.showerror("GIS-Export-Fehler", "GIS-Dateien konnten nicht erstellt werden")
                    else:
                        messagebox.showwarning("Keine Daten", "Keine 3D-Trajektoriendaten für GIS-Export verfügbar")
        except Exception as e:
            messagebox.showerror("GIS-Export-Fehler", f"Fehler beim GIS-Export: {e}")


def integrate_stereo_gui(main_app):
    """Integrate stereo GUI extensions into existing application"""
    stereo_extension = StereoGUIExtension(main_app)
    stereo_extension.integrate_stereo_controls()
    
    # Store reference for access
    main_app.stereo_extension = stereo_extension
    
    # 3D Stereo GUI integration completed - removed console output
    return stereo_extension
