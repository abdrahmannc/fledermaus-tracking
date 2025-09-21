import tkinter as tk
from tkinter import messagebox
import threading








# ===========================================
# Polygon Drawing Functionality
# ===========================================

def toggle_drawing_mode(self, event=None):
    """Toggle polygon drawing mode on/off"""
    self.drawing_mode = not self.drawing_mode
    if self.drawing_mode:
        self.btn_toggle_drawing.config(text="Zeichenmodus beenden")
        print("[STATUS] Polygon-Zeichenmodus: Klicken Sie, um Punkte zu setzen. ESC zum Beenden.")
        # Give focus to canvas for key events
        self.canvas.focus_set()
        messagebox.showinfo("Zeichenmodus", 
                            "Polygon-Zeichenmodus aktiviert!\n\n"
                            "• Linksklick: Punkt hinzufügen\n"
                            "• ESC: Polygon beenden\n"
                            "• Mindestens 3 Punkte erforderlich")
    else:
        self.btn_toggle_drawing.config(text="Polygon-Bereich zeichnen")
        print("[STATUS] Zeichenmodus deaktiviert.")
        # Finish current polygon if any
        if len(self.current_polygon) >= 3:
            self.finish_current_polygon()
        else:
            self.current_polygon = []
            self.redraw_polygons_on_canvas()

def clear_polygon_areas(self, event=None):
    """Clear all drawn polygon areas"""
    if self.polygon_areas:
        result = messagebox.askyesno("Polygone löschen", 
                                    f"Möchten Sie alle {len(self.polygon_areas)} Polygone löschen?")
        if result:
            self.polygon_areas = []
            self.current_polygon = []
            self.redraw_polygons_on_canvas()
            print("[STATUS] Alle Polygone gelöscht.")
            # Update detector with cleared areas
            if hasattr(self.detector, 'set_polygon_areas'):
                self.detector.set_polygon_areas([])
            # Update start button state after clearing polygons
            self.update_start_button_state()
    else:
        messagebox.showinfo("Keine Polygone", "Es sind keine Polygone zum Löschen vorhanden.")

def delete_drawings(self, event=None):
    """Robust function to delete all drawings (ROI and polygons) with tag-based canvas clearing"""
    # Check for ROI in multiple locations (self.roi, self.detector.roi)
    has_roi = ((hasattr(self, 'roi') and self.roi is not None) or 
               (hasattr(self, 'detector') and hasattr(self.detector, 'roi') and self.detector.roi is not None))
    has_polygons = self.polygon_areas and len(self.polygon_areas) > 0
    
    # Debug output
    print(f"[DEBUG] has_roi: {has_roi}, has_polygons: {has_polygons}")
    if hasattr(self, 'roi'):
        print(f"[DEBUG] self.roi: {self.roi}")
    if hasattr(self, 'detector') and hasattr(self.detector, 'roi'):
        print(f"[DEBUG] self.detector.roi: {self.detector.roi}")
    
    if not has_roi and not has_polygons:
        messagebox.showinfo("Keine Zeichnungen", "Es sind keine ROI oder Polygone zum Löschen vorhanden.")
        return
    
    # Count total shapes for confirmation dialog
    total_shapes = (1 if has_roi else 0) + (len(self.polygon_areas) if has_polygons else 0)
    shape_desc = []
    if has_roi:
        shape_desc.append("1 ROI")
    if has_polygons:
        shape_desc.append(f"{len(self.polygon_areas)} Polygon{'e' if len(self.polygon_areas) > 1 else ''}")
    
    result = messagebox.askyesno("Zeichen löschen", 
                                f"Möchten Sie alle gezeichneten Bereiche löschen?\n({', '.join(shape_desc)})")
    
    if result:
        # Robust attribute clearing - clear multiple common attribute names
        roi_attributes = ['roi', 'region_of_interest', 'selected_roi', 'roi_coords', 'roi_area']
        polygon_attributes = ['polygon_areas', 'polygons', 'drawn_polygons', 'current_polygon', 'temp_polygon']
        
        # Clear ROI attributes robustly - check multiple locations
        roi_cleared = False
        for attr in roi_attributes:
            if hasattr(self, attr):
                if getattr(self, attr) is not None:
                    setattr(self, attr, None)
                    roi_cleared = True
                    print(f"[DEBUG] Cleared self.{attr}")
            if hasattr(self, 'detector') and hasattr(self.detector, attr):
                if getattr(self.detector, attr) is not None:
                    setattr(self.detector, attr, None)
                    roi_cleared = True
                    print(f"[DEBUG] Cleared self.detector.{attr}")
        
        # Additional explicit ROI clearing for known locations
        if hasattr(self, 'roi'):
            self.roi = None
            roi_cleared = True
        if hasattr(self, 'detector') and hasattr(self.detector, 'roi'):
            self.detector.roi = None
            roi_cleared = True
            
        if roi_cleared:
            print("[DEBUG] ROI successfully cleared")
        
        # Clear polygon attributes robustly
        for attr in polygon_attributes:
            if hasattr(self, attr):
                if attr == 'current_polygon':
                    setattr(self, attr, [])
                else:
                    setattr(self, attr, [] if isinstance(getattr(self, attr, None), list) else None)
            if hasattr(self.detector, attr):
                if attr == 'current_polygon':
                    setattr(self.detector, attr, [])
                else:
                    setattr(self.detector, attr, [] if isinstance(getattr(self.detector, attr, None), list) else None)
        
        # Clear canvas items by tags
        try:
            if hasattr(self, 'canvas') and self.canvas:
                # Remove all drawn items with specific tags
                self.canvas.delete('drawn')
                self.canvas.delete('polygon')
                self.canvas.delete('roi')
                self.canvas.delete('current_polygon')
                self.canvas.delete('temp_line')
        except tk.TclError:
            pass  # Canvas might be destroyed
        
        # Call detector polygon clearing method if it exists
        if hasattr(self.detector, 'set_polygon_areas'):
            self.detector.set_polygon_areas([])
        
        # Also clear polygon mask
        if hasattr(self.detector, 'polygon_mask'):
            self.detector.polygon_mask = None
        
        # Refresh display
        self.redraw_polygons_on_canvas()
        
        # Refresh the video frame to remove ROI rectangle if ROI was cleared
        if roi_cleared and hasattr(self, 'detector') and hasattr(self.detector, 'video_path') and self.detector.video_path:
            try:
                import cv2
                cap = cv2.VideoCapture(self.detector.video_path)
                ret, frame = cap.read()
                cap.release()
                if ret:
                    # Show original frame without ROI rectangle
                    self.show_frame(frame)
                    print("[DEBUG] Refreshed video frame to remove ROI rectangle")
            except Exception as e:
                print(f"[DEBUG] Could not refresh video frame: {e}")
        
        # Display German status message
        print("[STATUS] Zeichnungen gelöscht.")
        
        # Update detection area status after clearing
        if hasattr(self, 'update_detection_area_status'):
            self.update_detection_area_status()
        
        # Update start button state
        self.update_start_button_state()

def clear_shapes(self, event=None):
    """Clear all drawn shapes (ROI and polygons) - legacy function, calls delete_drawings"""
    self.delete_drawings(event)

def on_escape_key(self, event):
    """Handle ESC key press to finish current polygon drawing"""
    if self.drawing_mode and self.current_polygon:
        # Check if we have enough points to create a polygon
        if len(self.current_polygon) >= 3:
            # Store the count before finishing (since finish_current_polygon clears the list)
            points_count = len(self.current_polygon)
            
            # Complete the polygon
            self.finish_current_polygon()
            
            # Show completion message in German
            messagebox.showinfo("Polygon abgeschlossen!", 
                                f"Das Polygon wurde erfolgreich abgeschlossen!\n"
                                f"{points_count} Punkte wurden gesetzt.\n\n"
                                f"Sie können jetzt ein neues Polygon zeichnen.")
        else:
            # Not enough points, show warning
            points_count = len(self.current_polygon)
            messagebox.showwarning("Zu wenige Punkte", 
                                f"Ein Polygon benötigt mindestens 3 Punkte.\n"
                                f"Aktuell: {points_count} Punkte gesetzt.\n\n"
                                f"Fügen Sie weitere Punkte hinzu oder "
                                f"beenden Sie den Zeichenmodus.")
    elif self.drawing_mode and not self.current_polygon:
        # No polygon being drawn, just show info
        messagebox.showinfo("Kein Polygon", 
                            "Es wird derzeit kein Polygon gezeichnet.\n\n"
                            "Klicken Sie auf die Leinwand, um ein neues Polygon zu beginnen.")

def on_canvas_click(self, event):
    """Handle canvas click events for polygon drawing"""
    if not self.drawing_mode or self.original_frame is None:
        return
        
    # Convert canvas coordinates to video coordinates
    video_x, video_y = self.canvas_to_video_coords(event.x, event.y)
    
    # Add point to current polygon
    self.current_polygon.append((video_x, video_y))
    self.redraw_polygons_on_canvas()
    
    points_count = len(self.current_polygon)
    print(f"[STATUS] Polygon: {points_count} Punkte gesetzt. ESC zum Beenden (min. 3 Punkte).")
    
def on_canvas_motion(self, event):
    """Handle mouse motion for drawing preview line"""
    if not self.drawing_mode or not self.current_polygon or self.original_frame is None:
        return
        
    # Remove previous preview line
    if self.temp_line_id:
        self.canvas.delete(self.temp_line_id)
        
    # Draw preview line from last point to current mouse position
    if len(self.current_polygon) > 0:
        last_point = self.current_polygon[-1]
        canvas_x1, canvas_y1 = self.video_to_canvas_coords(last_point[0], last_point[1])
        
        self.temp_line_id = self.canvas.create_line(
            canvas_x1, canvas_y1, event.x, event.y,
            fill="yellow", width=2, dash=(5, 5),
            tags=('drawn', 'temp_line')  # Add tags
        )
    
def on_canvas_right_click(self, event):
    """Handle right-click - no longer used for polygon completion"""
    if not self.drawing_mode:
        return
    
    # Show information about using ESC to complete polygons
    if len(self.current_polygon) >= 3:
        messagebox.showinfo("Polygon beenden", 
                            "Verwenden Sie die ESC-Taste, um das Polygon zu beenden.\n\n"
                            f"Aktuell: {len(self.current_polygon)} Punkte gesetzt.")
    else:
        messagebox.showinfo("Mehr Punkte erforderlich", 
                            f"Ein Polygon benötigt mindestens 3 Punkte.\n"
                            f"Aktuell: {len(self.current_polygon)} Punkte gesetzt.\n\n"
                            f"Verwenden Sie die ESC-Taste zum Beenden, "
                            f"wenn Sie mindestens 3 Punkte haben.")

def finish_current_polygon(self):
    """Finish the current polygon and add it to polygon areas with priority checking"""
    if len(self.current_polygon) >= 3:
        self.polygon_areas.append(self.current_polygon.copy())
        self.current_polygon = []
        
        # Remove preview line
        if self.temp_line_id:
            self.canvas.delete(self.temp_line_id)
            self.temp_line_id = None
            
        self.redraw_polygons_on_canvas()
        
        area_count = len(self.polygon_areas)
        print(f"[STATUS] Polygon #{area_count} hinzugefügt. Insgesamt {area_count} Polygone definiert.")
        
        # Update detector with new polygon areas
        if hasattr(self.detector, 'set_polygon_areas'):
            self.detector.set_polygon_areas(self.polygon_areas)
        
        # Check for ROI/Polygon priority conflict and notify user
        check_and_notify_priority_conflict(self)
        
        # Update start button state since we now have polygon areas
        self.update_start_button_state()
        
        messagebox.showinfo("Polygon hinzugefügt", 
                            f"Polygon #{area_count} wurde erfolgreich hinzugefügt!\n"
                            f"Insgesamt {area_count} Bereiche definiert.")

def check_and_notify_priority_conflict(self):
    """Check for ROI/Polygon conflict and notify user about priority - Scenario 1"""
    has_roi = hasattr(self, 'roi') and self.roi is not None
    has_polygons = self.polygon_areas and len(self.polygon_areas) > 0
    
    if has_roi and has_polygons:
        # Scenario 1: User drew polygon after ROI exists
        messagebox.showwarning(
            "ROI hat Priorität",
            f"Sie haben ein Polygon gezeichnet, während bereits ein ROI aktiv ist!\n\n"
            f"🎯 DAS ROI HAT PRIORITÄT\n\n"
            f"Das Polygon wird für die Erkennung IGNORIERT, "
            f"da das ROI bereits aktiv ist.\n\n"
            f"Nur das ROI wird für die Bewegungserkennung verwendet.\n\n"
            f"Um das Polygon zu verwenden, löschen Sie zuerst das ROI "
            f"mit 'Zeichnungen löschen' und zeichnen Sie das Polygon erneut."
        )
    
    # Update detection area status in GUI
    if hasattr(self, 'update_detection_area_status'):
        self.update_detection_area_status()

def canvas_to_video_coords(self, canvas_x, canvas_y):
    """Convert canvas coordinates to video coordinates"""
    if self.canvas_scale_x > 0 and self.canvas_scale_y > 0:
        video_x = int(canvas_x / self.canvas_scale_x)
        video_y = int(canvas_y / self.canvas_scale_y)
        return video_x, video_y
    return canvas_x, canvas_y

def video_to_canvas_coords(self, video_x, video_y):
    """Convert video coordinates to canvas coordinates"""
    canvas_x = int(video_x * self.canvas_scale_x)
    canvas_y = int(video_y * self.canvas_scale_y)
    return canvas_x, canvas_y

def redraw_polygons_on_canvas(self):
    """Thread-safe redraw of all polygons on the canvas"""
    # Ensure this runs in the main thread
    if threading.current_thread() is not threading.main_thread():
        self.root.after(0, self.redraw_polygons_on_canvas)
        return
        
    try:
        if self.original_frame is None:
            return
            
        # Check if canvas still exists
        if not hasattr(self, 'canvas') or not self.canvas.winfo_exists():
            return
            
        # Remove any existing polygon drawings (but keep the image)
        canvas_items = self.canvas.find_all()
        for item in canvas_items:
            if item != self.canvas_image:  # Keep the background image
                self.canvas.delete(item)
        
        # Draw completed polygons as actual polygons (not rectangles)
        for i, polygon in enumerate(self.polygon_areas):
            if len(polygon) >= 3:
                canvas_points = []
                for point in polygon:
                    canvas_x, canvas_y = self.video_to_canvas_coords(point[0], point[1])
                    canvas_points.extend([canvas_x, canvas_y])
                
                # Draw filled polygon with semi-transparent effect
                self.canvas.create_polygon(canvas_points, fill="lightgreen", 
                                            stipple="gray25", outline="green", width=3,
                                            smooth=True, tags=('drawn', 'polygon'))  # Add tags
                
                # Draw outline again for emphasis
                self.canvas.create_line(canvas_points + canvas_points[:2], 
                                        fill="darkgreen", width=2, smooth=True,
                                        tags=('drawn', 'polygon'))  # Add tags
                
                # Draw polygon number at centroid
                if canvas_points:
                    # Calculate polygon centroid
                    center_x = sum(canvas_points[::2]) / len(canvas_points[::2])
                    center_y = sum(canvas_points[1::2]) / len(canvas_points[1::2])
                    
                    # Add background circle for better visibility
                    self.canvas.create_oval(center_x-15, center_y-15, center_x+15, center_y+15,
                                            fill="white", outline="darkgreen", width=2,
                                            tags=('drawn', 'polygon'))  # Add tags
                    self.canvas.create_text(center_x, center_y, text=f"#{i+1}", 
                                            fill="darkgreen", font=("Arial", 10, "bold"),
                                            tags=('drawn', 'polygon'))  # Add tags
                                            
                                            
    except tk.TclError as e:
        if "invalid command name" in str(e):
            print(f"Canvas destroyed during polygon redraw: {e}")
        else:
            print(f"Canvas polygon error: {e}")
    except Exception as e:
        print(f"Polygon redraw error: {e}")
    
    # Draw current polygon being drawn as connected lines
    if len(self.current_polygon) >= 2:
        canvas_points = []
        for point in self.current_polygon:
            canvas_x, canvas_y = self.video_to_canvas_coords(point[0], point[1])
            canvas_points.extend([canvas_x, canvas_y])
        
        # Draw current polygon as connected line segments
        for i in range(0, len(canvas_points)-2, 2):
            self.canvas.create_line(canvas_points[i], canvas_points[i+1],
                                    canvas_points[i+2], canvas_points[i+3],
                                    fill="red", width=3, smooth=True,
                                    tags=('drawn', 'current_polygon'))  # Add tags
        
        # If we have 3+ points, show preview of closing line
        if len(self.current_polygon) >= 3:
            self.canvas.create_line(canvas_points[-2], canvas_points[-1],
                                    canvas_points[0], canvas_points[1],
                                    fill="red", width=2, dash=(5, 5),
                                    tags=('drawn', 'current_polygon'))  # Add tags
    
    # Draw points for current polygon with better visibility
    for i, point in enumerate(self.current_polygon):
        canvas_x, canvas_y = self.video_to_canvas_coords(point[0], point[1])
        # Draw point with number
        self.canvas.create_oval(canvas_x-6, canvas_y-6, canvas_x+6, canvas_y+6, 
                                fill="red", outline="darkred", width=2,
                                tags=('drawn', 'current_polygon'))  # Add tags
        self.canvas.create_text(canvas_x, canvas_y, text=str(i+1), 
                                fill="white", font=("Arial", 8, "bold"),
                                tags=('drawn', 'current_polygon'))  # Add tags

def get_polygon_areas(self):
    """Return the list of defined polygon areas"""
    return self.polygon_areas.copy()

def point_in_polygon(self, point, polygon):
    """Check if a point is inside a polygon using ray casting algorithm"""
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
        
    return inside

def check_bat_in_polygon_areas(self, bat_position):
    """Check if bat position is in any of the defined polygon areas"""
    if not self.polygon_areas:
        return False, -1
        
    for i, polygon in enumerate(self.polygon_areas):
        if len(polygon) >= 3 and self.point_in_polygon(bat_position, polygon):
            return True, i
    return False, -1
