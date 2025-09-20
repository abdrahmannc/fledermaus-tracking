import tkinter as tk
from tkinter import messagebox
import cv2

# Fix matplotlib font issues on Windows




          
def start_detection(self, event=None):
        """Enhanced detection with comprehensive ROI/polygon support and structured workflow"""
        if not self.video_path:
            messagebox.showerror("Fehler", "Bitte laden Sie zuerst ein Video!")
            return
        
        try:
            # Check if this will create a new analysis or add to existing
            analysis_info = self.check_existing_analysis(self.video_path)
            
            if analysis_info["exists"]:
                # Confirm if user wants to create additional analysis
                response = messagebox.askyesno(
                    "Zusätzliche Analyse", 
                    f"Für dieses Video existiert bereits eine Analyse.\n\n"
                    f"Möchten Sie eine zusätzliche Analyse durchführen?\n"
                    f"Dies erstellt neue Dateien neben den bestehenden.",
                    icon='question'
                )
                if not response:
                    return
            
            # Reset analysis session for clean start
            self.reset_analysis_session()
            
            # Determine detection mode and configure accordingly
            detection_mode = self.determine_detection_mode()
            
            if detection_mode == "polygon":
                # Case 2: User has drawn polygons
                self.detector.set_polygon_areas(self.polygon_areas)
                # CRITICAL: Clear ROI to ensure polygon detection is used
                self.detector.roi = None
                self.update_status(f"Erkennung gestartet mit {len(self.polygon_areas)} Polygon-Bereichen...")
                
                # Ensure polygon detection is properly configured
                if hasattr(self.detector, 'enable_polygon_filtering'):
                    self.detector.enable_polygon_filtering(True)
                    
            elif detection_mode == "roi" and self.roi:
                # Case 1: Traditional ROI exists - keep existing logic
                self.detector.roi = self.roi
                self.update_status("Erkennung gestartet mit traditionellem ROI...")
                
            else:
                # Case 3: Whole video detection
                self.update_status("Erkennung gestartet (gesamtes Video)...")
            
            # Show progress dialog for long videos
            progress_dialog = self.show_progress_dialog("Fledermaus-Erkennung läuft...", cancelable=True)
            
            # Start detection in background
            def on_progress_update(progress):
                if progress_dialog and not progress_dialog.is_cancelled():
                    percentage = progress.get_percentage()
                    status_text = progress.get_status_text()
                    progress_dialog.update_progress(percentage, status_text)
                    
                    # Close dialog when detection is completed
                    if percentage >= 100:
                        self.hide_progress_dialog()
                        return
                    
                # Check for cancellation
                if progress_dialog and progress_dialog.is_cancelled():
                    self.background_processor.cancel_processing()
                    self.hide_progress_dialog()
                    self.update_status("Detection cancelled by user")
                    self.hide_processing_animation()
                    self.btn_stop.config(state=tk.DISABLED)
                    self.btn_start.config(state=tk.NORMAL)
                    return
            
            # Configure detector with proper settings
            self.detector.cap = cv2.VideoCapture(self.video_path)
            self.detector.fps = self.fps
            
            # Start background detection
            success = self.background_processor.start_detection_background(
                self.detector, 
                progress_callback=on_progress_update
            )
            
            if not success:
                self.hide_progress_dialog()
                messagebox.showerror("Fehler", "Erkennung läuft bereits oder konnte nicht gestartet werden")
                return
            
            # Update button states
            self.btn_stop.config(state=tk.NORMAL)
            self.btn_start.config(state=tk.DISABLED)
            self.enable_export_buttons()
            self.btn_validate.config(state=tk.NORMAL)
            self.btn_replay_validation.config(state=tk.NORMAL)
            
            # Update workflow status
            self.update_analysis_workflow_status("running")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte Erkennung nicht starten: {str(e)}")
            self.hide_processing_animation()




def determine_detection_mode(self):
        """Determine the appropriate detection mode based on user input with correct priority"""
        # Priority: ROI first, then polygons, then whole video
        if self.roi is not None:
            return "roi"
        elif self.polygon_areas and len(self.polygon_areas) > 0:
            return "polygon"
        else:
            return "whole_video"



 # Also log to console
def stop_detection(self, event=None):
        """Stop detection and update UI - enhanced for background processing"""
        # Cancel background processing
        if hasattr(self, 'background_processor'):
            self.background_processor.cancel_processing()
        
        # Stop detector
        self.detector.stop_detection()
        
        # Hide progress dialog and animation
        self.hide_progress_dialog()
        self.hide_processing_animation()
        
        # Update status and buttons
        # Detection stopped - removed print statement for cleaner output
        self.btn_stop.config(state=tk.DISABLED)
        self.update_start_button_state()




def on_detection_finished(self):
        """
        Enhanced detection completion handler for background processing.
        Wird vom VideoDetector aufgerufen, nachdem der Erkennungs-Thread abgeschlossen ist.
        """
        try:
            # Hide progress dialog and animation - multiple calls to ensure it closes
            self.hide_progress_dialog()
            self.hide_processing_animation()
            
            # Force close any remaining progress dialogs after a short delay
            def force_close_dialogs():
                self.hide_progress_dialog()
            
            self.root.after(200, force_close_dialogs)  # 200ms delay
            
            # Update button states
            self.btn_stop.config(state=tk.DISABLED)
            self.btn_start.config(state=tk.NORMAL)
            
            # Update workflow status
            self.update_analysis_workflow_status("completed")
            
            # Update results display
            self.update_event_display()
            
            # Show completion status
            num_events = len(self.detector.events) if hasattr(self.detector, 'events') else 0
            self.update_status(f"Detection finished, {num_events} events detected")
            
            # Automatically export CSV results to create result folder structure
            if hasattr(self.detector, 'events') and self.detector.events:
                try:
                    # Call detector's export_results method to create CSV files and result folders
                    self.detector.export_results()
                    # Automatically exported CSV results - removed console output for cleaner interface
                except Exception as e:
                    # Auto-export failed but error handled internally - removed console output
                    pass
                
                # Prompt user to save marked video after successful detection
                # Use after_idle to ensure GUI is fully updated before showing dialog
                self.root.after_idle(self.prompt_marked_video_export)
            else:
                # No events detected - auto-export skipped
                pass
                
        except Exception as e:
            # Error handled internally by error handling system
            pass
            self.update_status(f"Detection completed with errors: {e}")
            self.hide_progress_dialog()
            self.hide_processing_animation()