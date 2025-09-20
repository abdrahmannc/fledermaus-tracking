

from tkinter import messagebox, ttk
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import cv2
import numpy as np

# Fix matplotlib font issues on Windows

def format_time(seconds):
    """Format seconds to HH:MM:SS format"""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def validate_events_gui(self, event=None):
        """Enhanced validation with fast event overview and motion visualization"""
        if not self.detector:
            messagebox.showerror("Fehler", "Kein Detektor verfügbar.")
            return
            
        if not hasattr(self.detector, 'events') or not self.detector.events:
            messagebox.showwarning("Keine Ereignisse", "Keine Ereignisse zur Validierung vorhanden.")
            return
            
        try:
            # Use the enhanced fast validation system
            from validation.fast_validator import FastValidationInterface
            fast_validator = FastValidationInterface(self)
            fast_validator.show_enhanced_validation_overview()
        except Exception as e:
            messagebox.showerror("Validierungsfehler", f"Fehler bei der Validierung: {str(e)}")
            print(f"[ERROR] Validation error: {e}")
            # Fallback to original method if fast validator fails
            try:
                self.show_fast_event_overview()
            except Exception as fallback_error:
                print(f"[ERROR] Fallback validation also failed: {fallback_error}")




def show_fast_event_overview(self):
    """Show fast overview of all detected events with motion visualization - responsive"""
    # Create responsive overview window
    overview_window = tk.Toplevel(self.root)
    overview_window.title("Schnelle Ereignis-Übersicht")
    
    # Responsive window sizing
    screen_width = self.root.winfo_screenwidth()
    screen_height = self.root.winfo_screenheight()
    
    if screen_width <= 1366:
        # Small screen
        window_width = min(1000, screen_width - 100)
        window_height = min(600, screen_height - 100)
    else:
        # Large screen
        window_width = 1200
        window_height = 800
        
    overview_window.geometry(f"{window_width}x{window_height}")
    overview_window.minsize(800, 500)
    overview_window.transient(self.root)
    overview_window.grab_set()
    
    # Center the window
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    overview_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Main container with responsive padding
    main_frame = ttk.Frame(overview_window, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title and summary
    title_label = ttk.Label(main_frame, text="Ereignis-Übersicht", 
                            font=('Arial', 14, 'bold'), foreground="#2B5D8A")
    title_label.pack(anchor=tk.W, pady=(0, 8))
    
    # Event summary
    events = self.detector.events
    total_duration = sum(event.get('duration', 0) for event in events)
    
    summary_frame = ttk.LabelFrame(main_frame, text="Zusammenfassung", padding=10)
    summary_frame.pack(fill=tk.X, pady=(0, 15))
    
    summary_info = ttk.Frame(summary_frame)
    summary_info.pack(fill=tk.X)
    
    ttk.Label(summary_info, text=f"Gefundene Ereignisse: {len(events)}", 
                font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
    ttk.Label(summary_info, text=f"Gesamtdauer: {total_duration:.1f}s", 
                font=('Arial', 10)).pack(side=tk.LEFT, padx=(20, 0))
    ttk.Label(summary_info, text=f"Durchschnitt: {total_duration/len(events):.1f}s", 
                font=('Arial', 10)).pack(side=tk.LEFT, padx=(20, 0))
    
    # Main content area with notebook tabs
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
    
    # Tab 1: Event Grid Overview
    grid_frame = ttk.Frame(notebook)
    notebook.add(grid_frame, text="📊 Ereignis-Raster")
    self.create_event_grid_view(grid_frame, events)
    
    # Tab 2: Timeline View
    timeline_frame = ttk.Frame(notebook)
    notebook.add(timeline_frame, text="📈 Zeitachse")
    self.create_timeline_view(timeline_frame, events)
    
    # Tab 3: Motion Heatmap
    heatmap_frame = ttk.Frame(notebook)
    notebook.add(heatmap_frame, text="🔥 Bewegungs-Heatmap")
    self.create_motion_heatmap_view(heatmap_frame, events)
    
    # Validation controls
    control_frame = ttk.Frame(main_frame)
    control_frame.pack(fill=tk.X)
    
    # Batch validation buttons
    batch_frame = ttk.LabelFrame(control_frame, text="Schnell-Validierung", padding=10)
    batch_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    
    ttk.Button(batch_frame, text="✅ Alle genehmigen", 
                command=lambda: self.batch_validate_events(events, 'approved', overview_window),
                style='Accent.TButton').pack(side=tk.LEFT, padx=(0, 10))
    
    ttk.Button(batch_frame, text="❌ Alle ablehnen", 
                command=lambda: self.batch_validate_events(events, 'rejected', overview_window)).pack(side=tk.LEFT, padx=(0, 10))
    
    ttk.Button(batch_frame, text="🔍 Einzelvalidierung", 
                command=lambda: [overview_window.destroy(), self.enhanced_validate_events()]).pack(side=tk.LEFT)
    
    # Close button
    ttk.Button(control_frame, text="❌ Schließen", 
                command=overview_window.destroy).pack(side=tk.RIGHT)
    
    # Cleanup function for mousewheel bindings
    def cleanup_overview_bindings():
        try:
            # Cleanup any canvas mousewheel bindings stored in tabs
            for child in notebook.winfo_children():
                if hasattr(child, '_canvas_mousewheel_binding'):
                    _, canvas = child._canvas_mousewheel_binding
                    canvas.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass
    
    overview_window.protocol("WM_DELETE_WINDOW", lambda: [cleanup_overview_bindings(), overview_window.destroy()])
    
    # Store validation decisions
    self.validation_decisions = {}





def create_event_grid_view(self, parent, events):
    """Create a grid view showing thumbnails of all events"""
    # Create scrollable frame
    canvas = tk.Canvas(parent)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)



def generate_event_thumbnails(self, parent, events, cols):
    """Generate thumbnail images for each event"""
    try:
        if not hasattr(self.detector, 'cap') or not self.detector.cap:
            cap = cv2.VideoCapture(self.video_path)
        else:
            cap = self.detector.cap
        
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        
        for idx, event in enumerate(events):
            row = idx // cols
            col = idx % cols
            
            # Create event frame
            event_frame = ttk.LabelFrame(parent, text=f"Ereignis {idx + 1}", padding=5)
            event_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # Configure grid weights
            parent.grid_columnconfigure(col, weight=1)
            
            # Extract key frame from event
            start_time = event.get('entry', 0)
            end_time = event.get('exit', start_time + 1)
            mid_time = (start_time + end_time) / 2
            
            # Set frame position
            mid_frame = int(mid_time * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
            ret, frame = cap.read()
            
            if ret:
                # Apply ROI or polygon highlighting
                highlighted_frame = self.highlight_detection_area(frame, event)
                
                # Resize for thumbnail
                thumbnail = cv2.resize(highlighted_frame, (200, 150))
                thumbnail_rgb = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)
                
                # Convert to PhotoImage
                pil_image = Image.fromarray(thumbnail_rgb)
                photo = ImageTk.PhotoImage(pil_image)
                
                # Create thumbnail label with click handler
                thumb_label = tk.Label(event_frame, image=photo, cursor="hand2")
                thumb_label.image = photo  # Keep reference
                thumb_label.pack(pady=(0, 5))
                
                # Bind click to show event details
                thumb_label.bind("<Button-1>", lambda e, ev=event, i=idx: self.show_event_detail(ev, i))
            
            # Event info
            info_text = f"Zeit: {start_time:.1f}s - {end_time:.1f}s\nDauer: {event.get('duration', 0):.1f}s"
            info_label = ttk.Label(event_frame, text=info_text, font=('Arial', 8))
            info_label.pack()
            
            # Validation buttons for individual events
            btn_frame = ttk.Frame(event_frame)
            btn_frame.pack(fill=tk.X, pady=(5, 0))
            
            approve_btn = ttk.Button(btn_frame, text="✅", width=3,
                                    command=lambda i=idx: self.mark_event_validation(i, 'approved'))
            approve_btn.pack(side=tk.LEFT, padx=(0, 2))
            
            reject_btn = ttk.Button(btn_frame, text="❌", width=3,
                                    command=lambda i=idx: self.mark_event_validation(i, 'rejected'))
            reject_btn.pack(side=tk.LEFT)
            
    except Exception as e:
        print(f"[ERROR] Error generating thumbnails: {e}")
        error_label = ttk.Label(parent, text=f"Fehler beim Laden der Ereignisse: {str(e)}")
        error_label.pack(pady=20)




def highlight_detection_area(self, frame, event):
    """Highlight the detection area (ROI or polygon) on the frame"""
    highlighted = frame.copy()
    
    try:
        # Draw ROI if available
        if hasattr(self, 'roi') and self.roi:
            x, y, w, h = self.roi
            cv2.rectangle(highlighted, (x, y), (x + w, y + h), (0, 255, 255), 2)
            cv2.putText(highlighted, "ROI", (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Draw polygons if available
        if hasattr(self, 'polygon_areas') and self.polygon_areas:
            for i, polygon in enumerate(self.polygon_areas):
                if len(polygon) >= 3:
                    pts = np.array(polygon, np.int32)
                    cv2.polylines(highlighted, [pts], True, (0, 255, 0), 2)
                    
                    # Add polygon number
                    if len(polygon) > 0:
                        center_x = int(sum(p[0] for p in polygon) / len(polygon))
                        center_y = int(sum(p[1] for p in polygon) / len(polygon))
                        cv2.putText(highlighted, f"#{i + 1}", (center_x, center_y),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Highlight bat center if available
        if 'bat_center' in event and event['bat_center']:
            center = event['bat_center']
            cv2.circle(highlighted, center, 15, (255, 0, 0), 3)
            cv2.circle(highlighted, center, 5, (255, 255, 255), -1)
        
    except Exception as e:
        print(f"[WARNING] Error highlighting detection area: {e}")
    
    return highlighted





def mark_event_validation(self, event_idx, decision):
    """Mark an event with validation decision"""
    self.validation_decisions[event_idx] = decision
    print(f"Event {event_idx + 1} marked as {decision}")




def show_event_detail(self, event, event_idx):
    """Show detailed view of a specific event"""
    detail_window = tk.Toplevel(self.root)
    detail_window.title(f"Ereignis {event_idx + 1} - Details")
    detail_window.geometry("800x600")
    detail_window.transient(self.root)
    
    main_frame = ttk.Frame(detail_window, padding=15)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Event information
    info_frame = ttk.LabelFrame(main_frame, text="Ereignis-Information", padding=10)
    info_frame.pack(fill=tk.X, pady=(0, 15))
    
    start_time = event.get('entry', 0)
    end_time = event.get('exit', start_time + 1)
    duration = event.get('duration', end_time - start_time)
    
    ttk.Label(info_frame, text=f"Ereignis Nr.: {event_idx + 1}").pack(anchor=tk.W)
    ttk.Label(info_frame, text=f"Startzeit: {start_time:.2f} Sekunden").pack(anchor=tk.W)
    ttk.Label(info_frame, text=f"Endzeit: {end_time:.2f} Sekunden").pack(anchor=tk.W)
    ttk.Label(info_frame, text=f"Dauer: {duration:.2f} Sekunden").pack(anchor=tk.W)
    
    # Video preview
    video_frame = ttk.LabelFrame(main_frame, text="Video-Vorschau", padding=10)
    video_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
    
    # Create canvas for video preview
    video_canvas = tk.Canvas(video_frame, bg='black', width=640, height=480)
    video_canvas.pack(fill=tk.BOTH, expand=True)
    
    # Load and display key frames
    self.load_event_preview(video_canvas, event)
    
    # Validation controls
    control_frame = ttk.Frame(main_frame)
    control_frame.pack(fill=tk.X)
    
    ttk.Button(control_frame, text="✅ Genehmigen", 
                command=lambda: [self.mark_event_validation(event_idx, 'approved'), 
                                detail_window.destroy()],
                style='Accent.TButton').pack(side=tk.LEFT, padx=(0, 10))
    
    ttk.Button(control_frame, text="❌ Ablehnen", 
                command=lambda: [self.mark_event_validation(event_idx, 'rejected'), 
                                detail_window.destroy()]).pack(side=tk.LEFT, padx=(0, 10))
    
    ttk.Button(control_frame, text="Schließen", 
                command=detail_window.destroy).pack(side=tk.RIGHT)




def load_event_preview(self, canvas, event):
    """Load and display preview frames for an event"""
    try:
        if not hasattr(self.detector, 'cap') or not self.detector.cap:
            cap = cv2.VideoCapture(self.video_path)
        else:
            cap = self.detector.cap
        
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        start_time = event.get('entry', 0)
        end_time = event.get('exit', start_time + 1)
        
        # Load middle frame
        mid_time = (start_time + end_time) / 2
        mid_frame = int(mid_time * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
        ret, frame = cap.read()
        
        if ret:
            # Highlight detection area
            highlighted = self.highlight_detection_area(frame, event)
            
            # Resize for display
            height, width = highlighted.shape[:2]
            canvas_width = 640
            canvas_height = 480
            
            if width > canvas_width or height > canvas_height:
                scale = min(canvas_width/width, canvas_height/height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                highlighted = cv2.resize(highlighted, (new_width, new_height))
            
            # Convert and display
            frame_rgb = cv2.cvtColor(highlighted, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(pil_image)
            
            canvas.delete("all")
            canvas.create_image(canvas_width//2, canvas_height//2, 
                                image=photo, anchor=tk.CENTER)
            canvas.photo = photo  # Keep reference
            
    except Exception as e:
        print(f"[ERROR] Error loading event preview: {e}")





def create_timeline_view(self, parent, events):
    """Create a timeline view of all events"""
    timeline_frame = ttk.Frame(parent, padding=10)
    timeline_frame.pack(fill=tk.BOTH, expand=True)
    
    # Timeline canvas
    canvas = tk.Canvas(timeline_frame, bg='white', height=200)
    canvas.pack(fill=tk.X, pady=(0, 10))
    
    # Calculate timeline parameters
    if not events:
        return
        
    video_duration = max(event.get('exit', 0) for event in events) + 5
    canvas_width = 800  # Will be updated after canvas is drawn
    
    def draw_timeline():
        canvas.update()
        canvas_width = canvas.winfo_width()
        canvas.delete("all")
        
        if canvas_width <= 1:
            return
        
        # Draw timeline background
        canvas.create_rectangle(50, 50, canvas_width - 50, 150, fill='lightgray', outline='gray')
        
        # Draw time markers
        for i in range(0, int(video_duration) + 1, max(1, int(video_duration / 10))):
            x = 50 + (i / video_duration) * (canvas_width - 100)
            canvas.create_line(x, 45, x, 155, fill='darkgray')
            canvas.create_text(x, 35, text=f"{i}s", font=('Arial', 8))
        
        # Draw events
        for idx, event in enumerate(events):
            start_time = event.get('entry', 0)
            end_time = event.get('exit', start_time + 1)
            
            start_x = 50 + (start_time / video_duration) * (canvas_width - 100)
            end_x = 50 + (end_time / video_duration) * (canvas_width - 100)
            
            # Color based on validation status
            color = 'lightblue'
            if idx in self.validation_decisions:
                color = 'lightgreen' if self.validation_decisions[idx] == 'approved' else 'lightcoral'
            
            # Draw event rectangle
            rect = canvas.create_rectangle(start_x, 60, end_x, 140, 
                                            fill=color, outline='darkblue', width=2)
            
            # Event label
            canvas.create_text((start_x + end_x) / 2, 100, 
                                text=f"E{idx + 1}", font=('Arial', 10, 'bold'))
            
            # Bind click event
            canvas.tag_bind(rect, "<Button-1>", 
                            lambda e, ev=event, i=idx: self.show_event_detail(ev, i))
    
    # Draw initial timeline
    timeline_frame.after(100, draw_timeline)
    
    # Bind resize event
    canvas.bind('<Configure>', lambda e: draw_timeline())
    
    # Legend
    legend_frame = ttk.Frame(timeline_frame)
    legend_frame.pack(fill=tk.X)
    
    ttk.Label(legend_frame, text="Legende:").pack(side=tk.LEFT)
    
    # Create colored squares for legend
    legend_canvas = tk.Canvas(legend_frame, height=20, width=300)
    legend_canvas.pack(side=tk.LEFT, padx=(10, 0))
    
    legend_canvas.create_rectangle(5, 5, 20, 15, fill='lightblue', outline='darkblue')
    legend_canvas.create_text(25, 10, text="Unvalidiert", anchor='w', font=('Arial', 8))
    
    legend_canvas.create_rectangle(100, 5, 115, 15, fill='lightgreen', outline='darkgreen')
    legend_canvas.create_text(120, 10, text="Genehmigt", anchor='w', font=('Arial', 8))
    
    legend_canvas.create_rectangle(200, 5, 215, 15, fill='lightcoral', outline='darkred')
    legend_canvas.create_text(220, 10, text="Abgelehnt", anchor='w', font=('Arial', 8))







def create_motion_heatmap_view(self, parent, events):
    """Create a motion heatmap view showing activity intensity"""
    heatmap_frame = ttk.Frame(parent, padding=10)
    heatmap_frame.pack(fill=tk.BOTH, expand=True)
    
    # Information label
    info_label = ttk.Label(heatmap_frame, 
                            text="Bewegungs-Heatmap zeigt die Intensität der erkannten Aktivität über die Zeit",
                            font=('Arial', 10))
    info_label.pack(anchor=tk.W, pady=(0, 10))
    
    # Heatmap canvas
    canvas = tk.Canvas(heatmap_frame, bg='white', height=300)
    canvas.pack(fill=tk.X, pady=(0, 10))
    
    def draw_heatmap():
        canvas.update()
        canvas_width = canvas.winfo_width()
        canvas.delete("all")
        
        if canvas_width <= 1 or not events:
            return
        
        # Calculate video duration and time bins
        video_duration = max(event.get('exit', 0) for event in events) + 5
        time_bins = 100  # Number of time segments
        bin_duration = video_duration / time_bins
        
        # Count events in each time bin
        activity_counts = [0] * time_bins
        for event in events:
            start_time = event.get('entry', 0)
            end_time = event.get('exit', start_time + 1)
            
            start_bin = int(start_time / bin_duration)
            end_bin = int(end_time / bin_duration)
            
            for bin_idx in range(max(0, start_bin), min(time_bins, end_bin + 1)):
                activity_counts[bin_idx] += 1
        
        # Normalize and draw heatmap
        max_count = max(activity_counts) if activity_counts else 1
        
        for i, count in enumerate(activity_counts):
            if count > 0:
                x1 = 50 + (i / time_bins) * (canvas_width - 100)
                x2 = 50 + ((i + 1) / time_bins) * (canvas_width - 100)
                
                # Color intensity based on activity count
                intensity = count / max_count
                red = min(255, int(255 * intensity))
                color = f"#{red:02x}{255-red:02x}00"  # Red to yellow gradient
                
                canvas.create_rectangle(x1, 50, x2, 250, fill=color, outline='')
        
        # Draw time axis
        for i in range(0, int(video_duration) + 1, max(1, int(video_duration / 10))):
            x = 50 + (i / video_duration) * (canvas_width - 100)
            canvas.create_line(x, 250, x, 260, fill='black')
            canvas.create_text(x, 270, text=f"{i}s", font=('Arial', 8))
        
        # Labels
        canvas.create_text(25, 150, text="Aktivität", font=('Arial', 10), angle=90)
        canvas.create_text(canvas_width // 2, 290, text="Zeit", font=('Arial', 10))
    
    # Draw initial heatmap
    heatmap_frame.after(100, draw_heatmap)
    canvas.bind('<Configure>', lambda e: draw_heatmap())
    
    # Activity statistics
    stats_frame = ttk.LabelFrame(heatmap_frame, text="Aktivitäts-Statistik", padding=10)
    stats_frame.pack(fill=tk.X)
    
    # Calculate peak activity times
    if events:
        # Find time periods with most activity
        video_duration = max(event.get('exit', 0) for event in events) + 5
        time_bins = 60  # 1-second bins
        bin_duration = video_duration / time_bins
        
        activity_counts = [0] * time_bins
        for event in events:
            start_time = event.get('entry', 0)
            end_time = event.get('exit', start_time + 1)
            
            start_bin = int(start_time / bin_duration)
            end_bin = int(end_time / bin_duration)
            
            for bin_idx in range(max(0, start_bin), min(time_bins, end_bin + 1)):
                activity_counts[bin_idx] += 1
        
        # Find peak times
        peak_activity = max(activity_counts) if activity_counts else 0
        peak_times = []
        for i, count in enumerate(activity_counts):
            if count == peak_activity and peak_activity > 0:
                peak_times.append(i * bin_duration)
        
        # Display statistics
        stats_text = f"Höchste Aktivität: {peak_activity} Ereignisse"
        if peak_times:
            times_str = ", ".join(f"{t:.1f}s" for t in peak_times[:3])
            stats_text += f" bei {times_str}"
            if len(peak_times) > 3:
                stats_text += f" (+{len(peak_times)-3} weitere)"
        
        ttk.Label(stats_frame, text=stats_text).pack(anchor=tk.W)





def batch_validate_events(self, events, decision, overview_window):
    """Apply batch validation to all events"""
    try:
        result = messagebox.askyesno(
            "Batch-Validierung",
            f"Möchten Sie wirklich alle {len(events)} Ereignisse als '{decision}' markieren?\n\n"
            f"Diese Aktion kann nicht rückgängig gemacht werden."
        )
        
        if result:
            # Mark all events with the decision
            for idx in range(len(events)):
                self.validation_decisions[idx] = decision
            
            # Apply decisions to detector events
            for idx, event in enumerate(self.detector.events):
                event['validated'] = True
                event['validation_result'] = decision
            
            messagebox.showinfo(
                "Validierung abgeschlossen",
                f"Alle {len(events)} Ereignisse wurden als '{decision}' markiert."
            )
            
            # Update event display
            self.update_event_display()
            overview_window.destroy()
            
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler bei der Batch-Validierung: {str(e)}")



def replay_validation(self, event=None):
    """Start multi-pass validation session using ValidationSession"""
    if not hasattr(self.detector, 'events') or not self.detector.events:
        messagebox.showwarning("Keine Ereignisse", "Keine Ereignisse zum Validieren vorhanden.")
        return
        
    if not self.video_path:
        messagebox.showerror("Fehler", "Video-Pfad nicht verfügbar.")
        return
        
    try:
        # Import ValidationSession
        from validation.manual_validator import ValidationSession
        
        # Create validation session
        self.validation_session = ValidationSession(self.video_path, self.detector.events)
        
        # Check if session is ready
        if not self.validation_session.is_ready():
            messagebox.showerror("Fehler", "Validation Session konnte nicht initialisiert werden.")
            return
        
        # Start multi-pass validation
        result = self.validation_session.validate_event_multipass()
        
        if result:
            self.flight_path_data = result.get('flight_paths', [])
            self.validation_history = result.get('validation_history', [])
            
            # Update detector events with validation results
            if 'validated_events' in result:
                self.detector.events = result['validated_events']
                self.update_event_display()
                
            messagebox.showinfo("Validierung abgeschlossen", 
                                f"Multi-pass Validierung abgeschlossen.\n"
                                f"Flugwege erfasst: {len(self.flight_path_data)}\n"
                                f"Validierungsrunden: {len(self.validation_history)}")
        else:
            messagebox.showinfo("Validierung abgebrochen", "Validierung wurde abgebrochen.")
            
    except ImportError as e:
        messagebox.showerror("Import Fehler", f"ValidationSession konnte nicht importiert werden: {str(e)}")
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler bei der Replay-Validierung: {str(e)}")
