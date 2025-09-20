import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
from datetime import datetime

# Fix matplotlib font issues on Windows





def generate_bat_paths_from_events(self):
    """Generate bat paths from detection events"""
    bat_paths = {}
    if hasattr(self.detector, 'events'):
        for i, event in enumerate(self.detector.events):
            # Create path from event data
            start_frame = event.get('start_frame', 0)
            end_frame = event.get('end_frame', start_frame + 30)
            center_x = event.get('center_x', 320)  # Default center positions
            center_y = event.get('center_y', 240)
            
            # Generate simple path (can be enhanced with actual tracking data)
            path_points = []
            for frame in range(start_frame, min(end_frame + 1, start_frame + 60)):
                # Add some variation to simulate movement
                x = center_x + (frame - start_frame) * 2
                y = center_y + np.sin((frame - start_frame) * 0.1) * 10
                path_points.append((frame / getattr(self, 'fps', 30), x, y))
            
            bat_paths[f"bat_{i+1}"] = path_points
    
    return bat_paths

def find_recent_flight_map(self):
    """Find the most recently created flight map for the current video"""
    try:
        if not hasattr(self, 'video_path') or not self.video_path:
            return None
            
        # Look in results directory for flight maps
        video_name = os.path.splitext(os.path.basename(self.video_path))[0]
        results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
        
        # Search in various possible locations
        search_patterns = [
            os.path.join(results_dir, f"*{video_name}*", "*flugweg*.png"),
            os.path.join(results_dir, f"*{video_name}*", "*flugkarte*.png"),
            os.path.join(results_dir, "*", "*flugweg*.png"),
            os.path.join(results_dir, "*", "*flugkarte*.png")
        ]
        
        import glob
        for pattern in search_patterns:
            files = glob.glob(pattern)
            if files:
                # Return the most recent one
                return max(files, key=os.path.getmtime)
        
        return None
    except Exception:
        return None

def display_flight_map(self, image_path=None, event=None):
    """Display flight map in a properly managed window with enhanced visualization options"""
    try:
        # If no image path provided, try to find the most recent flight map
        if image_path is None:
            image_path = self.find_recent_flight_map()
            if image_path is None:
                messagebox.showwarning("Keine Flugkarte", 
                                     "Keine Flugkarte gefunden. Bitte exportieren Sie zuerst eine Flugkarte über den Export-Button.")
                return
        # Create new window for flight map display
        flight_window = tk.Toplevel(self.root)
        flight_window.title("Flugkarte - Erweiterte Visualisierung")
        flight_window.geometry("1200x800")
        
        # Configure proper window closing
        def close_flight_window():
            try:
                flight_window.destroy()
            except:
                pass
        
        flight_window.protocol("WM_DELETE_WINDOW", close_flight_window)
        
        # Create main frame with notebook for tabs
        main_frame = ttk.Frame(flight_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Standard Flight Map
        map_frame = ttk.Frame(notebook)
        notebook.add(map_frame, text="📊 Standard Flugkarte")
        
        # Load and display flight map image
        img = Image.open(image_path)
        
        # Resize image to fit window if necessary
        window_width, window_height = 1150, 650
        img_width, img_height = img.size
        
        # Calculate scaling to fit window while maintaining aspect ratio
        scale_w = window_width / img_width
        scale_h = window_height / img_height
        scale = min(scale_w, scale_h, 1.0)  # Don't upscale
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(img)
        
        # Create scrollable canvas for flight map
        canvas_frame = ttk.Frame(map_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(canvas_frame, bg='white')
        scrollbar_v = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar_h = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=canvas.xview)
        canvas.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add image to canvas
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Keep reference to prevent garbage collection
        flight_window.photo = photo
        
        # Tab 2: Radar View
        self.create_radar_view_tab(notebook, flight_window)
        
        # Tab 3: Video Overlay (if video is available)
        if hasattr(self, 'video_path') and self.video_path:
            overlay_frame = ttk.Frame(notebook)
            notebook.add(overlay_frame, text="🎥 Video mit Flugwegen")
            
            # Create video overlay display
            self.create_video_overlay_display(overlay_frame)
        
        # Enhanced control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text=" PDF-Bericht erstellen", 
                    command=self.export_pdf_report).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="💾 Als Bild speichern", 
                    command=lambda: self.save_current_view(image_path)).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="❌ Schließen", command=close_flight_window).pack(side=tk.RIGHT, padx=5)
        
        # Focus the window
        flight_window.focus_set()
        flight_window.lift()
        
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Anzeigen der Flugkarte: {str(e)}")





def create_radar_view_tab(self, notebook, flight_window):
    """Create radar view tab with live radar-style display"""
    try:
        radar_frame = ttk.Frame(notebook)
        notebook.add(radar_frame, text="📡 Radar-Ansicht")
        
        # Check if we have flight data for radar view
        has_flight_data = False
        if hasattr(self, 'flight_path_data') and self.flight_path_data:
            has_flight_data = True
        elif hasattr(self.detector, 'bat_paths') and self.detector.bat_paths:
            has_flight_data = True
        
        if not has_flight_data:
            # Show message if no flight data available
            info_label = ttk.Label(radar_frame, 
                                    text="Keine Flugdaten für Radar-Ansicht verfügbar.\n"
                                        "Führen Sie eine Replay-Validierung durch, um Flugdaten zu sammeln.",
                                    font=('Segoe UI', 12), 
                                    foreground='gray')
            info_label.pack(expand=True)
            
            ttk.Button(radar_frame, text="Replay-Validierung starten", 
                        command=self.replay_validation).pack(pady=10)
            return
        
        # Create radar display
        radar_info = ttk.Label(radar_frame, 
                                text="🔴 LIVE RADAR - Fledermaus-Überwachung", 
                                font=('Courier New', 14, 'bold'),
                                foreground='darkgreen')
        radar_info.pack(pady=10)
        
        # Radar canvas with dark background
        radar_canvas = tk.Canvas(radar_frame, bg='black', width=800, height=600)
        radar_canvas.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        # Draw radar grid
        self.draw_radar_grid(radar_canvas)
        
        # Draw flight paths on radar if available
        self.draw_flight_paths_on_radar(radar_canvas)
        
        # Radar control frame
        radar_controls = ttk.Frame(radar_frame)
        radar_controls.pack(fill=tk.X, pady=5)
        
        status_label = ttk.Label(radar_controls, 
                                text=f"📊 Contacts: {len(self.detector.events) if hasattr(self.detector, 'events') else 0} | "
                                    f"Active: {len(self.detector.events) if hasattr(self.detector, 'events') else 0} | "
                                    f"Scan: {datetime.now().strftime('%H:%M:%S')}")
        status_label.pack()
        
    except Exception as e:
        error_label = ttk.Label(radar_frame, text=f"Fehler beim Erstellen der Radar-Ansicht: {str(e)}")
        error_label.pack(expand=True)






def draw_radar_grid(self, canvas):
    """Draw radar-style grid on canvas"""
    try:
        width = canvas.winfo_reqwidth()
        height = canvas.winfo_reqheight()
        
        # Draw grid lines
        grid_spacing = 50
        for x in range(0, width, grid_spacing):
            canvas.create_line(x, 0, x, height, fill='green', width=1, stipple='gray25')
        for y in range(0, height, grid_spacing):
            canvas.create_line(0, y, width, y, fill='green', width=1, stipple='gray25')
        
        # Draw center crosshairs
        center_x, center_y = width // 2, height // 2
        canvas.create_line(center_x, 0, center_x, height, fill='lime', width=2)
        canvas.create_line(0, center_y, width, center_y, fill='lime', width=2)
        
        # Draw range circles
        for radius in [100, 200, 300]:
            if radius * 2 < min(width, height):
                canvas.create_oval(center_x - radius, center_y - radius,
                                    center_x + radius, center_y + radius,
                                    outline='green', width=1, stipple='gray25')
    except:
        pass





def draw_flight_paths_on_radar(self, canvas):
    """Draw flight paths on radar display"""
    try:
        if not hasattr(self.detector, 'events') or not self.detector.events:
            return
        
        width = canvas.winfo_reqwidth()
        height = canvas.winfo_reqheight()
        
        # Get video dimensions for scaling
        if hasattr(self, 'video_path') and self.video_path:
            cap = cv2.VideoCapture(self.video_path)
            video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            scale_x = width / video_width
            scale_y = height / video_height
        else:
            scale_x = scale_y = 1
        
        # Radar colors for different contacts
        colors = ['#00FF00', '#FF4500', '#00BFFF', '#FFD700', '#FF69B4']
        
        # Draw simplified flight paths
        for i, event in enumerate(self.detector.events[:5]):  # Limit to 5 for clarity
            color = colors[i % len(colors)]
            
            # Simple representation - draw contact at estimated position
            # This is a simplified version for the demo
            x = int((50 + i * 100) * scale_x) % width
            y = int((50 + i * 80) * scale_y) % height
            
            # Draw radar blip
            canvas.create_oval(x-5, y-5, x+5, y+5, fill=color, outline=color)
            canvas.create_oval(x-15, y-15, x+15, y+15, outline=color, width=2)
            
            # Add contact label
            canvas.create_text(x+20, y-20, text=f"BAT-{i+1:02d}", 
                                fill=color, font=('Courier New', 8, 'bold'))
            
    except Exception as e:
        pass





def create_video_overlay_display(self, parent_frame):
    """Create video display with flight path overlay"""
    try:
        overlay_label = ttk.Label(parent_frame, text="Video mit Flugweg-Overlay")
        overlay_label.pack(pady=10)
        
        # Video canvas
        video_canvas = tk.Canvas(parent_frame, bg='black', width=640, height=480)
        video_canvas.pack(pady=10)
        
        # Control frame
        control_frame = ttk.Frame(parent_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        # Video controls
        ttk.Button(control_frame, text="▶ Play", 
                    command=lambda: self.play_video_with_overlay(video_canvas)).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="⏸ Pause", 
                    command=self.pause_video_overlay).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="⏹ Stop", 
                    command=self.stop_video_overlay).pack(side=tk.LEFT, padx=5)
        
        # Store canvas reference
        self.video_overlay_canvas = video_canvas
        self.video_overlay_playing = False
        
    except Exception as e:
        print(f"Error creating video overlay: {e}")



def play_video_with_overlay(self, canvas):
    """Play video with flight path overlay"""
    if not hasattr(self, 'video_path') or not self.video_path:
        return
        
    self.video_overlay_playing = True
    
    def update_video_frame():
        if not self.video_overlay_playing:
            return
            
        try:
            if not hasattr(self, 'overlay_cap') or self.overlay_cap is None:
                self.overlay_cap = cv2.VideoCapture(self.video_path)
            
            ret, frame = self.overlay_cap.read()
            if ret:
                # Resize frame to fit canvas
                frame = cv2.resize(frame, (640, 480))
                
                # Add flight path overlay if available
                if hasattr(self, 'flight_path_data') and self.flight_path_data:
                    frame = self.overlay_flight_paths_on_frame(frame)
                
                # Convert to display format
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                photo = ImageTk.PhotoImage(img)
                
                # Update canvas
                canvas.delete("all")
                canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                canvas.image = photo  # Keep reference
                
                # Schedule next frame
                self.root.after(33, update_video_frame)  # ~30 FPS
            else:
                # End of video, restart
                if hasattr(self, 'overlay_cap'):
                    self.overlay_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.root.after(33, update_video_frame)
                
        except Exception as e:
            print(f"Error in video overlay: {e}")
            self.video_overlay_playing = False
    
    update_video_frame()



def overlay_flight_paths_on_frame(self, frame):
    """Overlay flight paths on video frame"""
    try:
        # Simple overlay - draw flight paths as colored lines
        if hasattr(self, 'polygon_areas'):
            for i, polygon in enumerate(self.polygon_areas):
                if len(polygon) >= 3:
                    pts = np.array([[int(p[0]), int(p[1])] for p in polygon], np.int32)
                    cv2.polylines(frame, [pts], True, (0, 255, 0), 2)
                    
        # Add flight path lines if available
        if hasattr(self, 'detector') and hasattr(self.detector, 'events'):
            for i, event in enumerate(self.detector.events):
                if 'center_x' in event and 'center_y' in event:
                    center = (int(event['center_x']), int(event['center_y']))
                    cv2.circle(frame, center, 5, (255, 0, 0), -1)
                    
    except Exception as e:
        print(f"Error overlaying flight paths: {e}")
    
    return frame

def pause_video_overlay(self):
    """Pause video overlay"""
    self.video_overlay_playing = False

def stop_video_overlay(self):
    """Stop video overlay"""
    self.video_overlay_playing = False
    if hasattr(self, 'overlay_cap') and self.overlay_cap:
        self.overlay_cap.release()
        self.overlay_cap = None

def save_current_view(self, original_path):
    """Save current view or copy original"""
    try:
        import shutil
        filename = f"flugkarte_kopie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            initialname=filename
        )
        if save_path:
            shutil.copy2(original_path, save_path)
            messagebox.showinfo("Gespeichert", f"Flugkarte gespeichert unter:\n{save_path}")
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Speichern: {str(e)}")





def view_flight_paths(self):
    """Display flight paths visualization"""
    if not self.flight_path_data:
        messagebox.showwarning("Keine Flugwege", "Keine Flugweg-Daten verfügbar. Führen Sie zuerst eine Replay-Validierung durch.")
        return
        
    try:
        # Import visualization module
        from visualization.visualization import create_flight_path_visualization
        
        # Create visualization
        viz_path = create_flight_path_visualization(
            self.flight_path_data, 
            self.video_path,
            title=f"Flugwege - {os.path.basename(self.video_path)}"
        )
        
        if viz_path and os.path.exists(viz_path):
            messagebox.showinfo("Visualisierung erstellt", 
                                f"Flugweg-Visualisierung gespeichert:\n{viz_path}")
            
            # Ask if user wants to open the visualization
            if messagebox.askyesno("Visualisierung öffnen", 
                                    "Möchten Sie die Visualisierung jetzt öffnen?"):
                try:
                    os.startfile(viz_path)  # Windows
                except:
                    try:
                        subprocess.run(['xdg-open', viz_path])  # Linux
                    except:
                        messagebox.showinfo("Pfad", f"Visualisierung gespeichert unter:\n{viz_path}")
        else:
            messagebox.showerror("Fehler", "Visualisierung konnte nicht erstellt werden.")
            
    except ImportError as e:
        messagebox.showerror("Import Fehler", f"Visualisierungsmodul konnte nicht importiert werden: {str(e)}")
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler bei der Flugweg-Visualisierung: {str(e)}")
