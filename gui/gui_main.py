import tkinter as tk
from tkinter import messagebox, ttk

# Fix matplotlib font issues on Windows
import matplotlib
import matplotlib.pyplot as plt
import warnings

from detection import detection_and_analysis as detection
from export import export_functions as export_funcs
from gui import gui_creation_methods as gui_creation, parameter_and_ui_helpers as ui_helpers
from utils import progress_status_management as progress, results_and_data_management as results_mgmt, video_loading_and_management as video_loader, video_playback_and_controls as video_controls
from validation import event_validation as validation
from visualization import flight_path_and_visualization as flight_viz, polygon_drawing_and_roi_management as polygon_mgmt

# Suppress font warnings and configure safe fonts
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")
safe_fonts = ['DejaVu Sans', 'Arial', 'Segoe UI', 'Calibri', 'Tahoma', 'sans-serif']
matplotlib.rcParams['font.family'] = safe_fonts
matplotlib.rcParams['font.sans-serif'] = safe_fonts
matplotlib.rcParams['axes.unicode_minus'] = False
plt.rcParams.update({
    'font.family': safe_fonts,
    'font.sans-serif': safe_fonts,
    'axes.unicode_minus': False
})

from detection.video_detector import VideoDetector

# 3D Stereo Extension Import
try:
    STEREO_3D_AVAILABLE = True
except ImportError as e:
    # 3D Stereo extension not available - handled internally
    STEREO_3D_AVAILABLE = False

# Import modular components
from results_code import analysis_history_and_session_management as session_mgmt

# Import 3D analysis module conditionally
try:
    from gui import analysis_3d_and_stereo_vision as analysis_3d
    ANALYSIS_3D_AVAILABLE = analysis_3d.check_3d_availability()
    # 3D Analysis status checked - removed print statement for cleaner output
except ImportError as e:
    ANALYSIS_3D_AVAILABLE = False
    # 3D Analysis module not available - handled internally

def format_time(seconds):
    """Format seconds to HH:MM:SS format"""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

class BatDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fledermaus-Detektor Pro")

        # Get screen dimensions for responsive design
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Optimized for 14-inch screens (typically 1366x768 or 1920x1080)
        # Set minimum window size that fits comfortably on 14-inch screens
        min_width = min(1024, screen_width - 100)
        min_height = min(600, screen_height - 100)
        self.root.minsize(min_width, min_height)

        # Responsive window sizing based on actual screen dimensions
        if screen_width >= 1920 and screen_height >= 1080:
            # High-res screens: use more space but not maximized
            window_width = min(1600, screen_width - 100)
            window_height = min(900, screen_height - 100)
        elif screen_width >= 1366 and screen_height >= 768:
            # Standard 14-inch laptop screens
            window_width = min(1280, screen_width - 60)
            window_height = min(720, screen_height - 80)
        else:
            # Smaller screens: use most available space
            window_width = screen_width - 40
            window_height = screen_height - 60
        
        # Center the window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Configure proper window closing behavior
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Konfiguration des Hauptfensters
        self.root.configure(bg="#f0f0f0")
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Benutzerdefinierte Stile
        self.style.configure('TFrame', background="#f0f0f0")
        self.style.configure('TLabel', background="#f0f0f0", font=('Segoe UI', 9))
        self.style.configure('TButton', font=('Segoe UI', 9), padding=5)
        self.style.configure('TEntry', padding=3)
        self.style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'))
        self.style.configure('Status.TLabel', background="#e0e0e0", relief=tk.SUNKEN, padding=5)

        # Custom style for PDF export button (prominent blue)
        self.style.configure('PDF.TButton', font=('Segoe UI', 10, 'bold'),
                           foreground="#FFFFFF", background="#0066CC", padding=8)
        self.style.map('PDF.TButton',
                      background=[('active', '#0055AA'), ('pressed', '#004499')])

        # Accent button style
        self.style.configure('Accent.TButton', font=('Segoe UI', 9, 'bold'), padding=6)

        # Erkennungsparameter
        self.MOTION_THRESHOLD = 30
        self.COOLDOWN_FRAMES = 15
        self.MIN_CONTOUR_AREA = 5
        self.MAX_CONTOUR_AREA = 100

        self.debug_mode = tk.BooleanVar(value=False)

        # Mode status variable for 3D controls
        self.mode_status_var = tk.StringVar(value="Modus: 2D Standard")
        self.scale_factor = 0.5
        self.video_path = ""
        self.roi = None
        self.processing = False
        self.playing = False
        self.fps = 30
        self.total_frames = 0
        self.current_frame_idx = 0
        self.playback_speed = 1.0

        # Enhanced video player variables
        self.seeking = False  # Flag to prevent recursive updates during seeking

        # Drawing-related variables for polygon ROI
        self.drawing_mode = False
        self.polygon_areas = []  # List of completed polygon areas
        self.current_polygon = []  # Points of the polygon being drawn
        self.canvas_image = None
        self.canvas_scale_x = 1.0
        self.canvas_scale_y = 1.0
        self.original_frame = None
        self.temp_line_id = None  # For preview line while drawing

        # Multi-pass validation variables
        self.validation_session = None
        self.flight_path_data = []
        self.validation_history = []

        # 3D Stereo variables
        self.current_mode = "2D"  # Can be "2D", "3D", or "Hybrid"
        self.stereo_detector = None
        self.stereo_extension = None
        self.left_video_path = ""
        self.right_video_path = ""

        # Detektor initialisieren
        self.detector = VideoDetector(self)

        # Initialize background video processor
        from background_video_processor import BackgroundVideoProcessor
        self.background_processor = BackgroundVideoProcessor(self)
        self.current_progress_dialog = None

        # Set up proper window close handling
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Benutzeroberfläche erstellen
        self.setup_gui()

    def on_closing(self):
        """Handle application closing with proper cleanup"""
        try:
            # Stop video playback
            self.playing = False

            # Cancel any background processing
            if hasattr(self, 'background_processor'):
                self.background_processor.cancel_processing()

            # Close any progress dialogs
            if hasattr(self, 'current_progress_dialog') and self.current_progress_dialog:
                self.current_progress_dialog.close()

            # Close video capture
            if hasattr(self, 'cap') and self.cap.isOpened():
                self.cap.release()

            # Clear matplotlib figures
            plt.close('all')

        except Exception as e:
            # Cleanup error handled internally - removed console output
            pass
        finally:
            self.root.destroy()

    def setup_gui(self):
        """Konfiguriert die Hauptbenutzeroberfläche mit responsivem Design"""
        # Main container with responsive layout
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create responsive layout with PanedWindow for flexible sizing
        main_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)

        # Left Panel - Control area with scrollable content
        self.create_scrollable_control_panel(main_paned)

        # Right Panel - Video display and results
        self.create_display_panel(main_paned)

        # Configure paned window for responsive resizing
        # Optimized for 14-inch screens - narrower control panel
        screen_width = self.root.winfo_screenwidth()
        if screen_width <= 1366:
            # 14-inch screens: narrow control panel to maximize video space
            self.root.after(100, lambda: main_paned.sashpos(0, 300))
        elif screen_width <= 1600:
            # Medium screens: balanced layout
            self.root.after(100, lambda: main_paned.sashpos(0, 340))
        else:
            # Large screens: wider control panel
            self.root.after(100, lambda: main_paned.sashpos(0, 380))

        # GUI Creation Methods (delegated to modules)
    def create_scrollable_control_panel(self, main_paned):
        return gui_creation.create_scrollable_control_panel(self, main_paned)

    def create_display_panel(self, main_paned):
        return gui_creation.create_display_panel(self, main_paned)

    def create_video_area(self, parent):
        return gui_creation.create_video_area(self, parent)

    def create_video_controls(self, parent):
        return gui_creation.create_video_controls(self, parent)

    def create_results_area(self, parent):
        return gui_creation.create_results_area(self, parent)

    def create_file_controls(self, parent):
        return gui_creation.create_file_controls(self, parent)

    def create_detection_controls(self, parent):
        return gui_creation.create_detection_controls(self, parent)

    def create_parameter_controls(self, parent):
        return gui_creation.create_parameter_controls(self, parent)

    def create_export_controls(self, parent):
        return gui_creation.create_export_controls(self, parent)

    def create_3d_controls(self, parent):
        return gui_creation.create_3d_controls(self, parent)

    # Parameter and UI Helper Methods
    def add_compact_parameter_entry(self, parent, label, default, attr, row=None):
        return ui_helpers.add_compact_parameter_entry(self, parent, label, default, attr, row)

    def add_parameter_entry(self, parent, label, default, attr):
        return ui_helpers.add_parameter_entry(self, parent, label, default, attr)

    def add_labeled_entry(self, parent, label, default, attr):
        return ui_helpers.add_labeled_entry(self, parent, label, default, attr)

    def initialize_3d_button_state(self):
        return ui_helpers.initialize_3d_button_state(self)

    # Video Loading and Management Methods
    def load_video(self):
        return video_loader.load_video(self)

    def load_video_file(self, file_path=None):
        return video_loader.load_video_file(self, file_path)

    def update_start_button_state(self):
        return video_loader.update_start_button_state(self)

    def on_select_roi(self):
        return video_loader.on_select_roi(self)

    # Video Playback and Controls Methods
    def show_frame(self, frame):
        return video_controls.show_frame(self, frame)

    def play_video(self):
        return video_controls.play_video(self)

    def pause_video(self):
        return video_controls.pause_video(self)

    def stop_video(self):
        return video_controls.stop_video(self)

    def step_forward(self):
        return video_controls.step_forward(self)

    def step_backward(self):
        return video_controls.step_backward(self)

    def jump_seconds(self, seconds):
        return video_controls.jump_seconds(self, seconds)

    def seek_to_frame(self, frame_number):
        return video_controls.seek_to_frame(self, frame_number)

    def seek_to_time(self, time_seconds):
        return video_controls.seek_to_time(self, time_seconds)

    def goto_frame(self):
        return video_controls.goto_frame(self)

    def on_timeline_change(self, event=None):
        return video_controls.on_timeline_change(self, event)

    def _resume_after_seek(self):
        return video_controls._resume_after_seek(self)

    def update_timeline_and_time(self):
        return video_controls.update_timeline_and_time(self)

    def enable_video_controls(self):
        return video_controls.enable_video_controls(self)

    def set_speed(self, event=None):
        return video_controls.set_speed(self, event)

    def _stream_video(self):
        return video_controls._stream_video(self)

    def update_time_label(self, current_sec):
        return video_controls.update_time_label(self, current_sec)

    def enable_export_buttons(self):
        return video_controls.enable_export_buttons(self)

    # Detection and Analysis Methods
    def start_detection(self):
        return detection.start_detection(self)

    def determine_detection_mode(self):
        return detection.determine_detection_mode(self)

    def stop_detection(self):
        return detection.stop_detection(self)

    def on_detection_finished(self):
        return detection.on_detection_finished(self)

    def on_progress_update(self, progress):
        return detection.on_progress_update(self, progress)

    # Event Validation Methods
    def validate_events_gui(self):
        return validation.validate_events_gui(self)

    def show_fast_event_overview(self):
        return validation.show_fast_event_overview(self)

    def create_event_grid_view(self, parent, events):
        return validation.create_event_grid_view(self, parent, events)

    def generate_event_thumbnails(self, events):
        return validation.generate_event_thumbnails(self, events)

    def highlight_detection_area(self, frame, roi):
        return validation.highlight_detection_area(self, frame, roi)

    def mark_event_validation(self, event_idx, is_valid):
        return validation.mark_event_validation(self, event_idx, is_valid)

    def show_event_detail(self, event_idx):
        return validation.show_event_detail(self, event_idx)

    def load_event_preview(self, event_idx):
        return validation.load_event_preview(self, event_idx)

    def create_timeline_view(self, parent):
        return validation.create_timeline_view(self, parent)

    def create_motion_heatmap_view(self, parent):
        return validation.create_motion_heatmap_view(self, parent)

    def batch_validate_events(self, validation_decisions):
        return validation.batch_validate_events(self, validation_decisions)

    def enhanced_validate_events(self):
        return validation.enhanced_validate_events(self)

    def replay_validation(self):
        return validation.replay_validation(self)

    def cleanup_overview_bindings(self):
        return validation.cleanup_overview_bindings(self)

    def draw_timeline(self, canvas, events):
        return validation.draw_timeline(self, canvas, events)

    def draw_heatmap(self, canvas, events):
        return validation.draw_heatmap(self, canvas, events)

    # Detection Area Priority Management
    def update_detection_area_status(self):
        """Update GUI status to show current active detection area"""
        if hasattr(self, 'detector') and self.detector:
            area_info = self.detector.get_active_detection_area_info()
            mode = area_info.get("mode", "none")
            
            if mode == "roi_priority":
                status_msg = f"🎯 AKTIV: ROI (Polygone ignoriert: {area_info.get('polygon_count', 0)})"
            elif mode == "roi_only":
                status_msg = "🎯 AKTIV: Rechteckiges ROI"
            elif mode == "polygon_only":
                count = area_info.get('polygon_count', 0)
                status_msg = f"🔷 AKTIV: {count} Polygon{'e' if count > 1 else ''}"
            elif mode == "full_frame":
                status_msg = "🖼️ AKTIV: Gesamtes Video"
            else:
                status_msg = "❌ Kein Erkennungsbereich definiert"
            
            self.update_status(status_msg)
    
    def show_detection_area_priority_info(self):
        """Show detailed information about detection area priority"""
        if hasattr(self, 'detector') and self.detector:
            area_info = self.detector.get_active_detection_area_info()
            mode = area_info.get("mode", "none")
            
            if mode == "roi_priority":
                messagebox.showinfo(
                    "Erkennungsbereich-Status",
                    f"AKTUELL AKTIV: Rechteckiges ROI\n\n"
                    f"ROI-Koordinaten: {area_info.get('roi', 'Nicht verfügbar')}\n"
                    f"Ignorierte Polygone: {area_info.get('polygon_count', 0)}\n\n"
                    f"Das ROI hat Priorität über alle Polygone.\n"
                    f"Um Polygone zu verwenden, löschen Sie das ROI."
                )
            elif mode == "roi_only":
                messagebox.showinfo(
                    "Erkennungsbereich-Status",
                    f"AKTUELL AKTIV: Rechteckiges ROI\n\n"
                    f"ROI-Koordinaten: {area_info.get('roi', 'Nicht verfügbar')}\n"
                    f"Keine Polygone definiert."
                )
            elif mode == "polygon_only":
                count = area_info.get('polygon_count', 0)
                messagebox.showinfo(
                    "Erkennungsbereich-Status",
                    f"AKTUELL AKTIV: {count} Polygon{'e' if count > 1 else ''}\n\n"
                    f"Kein ROI definiert.\n"
                    f"Alle definierten Polygone werden für die Erkennung verwendet."
                )
            elif mode == "full_frame":
                messagebox.showinfo(
                    "Erkennungsbereich-Status",
                    f"AKTUELL AKTIV: Gesamtes Video\n\n"
                    f"Weder ROI noch Polygone sind definiert.\n"
                    f"Das gesamte Video wird für die Erkennung verwendet."
                )
            else:
                messagebox.showinfo(
                    "Erkennungsbereich-Status",
                    "Kein Erkennungsbereich definiert.\n\n"
                    "Definieren Sie ein ROI oder Polygone für die Erkennung."
                )

    # Export Functions Methods
    def export_results(self):
        return export_funcs.export_results(self)

    def export_summary_csv(self):
        return export_funcs.export_summary_csv(self)

    def prompt_marked_video_export(self):
        return export_funcs.prompt_marked_video_export(self)

    def export_marked_video(self):
        return export_funcs.export_marked_video(self)

    def export_marked_video_background(self):
        return export_funcs.export_marked_video_background(self)

    def export_flightMap(self):
        return export_funcs.export_flightMap(self)

    def export_pdf_report(self):
        return export_funcs.export_pdf_report(self)

    def export_radar_view(self):
        return export_funcs.export_radar_view(self)

    def export_gis_data(self):
        return export_funcs.export_gis_data(self)

    def export_hotzone(self):
        return export_funcs.export_hotzone(self)

    def cleanup_bindings(self):
        return export_funcs.cleanup_bindings(self)

    def do_export(self, export_type):
        return export_funcs.do_export(self, export_type)

    def on_export_progress(self, progress):
        return export_funcs.on_export_progress(self, progress)

    # Flight Path and Visualization Methods
    def generate_bat_paths_from_events(self):
        return flight_viz.generate_bat_paths_from_events(self)

    def display_flight_map(self, image_path=None):
        return flight_viz.display_flight_map(self, image_path)

    def create_radar_view_tab(self, notebook, flight_window):
        return flight_viz.create_radar_view_tab(self, notebook, flight_window)

    def draw_radar_grid(self, canvas):
        return flight_viz.draw_radar_grid(self, canvas)

    def draw_flight_paths_on_radar(self, canvas):
        return flight_viz.draw_flight_paths_on_radar(self, canvas)

    def create_video_overlay_display(self, parent_frame):
        return flight_viz.create_video_overlay_display(self, parent_frame)

    def play_video_with_overlay(self, canvas):
        return flight_viz.play_video_with_overlay(self, canvas)

    def overlay_flight_paths_on_frame(self, frame):
        return flight_viz.overlay_flight_paths_on_frame(self, frame)

    def pause_video_overlay(self):
        return flight_viz.pause_video_overlay(self)

    def stop_video_overlay(self):
        return flight_viz.stop_video_overlay(self)

    def save_current_view(self):
        return flight_viz.save_current_view(self)

    def view_flight_paths(self):
        return flight_viz.view_flight_paths(self)

    def update_video_frame(self):
        return flight_viz.update_video_frame(self)

    def close_flight_window(self):
        return flight_viz.close_flight_window(self)

    # Polygon Drawing and ROI Management Methods
    def toggle_drawing_mode(self):
        return polygon_mgmt.toggle_drawing_mode(self)

    def clear_polygon_areas(self):
        return polygon_mgmt.clear_polygon_areas(self)
    
    def clear_shapes(self):
        return polygon_mgmt.clear_shapes(self)
    
    def delete_drawings(self):
        return polygon_mgmt.delete_drawings(self)

    def on_escape_key(self, event):
        return polygon_mgmt.on_escape_key(self, event)

    def on_canvas_click(self, event):
        return polygon_mgmt.on_canvas_click(self, event)

    def on_canvas_motion(self, event):
        return polygon_mgmt.on_canvas_motion(self, event)

    def on_canvas_right_click(self, event):
        return polygon_mgmt.on_canvas_right_click(self, event)

    def finish_current_polygon(self):
        return polygon_mgmt.finish_current_polygon(self)

    def canvas_to_video_coords(self, canvas_x, canvas_y):
        return polygon_mgmt.canvas_to_video_coords(self, canvas_x, canvas_y)

    def video_to_canvas_coords(self, video_x, video_y):
        return polygon_mgmt.video_to_canvas_coords(self, video_x, video_y)

    def redraw_polygons_on_canvas(self):
        return polygon_mgmt.redraw_polygons_on_canvas(self)

    def get_polygon_areas(self):
        return polygon_mgmt.get_polygon_areas(self)

    def point_in_polygon(self, point, polygon):
        return polygon_mgmt.point_in_polygon(self, point, polygon)

    def check_bat_in_polygon_areas(self, bat_center):
        return polygon_mgmt.check_bat_in_polygon_areas(self, bat_center)

    # Progress and Status Management Methods
    def update_progress_bar(self, value):
        return progress.update_progress_bar(self, value)

    def show_progress_dialog(self, title="Verarbeitung", cancelable=True):
        return progress.show_progress_dialog(self, title, cancelable)

    def hide_progress_dialog(self):
        return progress.hide_progress_dialog(self)

    def show_processing_animation(self):
        return progress.show_processing_animation(self)

    def hide_processing_animation(self):
        return progress.hide_processing_animation(self)

    def force_close_animation(self):
        return progress.force_close_animation(self)

    def update_status(self, msg):
        return progress.update_status(self, msg)

    # Results and Data Management Methods
    def update_event_display(self):
        return results_mgmt.update_event_display(self)

    def show_results_access_panel(self, event=None):
        return results_mgmt.show_results_access_panel(self, event)

    def show_results_access_window(self, video_folders, results_dir):
        return results_mgmt.show_results_access_window(self, video_folders, results_dir)

    def create_result_folder_card(self, parent, folder_name, folder_path, index, access_window):
        return results_mgmt.create_result_folder_card(self, parent, folder_name, folder_path, index, access_window)

    def analyze_folder_files(self, folder_path):
        return results_mgmt.analyze_folder_files(self, folder_path)

    def open_file_with_system(self, file_path):
        return results_mgmt.open_file_with_system(self, file_path)

    def open_csv_files_menu(self, csv_files, folder_name=None):
        return results_mgmt.open_csv_files_menu(self, csv_files, folder_name)

    def open_video_files_menu(self, video_files, folder_name=None):
        return results_mgmt.open_video_files_menu(self, video_files, folder_name)

    def open_image_files_menu(self, image_files, folder_name=None):
        return results_mgmt.open_image_files_menu(self, image_files, folder_name)

    def show_file_selection_menu(self, files, folder_name, title=None, icon=None):
        # For backward compatibility, handle old signature
        if title is None and icon is None:
            # Old signature: show_file_selection_menu(files, file_type)
            file_type = folder_name  # folder_name is actually file_type in old usage
            return results_mgmt.show_file_selection_menu(self, files, file_type)
        else:
            # New signature: show_file_selection_menu(files, folder_name, title, icon)
            return results_mgmt.show_file_selection_menu(self, files, folder_name, title, icon)

    def get_file_size_str(self, file_path):
        return results_mgmt.get_file_size_str(self, file_path)

    def load_folder_results_for_analysis(self, folder_path, folder_name, parent_window):
        return results_mgmt.load_folder_results_for_analysis(self, folder_path, folder_name, parent_window)

    def refresh_results_window(self):
        return results_mgmt.refresh_results_window(self)

    def load_previous_video_results(self, event=None):
        return results_mgmt.load_previous_video_results(self, event)

    def show_video_folder_selection(self, video_folders, results_dir):
        return results_mgmt.show_video_folder_selection(self, video_folders, results_dir)

    def count_events_in_csv(self, csv_path):
        return results_mgmt.count_events_in_csv(self, csv_path)

    def load_video_results_from_folder(self, folder_path, folder_name):
        return results_mgmt.load_video_results_from_folder(self, folder_path, folder_name)

    def load_events_from_csv(self, csv_path):
        return results_mgmt.load_events_from_csv(self, csv_path)

    def parse_time_to_seconds(self, time_str):
        return results_mgmt.parse_time_to_seconds(self, time_str)

    def show_loaded_events_window(self, events, source_info):
        return results_mgmt.show_loaded_events_window(self, events, source_info)

    def format_time(self, seconds):
        return results_mgmt.format_time(self, seconds)

    def safe_format_time(self, seconds):
        return results_mgmt.safe_format_time(self, seconds)

    def check_manual_folder_contents(self, folder_path):
        return results_mgmt.check_manual_folder_contents(self, folder_path)

    def load_manual_folder_results(self, folder_path):
        return results_mgmt.load_manual_folder_results(self, folder_path)

    def validate_csv_file(self, csv_path):
        return results_mgmt.validate_csv_file(self, csv_path)

    def select_csv_file(self):
        return results_mgmt.select_csv_file(self)

    def find_associated_video(self, folder_path, folder_name):
        return results_mgmt.find_associated_video(self, folder_path, folder_name)

    def configure_scroll_region(self, canvas, frame):
        return results_mgmt.configure_scroll_region(self, canvas, frame)

    def configure_canvas_width(self, canvas, frame):
        return results_mgmt.configure_canvas_width(self, canvas, frame)

    def _bind_mousewheel(self, canvas):
        return results_mgmt._bind_mousewheel(self, canvas)

    def _unbind_mousewheel(self, canvas):
        return results_mgmt._unbind_mousewheel(self, canvas)

    def on_double_click(self, folder_info):
        return results_mgmt.on_double_click(self, folder_info)

    def open_selected(self, folder_info):
        return results_mgmt.open_selected(self, folder_info)

    def browse_folder(self):
        return results_mgmt.browse_folder(self)

    def load_manual_folder(self, folder_path):
        return results_mgmt.load_manual_folder(self, folder_path)

    def select_csv(self):
        return results_mgmt.select_csv(self)

    def load_selected_auto(self, folder_info):
        return results_mgmt.load_selected_auto(self, folder_info)

    def confirm_selection(self, folder_info):
        return results_mgmt.confirm_selection(self, folder_info)

    # Analysis History and Session Management Methods
    def check_existing_analysis(self, video_path=None):
        return session_mgmt.check_existing_analysis(self, video_path)

    def show_analysis_history_dialog(self, analysis_info):
        return session_mgmt.show_analysis_history_dialog(self, analysis_info)

    def show_folder_choice_dialog(self):
        return session_mgmt.show_folder_choice_dialog(self)

    def show_video_info_dialog(self, video_path):
        return session_mgmt.show_video_info_dialog(self, video_path)

    def show_previous_events_enhanced(self, events, session_info=None):
        return session_mgmt.show_previous_events_enhanced(self, events, session_info)

    def show_enhanced_event_viewer(self, events, session_info=None):
        return session_mgmt.show_enhanced_event_viewer(self, events, session_info)

    def navigate_to_event(self, event_data):
        return session_mgmt.navigate_to_event(self, event_data)

    def refresh_event_points(self):
        return session_mgmt.refresh_event_points(self)

    def load_existing_analysis(self, folder_path):
        return session_mgmt.load_existing_analysis(self, folder_path)

    def update_video_workflow_status(self, status):
        return session_mgmt.update_video_workflow_status(self, status)

    def show_validation_history(self):
        return session_mgmt.show_validation_history(self)

    def _bind_to_mousewheel(self, widget, canvas):
        return session_mgmt._bind_to_mousewheel(self, widget, canvas)

    def _unbind_from_mousewheel(self, widget):
        return session_mgmt._unbind_from_mousewheel(self, widget)

    def load_existing(self):
        return session_mgmt.load_existing(self)

    def continue_new(self):
        return session_mgmt.continue_new(self)

    def cancel(self):
        return session_mgmt.cancel(self)

    def choose_reuse(self):
        return session_mgmt.choose_reuse(self)

    def choose_new_version(self):
        return session_mgmt.choose_new_version(self)

    def create_pdf(self):
        return session_mgmt.create_pdf(self)

    def on_event_double_click(self, event):
        return session_mgmt.on_event_double_click(self, event)

    # 3D Analysis and Stereo Vision Methods (conditional)
    if ANALYSIS_3D_AVAILABLE:
        def show_3d_visualization(self):
            return analysis_3d.show_3d_visualization(self)

        def switch_to_2d_mode(self):
            return analysis_3d.switch_to_2d_mode(self)

        def switch_to_3d_mode(self):
            return analysis_3d.switch_to_3d_mode(self)

        def switch_to_hybrid_mode(self):
            return analysis_3d.switch_to_hybrid_mode(self)

        def load_stereo_videos(self):
            return analysis_3d.load_stereo_videos(self)

        def start_3d_analysis(self):
            return analysis_3d.start_3d_analysis(self)

        def on_3d_analysis_complete(self, results):
            return analysis_3d.on_3d_analysis_complete(self, results)

        def on_3d_analysis_error(self, error):
            return analysis_3d.on_3d_analysis_error(self, error)

        def view_3d_visualization(self):
            return analysis_3d.view_3d_visualization(self)

        def open_3d_analysis_gui(self):
            return analysis_3d.open_3d_analysis_gui(self)

        def start_stereo_calibration(self):
            return analysis_3d.start_stereo_calibration(self)

        def progress_callback(self, progress):
            return analysis_3d.progress_callback(self, progress)

        def run_detection(self):
            return analysis_3d.run_detection(self)

        def create_visualization(self):
            return analysis_3d.create_visualization(self)
    else:
        # Fallback methods when 3D analysis is not available
        def show_3d_visualization(self):
            messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")

        def switch_to_2d_mode(self):
            pass  # Already in 2D mode

        def switch_to_3d_mode(self):
            messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")

        def switch_to_hybrid_mode(self):
            messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")

        def load_stereo_videos(self):
            messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")

        def start_3d_analysis(self):
            messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")

        def on_3d_analysis_complete(self, results):
            pass

        def on_3d_analysis_error(self, error):
            pass

        def view_3d_visualization(self):
            messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")

        def open_3d_analysis_gui(self):
            messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")

        def start_stereo_calibration(self):
            messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")

        def progress_callback(self, progress):
            pass

        def run_detection(self):
            messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")

        def create_visualization(self):
            messagebox.showinfo("3D Nicht verfügbar", "3D-Analyse-Module ist nicht verfügbar.")

    # Legacy methods that need to remain for compatibility
    def reset_analysis_session(self):
        """Reset the current analysis session to prepare for new analysis"""
        # Clear detector state
        if hasattr(self.detector, 'events'):
            self.detector.events = []
        if hasattr(self.detector, 'marked_frames'):
            self.detector.marked_frames = []
        if hasattr(self.detector, 'bat_centers'):
            self.detector.bat_centers = []

        # Reset validation state
        self.validation_session = None
        self.flight_path_data = []
        self.validation_history = []

        # Clear ROI and polygons if desired
        # self.roi = None
        # self.polygon_areas = []

        # Disable export buttons until new analysis is complete
        self.disable_export_buttons()

        # Update event display
        self.update_event_display()

    def disable_export_buttons(self):
        """Disable export buttons when no analysis data is available"""
        if hasattr(self, 'btn_export_csv'):
            self.btn_export_csv.config(state=tk.DISABLED)
        if hasattr(self, 'btn_export_pdf'):
            self.btn_export_pdf.config(state=tk.DISABLED)
        if hasattr(self, 'btn_validate'):
            self.btn_validate.config(state=tk.DISABLED)
        if hasattr(self, 'btn_replay_validation'):
            self.btn_replay_validation.config(state=tk.DISABLED)

    def update_analysis_workflow_status(self, status):
        """Update status display with workflow information - now console only"""
        try:
            if status == "running":
                workflow_info = ""  # Analysis running message removed
            elif status == "completed":
                workflow_info = "✅ Analyse abgeschlossen"
            elif status == "validation":
                workflow_info = "🔍 Validierung aktiv"
            else:
                workflow_info = f"Status: {status}"

            # Workflow info displayed in GUI status - removed console output
        except:
            pass  # Don't fail if status update fails

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling in control panel"""
        if hasattr(self, 'control_canvas') and self.control_canvas.winfo_exists():
            self.control_canvas.yview_scroll(int(-1*(event.delta/120)), "units")


if __name__ == "__main__":
    root = tk.Tk()
    app = BatDetectorApp(root)
    root.mainloop()