import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import csv
from datetime import datetime

# Fix matplotlib font issues on Windows

def format_time(seconds):
    """Format seconds to HH:MM:SS format"""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"



def update_event_display(self):
    """Update the event display in the treeview with safe entry/exit time handling"""
    # Clear existing items
    for item in self.tree.get_children():
        self.tree.delete(item)
        
    # Add events to treeview
    if hasattr(self.detector, 'events'):
        for event in self.detector.events:
            # Safe handling of entry time
            entry_time = event.get('entry') or event.get('einflugzeit')
            if entry_time is None:
                entry_time_str = "unbekannt"
            else:
                entry_time_str = self.format_time(entry_time)
            
            # Safe handling of exit time  
            exit_time = event.get('exit') or event.get('ausflugzeit')
            if exit_time is None:
                exit_time_str = "unbekannt"
            else:
                exit_time_str = self.format_time(exit_time)
            
            # Safe handling of duration
            duration = event.get('duration') or event.get('dauer')
            if duration is None:
                duration_str = "unbekannt"
            elif duration <= 0:
                duration_str = "unbekannt"
            else:
                duration_str = f"{duration:.1f}s"
            
            # Add visual indicator for incomplete events
            if event.get('incomplete', False):
                entry_time_str += " ⚠"
                exit_time_str += " ⚠"
                duration_str += " ⚠"
            
            self.tree.insert('', 'end', values=(entry_time_str, exit_time_str, duration_str))


def show_results_access_panel(self, event=None):
    """Show comprehensive results access panel for opening all types of result files"""
    try:
        # Get app root directory and results folder
        app_root = os.path.dirname(os.path.dirname(__file__))
        results_dir = os.path.join(app_root, "results")
        
        if not os.path.exists(results_dir):
            messagebox.showinfo("Keine Ergebnisse", 
                                "Der Ergebnisordner existiert noch nicht.\n"
                                "Führen Sie zunächst eine Videoanalyse durch.")
            return
        
        # Get all video result folders
        video_folders = []
        for item in os.listdir(results_dir):
            folder_path = os.path.join(results_dir, item)
            if os.path.isdir(folder_path) and not item.startswith('.'):
                # Get the modification time for sorting
                try:
                    mod_time = os.path.getmtime(folder_path)
                    video_folders.append((item, folder_path, mod_time))
                except:
                    # Fallback if stat fails
                    video_folders.append((item, folder_path, 0))
        
        # Sort by modification time (most recent first)
        video_folders.sort(key=lambda x: x[2], reverse=True)
        
        # Remove the timestamp from tuples for compatibility
        video_folders = [(item, folder_path) for item, folder_path, _ in video_folders]
        
        if not video_folders:
            messagebox.showinfo("Keine Ergebnisse", 
                                "Keine Videoergebnisse gefunden.\n"
                                "Führen Sie zunächst eine Videoanalyse durch.")
            return
        
        # Create results access window
        self.show_results_access_window(video_folders, results_dir)
        
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Laden der Ergebnisse: {str(e)}")

def show_results_access_window(self, video_folders, results_dir):
    """Display the results access window with all available result files"""
    access_window = tk.Toplevel(self.root)
    access_window.title("📁 Ergebnisse öffnen - Fledermaus-Analysen")
    
    # Make window fully responsive - no fixed height
    access_window.minsize(900, 600)
    access_window.resizable(True, True)
    access_window.transient(self.root)
    
    # Configure window grid for proper expansion
    access_window.grid_rowconfigure(0, weight=1)
    access_window.grid_columnconfigure(0, weight=1)
    
    # Center window on screen
    access_window.update_idletasks()
    screen_width = access_window.winfo_screenwidth()
    screen_height = access_window.winfo_screenheight()
    window_width = min(1000, screen_width - 100)
    window_height = min(700, screen_height - 100)
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    access_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Main container with grid layout for proper responsiveness
    main_container = ttk.Frame(access_window)
    main_container.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
    
    # Configure main container grid weights
    main_container.grid_rowconfigure(1, weight=1)  # Content area expands
    main_container.grid_rowconfigure(0, weight=0)  # Header fixed
    main_container.grid_rowconfigure(2, weight=0)  # Footer fixed
    main_container.grid_columnconfigure(0, weight=1)
    
    # Header - fixed height
    header_frame = ttk.Frame(main_container)
    header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
    
    ttk.Label(header_frame, text="🦇 Analyseergebnisse verwalten", 
                font=('Segoe UI', 16, 'bold')).pack(side=tk.LEFT)
    
    # Refresh button
    refresh_btn = ttk.Button(header_frame, text="🔄 Aktualisieren", 
                            command=lambda: self.refresh_results_window(access_window, results_dir))
    refresh_btn.pack(side=tk.RIGHT)
    
    # Main content frame with scrolling - expandable
    content_frame = ttk.Frame(main_container)
    content_frame.grid(row=1, column=0, sticky="nsew")
    
    # Configure content frame for proper scrolling
    content_frame.grid_rowconfigure(0, weight=1)
    content_frame.grid_columnconfigure(0, weight=1)
    
    # Create scrollable canvas with proper responsive behavior
    canvas = tk.Canvas(content_frame, highlightthickness=0)
    scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    # Bind frame configuration for automatic scrolling
    def configure_scroll_region(event):
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def configure_canvas_width(event):
        # Make the canvas content expand with window width
        canvas_width = canvas.winfo_width()
        canvas.itemconfig(canvas_window, width=canvas_width)
    
    scrollable_frame.bind("<Configure>", configure_scroll_region)
    canvas.bind("<Configure>", configure_canvas_width)
    
    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Grid layout for canvas and scrollbar
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    def _on_mousewheel(event):
        try:
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except tk.TclError:
            # Canvas has been destroyed, ignore the event
            pass

    def _bind_mousewheel(event):
        try:
            if canvas.winfo_exists():
                canvas.bind_all("<MouseWheel>", _on_mousewheel)
        except tk.TclError:
            # Canvas has been destroyed, cannot bind
            pass
    
    def _unbind_mousewheel(event):
        try:
            if canvas.winfo_exists():
                canvas.unbind_all("<MouseWheel>")
        except tk.TclError:
            # Canvas has been destroyed, nothing to unbind
            pass
    
    canvas.bind('<Enter>', _bind_mousewheel)
    canvas.bind('<Leave>', _unbind_mousewheel)
    
    # Add video folders (sorted by most recent first)
    for i, (folder_name, folder_path) in enumerate(video_folders):
        self.create_result_folder_card(scrollable_frame, folder_name, folder_path, i, access_window)
    
    # Footer with statistics and actions - fixed at bottom
    footer_frame = ttk.Frame(main_container)
    footer_frame.grid(row=2, column=0, sticky="ew", pady=(15, 0))
    
    # Configure footer for proper expansion
    footer_frame.grid_columnconfigure(1, weight=1)
    
    ttk.Separator(footer_frame, orient='horizontal').grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))
    
    # Statistics on the left
    total_folders = len(video_folders)
    stats_text = f"📊 Insgesamt {total_folders} Videoanalyse{'n' if total_folders != 1 else ''} verfügbar"
    ttk.Label(footer_frame, text=stats_text, font=('Segoe UI', 10)).grid(row=1, column=0, sticky="w")
    
    # Actions on the right - always visible
    actions_frame = ttk.Frame(footer_frame)
    actions_frame.grid(row=1, column=2, sticky="e")
    
    ttk.Button(actions_frame, text="📁 Ordner öffnen", 
                command=lambda: os.startfile(results_dir)).pack(side=tk.LEFT, padx=(0, 10))
    
    ttk.Button(actions_frame, text="❌ Schließen", 
                command=access_window.destroy).pack(side=tk.LEFT)

def create_result_folder_card(self, parent, folder_name, folder_path, index, access_window):
    """Create a card for each video result folder with file access buttons"""
    # Card frame with alternating colors and better resizing behavior
    card_bg = '#f8f9fa' if index % 2 == 0 else '#ffffff'
    card_frame = tk.Frame(parent, bg=card_bg, relief=tk.RIDGE, bd=1)
    card_frame.pack(fill=tk.X, padx=5, pady=3, expand=False)  # Don't expand vertically
    
    # Main content with proper padding
    content_frame = tk.Frame(card_frame, bg=card_bg)
    content_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)
    
    # Header with video name and timestamp
    header_frame = tk.Frame(content_frame, bg=card_bg)
    header_frame.pack(fill=tk.X, pady=(0, 8))
    
    # Video icon and name
    name_frame = tk.Frame(header_frame, bg=card_bg)
    name_frame.pack(side=tk.LEFT)
    
    tk.Label(name_frame, text="🎥", font=('Segoe UI', 14), bg=card_bg).pack(side=tk.LEFT)
    tk.Label(name_frame, text=folder_name, font=('Segoe UI', 12, 'bold'), 
            bg=card_bg, fg='#2c3e50').pack(side=tk.LEFT, padx=(5, 0))
    
    # Timestamp info with better formatting
    try:
        folder_stat = os.stat(folder_path)
        modified_time = datetime.fromtimestamp(folder_stat.st_mtime)
        time_text = f"Zuletzt geändert: {modified_time.strftime('%d.%m.%Y %H:%M')}"
        # Add "NEUESTE" indicator for the first (most recent) entry
        if index == 0:
            time_text = "🆕 NEUESTE - " + time_text
        tk.Label(header_frame, text=time_text, font=('Segoe UI', 9), 
                bg=card_bg, fg='#7f8c8d').pack(side=tk.RIGHT)
    except:
        if index == 0:
            tk.Label(header_frame, text="🆕 NEUESTE", font=('Segoe UI', 9), 
                    bg=card_bg, fg='#7f8c8d').pack(side=tk.RIGHT)
    
    # Analyze available files
    available_files = self.analyze_folder_files(folder_path)
    
    # File access buttons frame
    buttons_frame = tk.Frame(content_frame, bg=card_bg)
    buttons_frame.pack(fill=tk.X, pady=(5, 0))
    
    # Row 1: Main analysis files - wrap properly on resize
    row1_frame = tk.Frame(buttons_frame, bg=card_bg)
    row1_frame.pack(fill=tk.X, pady=(0, 5))
    
    # PDF Report
    if available_files['pdf']:
        pdf_btn = tk.Button(row1_frame, text="📄 PDF öffnen", 
                            command=lambda: self.open_file_with_system(available_files['pdf'][0]),
                            bg='#e74c3c', fg='white', font=('Segoe UI', 9, 'bold'),
                            relief=tk.FLAT, padx=8, pady=4)
        pdf_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    # CSV Files
    if available_files['csv']:
        csv_btn = tk.Button(row1_frame, text="📊 CSV öffnen", 
                            command=lambda: self.open_csv_files_menu(available_files['csv'], folder_name),
                            bg='#27ae60', fg='white', font=('Segoe UI', 9, 'bold'),
                            relief=tk.FLAT, padx=8, pady=4)
        csv_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    # Marked Videos
    if available_files['videos']:
        video_btn = tk.Button(row1_frame, text="🎥 Video öffnen", 
                            command=lambda: self.open_video_files_menu(available_files['videos'], folder_name),
                            bg='#3498db', fg='white', font=('Segoe UI', 9, 'bold'),
                            relief=tk.FLAT, padx=8, pady=4)
        video_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    # Flight Path Images
    if available_files['images']:
        img_btn = tk.Button(row1_frame, text="🗺️ Bilder öffnen", 
                            command=lambda: self.open_image_files_menu(available_files['images'], folder_name),
                            bg='#f39c12', fg='white', font=('Segoe UI', 9, 'bold'),
                            relief=tk.FLAT, padx=8, pady=4)
        img_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    # Row 2: Folder operations
    row2_frame = tk.Frame(buttons_frame, bg=card_bg)
    row2_frame.pack(fill=tk.X)
    
    # Open folder
    folder_btn = tk.Button(row2_frame, text="📁 Ordner öffnen", 
                            command=lambda: self.open_file_with_system(folder_path),
                            bg='#95a5a6', fg='white', font=('Segoe UI', 9),
                            relief=tk.FLAT, padx=8, pady=3)
    folder_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    # Load results for analysis
    load_btn = tk.Button(row2_frame, text="📂 In Anwendung laden", 
                        command=lambda: self.load_folder_results_for_analysis(folder_path, folder_name, access_window),
                        bg='#9b59b6', fg='white', font=('Segoe UI', 9),
                        relief=tk.FLAT, padx=8, pady=3)
    load_btn.pack(side=tk.LEFT, padx=(0, 5))
    
    # File count info
    file_count = sum(len(files) for files in available_files.values())
    if file_count > 0:
        count_text = f"💾 {file_count} Datei{'en' if file_count != 1 else ''}"
        tk.Label(row2_frame, text=count_text, font=('Segoe UI', 9), 
                bg=card_bg, fg='#7f8c8d').pack(side=tk.RIGHT)

def analyze_folder_files(self, folder_path):
    """Analyze files in a result folder and categorize them"""
    files = {
        'pdf': [],
        'csv': [],
        'videos': [],
        'images': [],
        'other': []
    }
    
    try:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                ext = filename.lower().split('.')[-1]
                
                if ext == 'pdf':
                    files['pdf'].append(file_path)
                elif ext == 'csv':
                    files['csv'].append(file_path)
                elif ext in ['avi', 'mp4', 'mov']:
                    files['videos'].append(file_path)
                elif ext in ['png', 'jpg', 'jpeg']:
                    files['images'].append(file_path)
                else:
                    files['other'].append(file_path)
    except Exception as e:
        # Error analyzing folder - handled internally
        pass
    
    return files

def open_file_with_system(self, file_path):
    """Open a file with the system's default application"""
    try:
        if os.name == 'nt':  # Windows
            os.startfile(file_path)
        elif os.name == 'posix':  # macOS and Linux
            import subprocess
            if sys.platform == 'darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # Linux
                subprocess.run(['xdg-open', file_path])
        else:
            messagebox.showwarning("Nicht unterstützt", 
                                    f"Automatisches Öffnen auf diesem System nicht unterstützt.\n"
                                    f"Öffnen Sie die Datei manuell:\n{file_path}")
            
    except Exception as e:
        messagebox.showerror("Fehler beim Öffnen", 
                            f"Datei konnte nicht geöffnet werden:\n{file_path}\n\nFehler: {str(e)}")

def open_csv_files_menu(self, csv_files, folder_name):
    """Show menu for selecting CSV file to open"""
    if len(csv_files) == 1:
        self.open_file_with_system(csv_files[0])
        return
    
    # Multiple CSV files - show selection
    menu_window = tk.Toplevel(self.root)
    menu_window.title(f"CSV-Dateien - {folder_name}")
    menu_window.geometry("500x300")
    menu_window.resizable(False, False)
    menu_window.transient(self.root)
    menu_window.grab_set()
    
    # Center window
    menu_window.update_idletasks()
    x = (menu_window.winfo_screenwidth() - menu_window.winfo_width()) // 2
    y = (menu_window.winfo_screenheight() - menu_window.winfo_height()) // 2
    menu_window.geometry(f"+{x}+{y}")
    
    main_frame = ttk.Frame(menu_window)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
    
    ttk.Label(main_frame, text="📊 CSV-Datei auswählen", 
                font=('Segoe UI', 14, 'bold')).pack(pady=(0, 15))
    
    # File list
    for csv_file in csv_files:
        filename = os.path.basename(csv_file)
        file_size = self.get_file_size_str(csv_file)
        
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.X, pady=2)
        
        btn = ttk.Button(file_frame, text=f"📄 {filename} ({file_size})", 
                        command=lambda f=csv_file: [self.open_file_with_system(f), menu_window.destroy()])
        btn.pack(fill=tk.X)
    
    # Close button
    ttk.Button(main_frame, text="Schließen", 
                command=menu_window.destroy).pack(pady=(15, 0))

    def open_video_files_menu(self, video_files, folder_name):
        """Show menu for selecting video file to open"""
        if len(video_files) == 1:
            self.open_file_with_system(video_files[0])
            return
        
        # Multiple video files - show selection (similar to CSV menu)
        self.show_file_selection_menu(video_files, folder_name, "🎥 Video-Dateien", "🎬")

    def open_image_files_menu(self, image_files, folder_name):
        """Show menu for selecting image file to open"""
        if len(image_files) == 1:
            self.open_file_with_system(image_files[0])
            return
        
        # Multiple image files - show selection
        self.show_file_selection_menu(image_files, folder_name, "🗺️ Bilder", "🖼️")

    def show_file_selection_menu(self, files, folder_name, title, icon):
        """Generic file selection menu"""
        menu_window = tk.Toplevel(self.root)
        menu_window.title(f"{title} - {folder_name}")
        menu_window.geometry("600x400")
        menu_window.resizable(True, True)
        menu_window.transient(self.root)
        menu_window.grab_set()
        
        # Center window
        menu_window.update_idletasks()
        x = (menu_window.winfo_screenwidth() - menu_window.winfo_width()) // 2
        y = (menu_window.winfo_screenheight() - menu_window.winfo_height()) // 2
        menu_window.geometry(f"+{x}+{y}")
        
        main_frame = ttk.Frame(menu_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        ttk.Label(main_frame, text=f"{title} auswählen", 
                    font=('Segoe UI', 14, 'bold')).pack(pady=(0, 15))
        
        # Scrollable list
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        listbox = tk.Listbox(list_frame, font=('Segoe UI', 10))
        scrollbar_y = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
        scrollbar_x = ttk.Scrollbar(list_frame, orient="horizontal", command=listbox.xview)
        
        listbox.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        for file_path in files:
            filename = os.path.basename(file_path)
            file_size = self.get_file_size_str(file_path)
            listbox.insert(tk.END, f"{icon} {filename} ({file_size})")
        
        # Pack scrollbars and listbox
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        listbox.pack(side="left", fill="both", expand=True)
        
        # Double-click to open
        def on_double_click(event):
            selection = listbox.curselection()
            if selection:
                file_path = files[selection[0]]
                self.open_file_with_system(file_path)
                menu_window.destroy()
        
        listbox.bind("<Double-Button-1>", on_double_click)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        def open_selected():
            selection = listbox.curselection()
            if selection:
                file_path = files[selection[0]]
                self.open_file_with_system(file_path)
                menu_window.destroy()
            else:
                messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie eine Datei aus.")
        
        ttk.Button(button_frame, text="Öffnen", command=open_selected).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Alle öffnen", 
                    command=lambda: [self.open_file_with_system(f) for f in files]).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(button_frame, text="Schließen", 
                    command=menu_window.destroy).pack(side=tk.RIGHT)

    def get_file_size_str(self, file_path):
        """Get human-readable file size string"""
        try:
            size = os.path.getsize(file_path)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except:
            return "Unknown"

def load_folder_results_for_analysis(self, folder_path, folder_name, parent_window):
    """Load results from folder into the application for further analysis"""
    try:
        # Find CSV file with detections
        csv_files = []
        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.csv') and 'detection' in filename.lower():
                csv_files.append(os.path.join(folder_path, filename))
        
        if not csv_files:
            # Look for any CSV file
            csv_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                        if f.lower().endswith('.csv')]
        
        if not csv_files:
            messagebox.showwarning("Keine Daten", 
                                    f"Keine CSV-Dateien in '{folder_name}' gefunden.")
            return
        
        # Use the first CSV file (or let user choose if multiple)
        csv_path = csv_files[0]
        if len(csv_files) > 1:
            # Show selection dialog
            selection_window = tk.Toplevel(parent_window)
            selection_window.title("CSV-Datei auswählen")
            selection_window.geometry("400x300")
            selection_window.transient(parent_window)
            selection_window.grab_set()
            
            selected_path = tk.StringVar()
            
            ttk.Label(selection_window, text="Mehrere CSV-Dateien gefunden.\nWählen Sie die Datei für den Import:").pack(pady=10)
            
            for csv_file in csv_files:
                filename = os.path.basename(csv_file)
                ttk.Radiobutton(selection_window, text=filename, 
                                variable=selected_path, value=csv_file).pack(anchor=tk.W, padx=20)
            
            def confirm_selection():
                if selected_path.get():
                    nonlocal csv_path
                    csv_path = selected_path.get()
                    selection_window.destroy()
                else:
                    messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie eine CSV-Datei aus.")
            
            ttk.Button(selection_window, text="Auswählen", command=confirm_selection).pack(pady=10)
            ttk.Button(selection_window, text="Abbrechen", command=selection_window.destroy).pack()
            
            # Wait for selection
            selection_window.wait_window()
            
            if not selected_path.get():
                return  # User cancelled
        
        # Load the events from CSV
        events = self.load_events_from_csv(csv_path)
        if not events:
            messagebox.showwarning("Keine Ereignisse", 
                                    f"Keine gültigen Ereignisse in der CSV-Datei gefunden.")
            return
        
        # Try to find the original video file
        video_path = self.find_associated_video(folder_path, folder_name)
        
        if not video_path:
            # Ask user to select video file
            video_path = filedialog.askopenfilename(
                title=f"Video-Datei für '{folder_name}' auswählen",
                filetypes=[("Video-Dateien", "*.mp4 *.avi *.mov"), ("Alle Dateien", "*.*")]
            )
            if not video_path:
                messagebox.showinfo("Kein Video", 
                                    "Ohne Video-Datei können nur die Ereignisdaten geladen werden.")
        
        # Load video if available
        if video_path and os.path.exists(video_path):
            self.video_path = video_path
            self.load_video_file()
        
        # Load events into detector
        self.detector.events = events
        if hasattr(self.detector, 'video_path'):
            self.detector.video_path = self.video_path
        
        # Update GUI
        self.update_event_display()
        self.update_status(f"Geladen: {folder_name} | {len(events)} Ereignisse")
        
        # Enable relevant buttons
        self.btn_validate.config(state=tk.NORMAL)
        self.btn_replay_validation.config(state=tk.NORMAL)
        self.btn_export_csv.config(state=tk.NORMAL)
        self.btn_export_pdf.config(state=tk.NORMAL)
        
        # Close results window
        parent_window.destroy()
        
        messagebox.showinfo("Ergebnisse geladen", 
                            f"Erfolgreich geladen:\n"
                            f"• Video: {os.path.basename(video_path) if video_path else 'Nicht verfügbar'}\n"
                            f"• Ordner: {folder_name}\n"
                            f"• Ereignisse: {len(events)}")
                            
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Laden der Ergebnisse: {str(e)}")

def refresh_results_window(self, window, results_dir):
    """Refresh the results access window"""
    try:
        window.destroy()
        self.show_results_access_panel()
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Aktualisieren: {str(e)}")

def load_previous_video_results(self, event=None):
    """Enhanced function to load previous video results from structured folders or manual selection"""
    try:
        # Get app root directory
        app_root = os.path.dirname(os.path.dirname(__file__))
        results_dir = os.path.join(app_root, "results")
        
        # Get all video folders in results directory (if it exists)
        video_folders = []
        if os.path.exists(results_dir):
            for item in os.listdir(results_dir):
                folder_path = os.path.join(results_dir, item)
                if os.path.isdir(folder_path):
                    # Check if it has detection data files
                    csv_path = os.path.join(folder_path, "detections.csv")
                    if os.path.exists(csv_path):
                        video_folders.append((item, folder_path, csv_path))
        
        # Show selection dialog with both automatic and manual options
        self.show_video_folder_selection(video_folders, results_dir)
        
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Laden der Videoergebnisse: {str(e)}")

def show_video_folder_selection(self, video_folders, results_dir):
    """Show dialog to select a video folder and display its results"""
    # Create selection window
    selection_window = tk.Toplevel(self.root)
    selection_window.title("Video-Ergebnisse auswählen")
    selection_window.geometry("800x600")
    selection_window.transient(self.root)
    selection_window.grab_set()
    
    # Main frame
    main_frame = ttk.Frame(selection_window, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    title_label = ttk.Label(main_frame, text="Video-Ergebnisse für Validierung auswählen", 
                            font=('Arial', 12, 'bold'))
    title_label.pack(anchor=tk.W, pady=(0, 10))
    
    # Info frame with instructions
    info_frame = ttk.Frame(main_frame)
    info_frame.pack(fill=tk.X, pady=(0, 10))
    
    if video_folders:
        info_text = f"Gefunden: {len(video_folders)} Video-Ordner mit Erkennungsdaten"
    else:
        info_text = "Keine automatisch erkannten Video-Ordner gefunden"
    
    ttk.Label(info_frame, text=info_text, font=('Arial', 10)).pack(anchor=tk.W)
    ttk.Label(info_frame, text="Sie können einen Ordner aus der Liste auswählen oder manuell durchsuchen.", 
                font=('Arial', 9), foreground="#666666").pack(anchor=tk.W)
    
    # Notebook for tabs
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
    
    # Tab 1: Automatic detection
    auto_frame = ttk.Frame(notebook, padding=10)
    notebook.add(auto_frame, text=f"Erkannte Ordner ({len(video_folders)})")
    
    if video_folders:
        # Create treeview for video folders
        tree_frame = ttk.Frame(auto_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Columns: Video Name, Last Modified, Events Count
        columns = ('video', 'modified', 'events')
        tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', height=12)
        
        # Define headings
        tree.heading('#0', text='', anchor=tk.W)
        tree.heading('video', text='Video-Name', anchor=tk.W)
        tree.heading('modified', text='Zuletzt geändert', anchor=tk.W)
        tree.heading('events', text='Ereignisse', anchor=tk.CENTER)
        
        # Configure column widths
        tree.column('#0', width=30, minwidth=30)
        tree.column('video', width=350, minwidth=250)
        tree.column('modified', width=200, minwidth=150)
        tree.column('events', width=100, minwidth=80)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate tree with video folders
        for i, (folder_name, folder_path, csv_path) in enumerate(video_folders):
            try:
                # Get modification time
                mod_time = os.path.getmtime(csv_path)
                mod_time_str = datetime.fromtimestamp(mod_time).strftime("%d.%m.%Y %H:%M")
                
                # Count events in CSV
                event_count = self.count_events_in_csv(csv_path)
                
                tree.insert('', 'end', iid=i, text='📁', values=(folder_name, mod_time_str, event_count))
            except Exception as e:
                tree.insert('', 'end', iid=i, text='📁', values=(folder_name, "Unbekannt", "Fehler"))
        
        # Auto tab button frame
        auto_button_frame = ttk.Frame(auto_frame)
        auto_button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def load_selected_auto():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie ein Video aus.")
                return
            
            selected_index = int(selection[0])
            folder_name, folder_path, csv_path = video_folders[selected_index]
            
            # Load the video results
            self.load_video_results_from_folder(folder_path, folder_name)
            selection_window.destroy()
        
        # Double-click to load
        tree.bind("<Double-1>", lambda e: load_selected_auto())
        
        ttk.Button(auto_button_frame, text="✓ Ausgewählten Ordner laden", 
                    command=load_selected_auto, style='Accent.TButton').pack(side=tk.LEFT, padx=(0, 5))
        
    else:
        # No automatic folders found
        no_results_frame = ttk.Frame(auto_frame)
        no_results_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(no_results_frame, text="Keine Video-Ordner mit Erkennungsdaten gefunden", 
                    font=('Arial', 11), foreground="#888888").pack(expand=True)
        ttk.Label(no_results_frame, text="Verwenden Sie den Tab 'Manuell durchsuchen' um einen Ordner auszuwählen.", 
                    font=('Arial', 9), foreground="#666666").pack()
    
    # Tab 2: Manual browsing
    manual_frame = ttk.Frame(notebook, padding=10)
    notebook.add(manual_frame, text="Manuell durchsuchen")
    
    # Manual selection frame
    manual_content = ttk.Frame(manual_frame)
    manual_content.pack(fill=tk.BOTH, expand=True)
    
    # Instructions
    instructions = ttk.Label(manual_content, 
                            text="Wählen Sie einen beliebigen Ordner mit Erkennungsdaten:", 
                            font=('Arial', 11, 'bold'))
    instructions.pack(anchor=tk.W, pady=(0, 10))
    
    ttk.Label(manual_content, 
                text="• Der Ordner sollte eine 'detections.csv' Datei enthalten\n"
                    "• Alternativ andere CSV-Dateien mit Ereignisdaten\n"
                    "• Kann auch außerhalb des 'results' Ordners liegen", 
                font=('Arial', 9), foreground="#666666").pack(anchor=tk.W, pady=(0, 20))
    
    # Selected folder display
    self.selected_manual_folder = tk.StringVar(value="Kein Ordner ausgewählt")
    folder_display_frame = ttk.Frame(manual_content)
    folder_display_frame.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Label(folder_display_frame, text="Ausgewählter Ordner:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
    folder_label = ttk.Label(folder_display_frame, textvariable=self.selected_manual_folder, 
                            font=('Arial', 9), foreground="#333333", background="#f0f0f0", 
                            relief=tk.SUNKEN, padding=5)
    folder_label.pack(fill=tk.X, pady=(2, 0))
    
    # Manual buttons
    manual_button_frame = ttk.Frame(manual_content)
    manual_button_frame.pack(fill=tk.X, pady=(10, 0))
    
    def browse_folder():
        try:
            folder_path = filedialog.askdirectory(
                title="Ordner mit Erkennungsdaten auswählen",
                initialdir=results_dir if os.path.exists(results_dir) else os.path.expanduser("~")
            )
            
            if folder_path:
                self.selected_manual_folder.set(folder_path)
                # Check what files are available
                self.check_manual_folder_contents(folder_path, manual_content)
        except KeyboardInterrupt:
            # Folder selection cancelled - handled internally
            pass
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Öffnen der Ordnerauswahl: {str(e)}")
    
    def load_manual_folder():
        folder_path = self.selected_manual_folder.get()
        if folder_path == "Kein Ordner ausgewählt" or not os.path.exists(folder_path):
            messagebox.showwarning("Kein Ordner", "Bitte wählen Sie zuerst einen Ordner aus.")
            return
        
        # Try to load from the manual folder
        self.load_manual_folder_results(folder_path)
        selection_window.destroy()
    
    ttk.Button(manual_button_frame, text="📁 Ordner durchsuchen...", 
                command=browse_folder).pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(manual_button_frame, text="✓ Ordner laden", 
                command=load_manual_folder, style='Accent.TButton').pack(side=tk.LEFT)
    
    # Global button frame
    global_button_frame = ttk.Frame(main_frame)
    global_button_frame.pack(fill=tk.X, pady=(10, 0))
    
    ttk.Button(global_button_frame, text="Abbrechen", 
                command=selection_window.destroy).pack(side=tk.RIGHT)

def count_events_in_csv(self, csv_path):
    """Count the number of events in a CSV file"""
    try:
        import csv
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Skip metadata lines starting with #
            event_count = 0
            header_found = False
            for row in reader:
                if not row or (row[0].startswith('#')):
                    continue
                if not header_found:
                    header_found = True
                    continue
                event_count += 1
            return event_count
    except Exception:
        return "?"

def load_video_results_from_folder(self, folder_path, folder_name):
    """Load and display results from a specific video folder"""
    try:
        csv_path = os.path.join(folder_path, "detections.csv")
        
        # Load events from CSV
        events = self.load_events_from_csv(csv_path)
        
        if not events:
            messagebox.showinfo("Keine Ereignisse", f"Keine Ereignisse in {folder_name} gefunden.")
            return
        
        # Find the original video file (look for common video extensions)
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        original_video_path = None
        
        # First, check if we can find the original video based on folder name
        for ext in video_extensions:
            potential_path = os.path.join(os.path.dirname(folder_path), f"{folder_name}{ext}")
            if os.path.exists(potential_path):
                original_video_path = potential_path
                break
        
        # If not found, ask user to select the video file
        if not original_video_path:
            original_video_path = filedialog.askopenfilename(
                title=f"Video-Datei für '{folder_name}' auswählen",
                filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv"), ("All files", "*.*")]
            )
            if not original_video_path:
                return
        
        # Load the video and set up for validation
        self.video_path = original_video_path
        self.cap = cv2.VideoCapture(self.video_path)
        
        if not self.cap.isOpened():
            messagebox.showerror("Fehler", "Video-Datei konnte nicht geöffnet werden.")
            return
        
        # Set up video information
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Set loaded events to detector
        self.detector.events = events
        self.detector.video_path = self.video_path
        
        # Update status
        self.update_status(f"Geladen: {folder_name} | {len(events)} Ereignisse")
        
        # Enable validation and other buttons
        self.btn_validate.config(state=tk.NORMAL)
        self.btn_replay_validation.config(state=tk.NORMAL)
        self.btn_export_csv.config(state=tk.NORMAL)
        self.btn_export_pdf.config(state=tk.NORMAL)
        
        # Update event display
        self.update_event_display()
        
        # Show results window
        self.show_loaded_events_window(events, folder_name)
        
        messagebox.showinfo("Ergebnisse geladen", 
                            f"Video: {os.path.basename(original_video_path)}\n"
                            f"Ordner: {folder_name}\n"
                            f"Ereignisse: {len(events)}\n\n"
                            f"Sie können jetzt die Ereignisse validieren oder weitere Analysen durchführen.")
    
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Laden der Ergebnisse: {str(e)}")

def load_events_from_csv(self, csv_path):
    """Load events from a CSV file"""
    events = []
    try:
        import csv
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = None
            
            for row in reader:
                # Skip empty rows and metadata
                if not row or row[0].startswith('#'):
                    continue
                
                # Find header row
                if header is None:
                    header = [col.lower().strip() for col in row]
                    continue
                
                # Parse event data
                event = {}
                for i, value in enumerate(row):
                    if i < len(header):
                        col_name = header[i]
                        
                        # Map CSV columns to event fields
                        if 'einflug' in col_name or 'entry' in col_name:
                            event['entry'] = self.parse_time_to_seconds(value)
                            event['start_frame'] = event['entry'] * self.fps if hasattr(self, 'fps') and self.fps > 0 else 0
                        elif 'ausflug' in col_name or 'exit' in col_name:
                            event['exit'] = self.parse_time_to_seconds(value)
                            event['end_frame'] = event['exit'] * self.fps if hasattr(self, 'fps') and self.fps > 0 else 0
                        elif 'dauer' in col_name or 'duration' in col_name:
                            try:
                                if 's' in value:
                                    event['duration'] = float(value.replace('s', '').strip())
                                else:
                                    event['duration'] = float(value)
                            except ValueError:
                                event['duration'] = 0
                
                # Calculate duration if not provided
                if 'duration' not in event and 'entry' in event and 'exit' in event:
                    event['duration'] = event['exit'] - event['entry']
                
                if 'entry' in event and 'exit' in event:
                    events.append(event)
    
    except Exception as e:
        # Error loading events from CSV - handled internally
        pass
    
    return events

def parse_time_to_seconds(self, time_str):
    """Parse time string (MM:SS or seconds) to seconds"""
    try:
        if ':' in time_str:
            # Format MM:SS
            parts = time_str.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes * 60 + seconds
            elif len(parts) == 3:
                # Format HH:MM:SS
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        else:
            # Assume it's already in seconds
            return float(time_str)
    except ValueError:
        return 0

def show_loaded_events_window(self, events, folder_name):
    """Show a detailed window with loaded events"""
    # Create events display window
    events_window = tk.Toplevel(self.root)
    events_window.title(f"Ereignisse - {folder_name}")
    events_window.geometry("800x600")
    events_window.transient(self.root)
    
    # Main frame
    main_frame = ttk.Frame(events_window, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    title_label = ttk.Label(main_frame, text=f"Geladene Ereignisse aus '{folder_name}'", 
                            font=('Arial', 14, 'bold'))
    title_label.pack(anchor=tk.W, pady=(0, 10))
    
    # Summary info
    info_frame = ttk.Frame(main_frame)
    info_frame.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Label(info_frame, text=f"Anzahl Ereignisse: {len(events)}", 
                font=('Arial', 10)).pack(anchor=tk.W)
    
    if events:
        total_duration = sum(event.get('duration', 0) for event in events)
        ttk.Label(info_frame, text=f"Gesamtdauer: {total_duration:.1f} Sekunden", 
                    font=('Arial', 10)).pack(anchor=tk.W)
    
    # Events table
    tree_frame = ttk.Frame(main_frame)
    tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    columns = ('nr', 'einflug', 'ausflug', 'dauer')
    tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)
    
    # Define headings
    tree.heading('nr', text='Nr.', anchor=tk.CENTER)
    tree.heading('einflug', text='Einflug', anchor=tk.CENTER)
    tree.heading('ausflug', text='Ausflug', anchor=tk.CENTER)
    tree.heading('dauer', text='Dauer', anchor=tk.CENTER)
    
    # Configure column widths
    tree.column('nr', width=60, minwidth=50)
    tree.column('einflug', width=150, minwidth=100)
    tree.column('ausflug', width=150, minwidth=100)
    tree.column('dauer', width=120, minwidth=100)
    
    # Add scrollbar
    scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Populate tree with events
    for i, event in enumerate(events, 1):
        # Safe handling of entry/exit times
        entry_time = event.get('entry') or event.get('einflugzeit')
        exit_time = event.get('exit') or event.get('ausflugzeit')
        duration = event.get('duration') or event.get('dauer')
        
        einflug = self.safe_format_time(entry_time)
        ausflug = self.safe_format_time(exit_time)
        
        if duration is not None and duration > 0:
            dauer = f"{duration:.1f}s"
        else:
            dauer = "unbekannt"
        
        # Add visual indicator for incomplete events
        if event.get('incomplete', False):
            einflug += " ⚠"
            ausflug += " ⚠"
            dauer += " ⚠"
        
        tree.insert('', 'end', values=(i, einflug, ausflug, dauer))
    
    # Button frame
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=(10, 0))
    
    ttk.Button(button_frame, text="Ereignisse validieren", 
                command=lambda: [events_window.destroy(), self.validate_events_gui()]).pack(side=tk.LEFT, padx=(0, 5))
    
    ttk.Button(button_frame, text="Replay-Validierung", 
                command=lambda: [events_window.destroy(), self.replay_validation()]).pack(side=tk.LEFT, padx=(0, 5))
    
    ttk.Button(button_frame, text="Schließen", 
                command=events_window.destroy).pack(side=tk.RIGHT)

def format_time(self, seconds):
    """Format seconds to MM:SS format"""
    if seconds is None:
        return "unbekannt"
    try:
        seconds = float(seconds)
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    except (ValueError, TypeError):
        return "unbekannt"

def safe_format_time(self, seconds):
    """Safely format seconds to MM:SS format with None handling"""
    if seconds is None:
        return "unbekannt"
    try:
        seconds = float(seconds)
        if seconds < 0:
            return "unbekannt"
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    except (ValueError, TypeError):
        return "unbekannt"

def check_manual_folder_contents(self, folder_path, parent_frame):
    """Check and display contents of manually selected folder"""
    try:
        # Create or update info display
        if hasattr(self, 'folder_info_frame'):
            self.folder_info_frame.destroy()
        
        self.folder_info_frame = ttk.LabelFrame(parent_frame, text="Ordner-Analyse", padding=10)
        self.folder_info_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Look for CSV files
        csv_files = []
        for file in os.listdir(folder_path):
            if file.lower().endswith('.csv'):
                csv_files.append(file)
        
        if csv_files:
            ttk.Label(self.folder_info_frame, text=f"✓ {len(csv_files)} CSV-Datei(en) gefunden:", 
                        font=('Arial', 9, 'bold'), foreground="#006600").pack(anchor=tk.W)
            
            for csv_file in csv_files[:5]:  # Show first 5 files
                csv_path = os.path.join(folder_path, csv_file)
                try:
                    event_count = self.count_events_in_csv(csv_path)
                    ttk.Label(self.folder_info_frame, text=f"  • {csv_file} ({event_count} Ereignisse)", 
                                font=('Arial', 8)).pack(anchor=tk.W)
                except:
                    ttk.Label(self.folder_info_frame, text=f"  • {csv_file} (Format unbekannt)", 
                                font=('Arial', 8)).pack(anchor=tk.W)
            
            if len(csv_files) > 5:
                ttk.Label(self.folder_info_frame, text=f"  ... und {len(csv_files)-5} weitere", 
                            font=('Arial', 8), foreground="#666666").pack(anchor=tk.W)
        else:
            ttk.Label(self.folder_info_frame, text="⚠ Keine CSV-Dateien gefunden", 
                        font=('Arial', 9, 'bold'), foreground="#CC6600").pack(anchor=tk.W)
            ttk.Label(self.folder_info_frame, text="Dieser Ordner scheint keine Erkennungsdaten zu enthalten.", 
                        font=('Arial', 8), foreground="#666666").pack(anchor=tk.W)
            
    except Exception as e:
        if hasattr(self, 'folder_info_frame'):
            self.folder_info_frame.destroy()
        
        self.folder_info_frame = ttk.LabelFrame(parent_frame, text="Ordner-Analyse", padding=10)
        self.folder_info_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(self.folder_info_frame, text="✗ Fehler beim Analysieren des Ordners", 
                    font=('Arial', 9, 'bold'), foreground="#CC0000").pack(anchor=tk.W)
        ttk.Label(self.folder_info_frame, text=f"Fehler: {str(e)}", 
                    font=('Arial', 8), foreground="#666666").pack(anchor=tk.W)

def load_manual_folder_results(self, folder_path):
    """Load results from a manually selected folder"""
    try:
        # Look for CSV files with detection data
        csv_files = []
        for file in os.listdir(folder_path):
            if file.lower().endswith('.csv'):
                csv_path = os.path.join(folder_path, file)
                # Try to validate if it contains events
                if self.validate_csv_file(csv_path):
                    csv_files.append((file, csv_path))
        
        if not csv_files:
            messagebox.showwarning("Keine Erkennungsdaten", 
                                    "Keine Erkennungsdaten in diesem Ordner gefunden.\n\n"
                                    "Der Ordner sollte mindestens eine CSV-Datei mit "
                                    "Ereignisdaten (Einflug, Ausflug, Dauer) enthalten.")
            return
        
        # If multiple CSV files, let user choose or use the first valid one
        if len(csv_files) == 1:
            csv_file, csv_path = csv_files[0]
        else:
            # Show selection dialog for multiple CSV files
            csv_file, csv_path = self.select_csv_file(csv_files)
            if not csv_path:
                return
        
        # Load events from selected CSV
        events = self.load_events_from_csv(csv_path)
        
        if not events:
            messagebox.showwarning("Keine Ereignisse", 
                                    f"Keine gültigen Ereignisse in '{csv_file}' gefunden.\n\n"
                                    "Die CSV-Datei sollte Spalten für Einflug, Ausflug und "
                                    "optional Dauer enthalten.")
            return
        
        # Try to find associated video file
        folder_name = os.path.basename(folder_path)
        video_path = self.find_associated_video(folder_path, folder_name)
        
        if not video_path:
            video_path = filedialog.askopenfilename(
                title=f"Video-Datei für '{folder_name}' auswählen",
                filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv"), ("All files", "*.*")]
            )
            if not video_path:
                return
        
        # Load the video and set up for validation
        self.video_path = video_path
        self.cap = cv2.VideoCapture(self.video_path)
        
        if not self.cap.isOpened():
            messagebox.showerror("Fehler", "Video-Datei konnte nicht geöffnet werden.")
            return
        
        # Set up video information
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Set loaded events to detector
        self.detector.events = events
        self.detector.video_path = self.video_path
        
        # Update status
        self.update_status(f"Manuell geladen: {folder_name} | {len(events)} Ereignisse")
        
        # Enable validation and other buttons
        self.btn_validate.config(state=tk.NORMAL)
        self.btn_replay_validation.config(state=tk.NORMAL)
        self.btn_export_csv.config(state=tk.NORMAL)
        self.btn_export_pdf.config(state=tk.NORMAL)
        
        # Update event display
        self.update_event_display()
        
        # Show results window
        self.show_loaded_events_window(events, folder_name)
        
        messagebox.showinfo("Ergebnisse geladen", 
                            f"Ordner: {folder_name}\n"
                            f"Video: {os.path.basename(video_path)}\n"
                            f"CSV-Datei: {csv_file}\n"
                            f"Ereignisse: {len(events)}\n\n"
                            f"Sie können jetzt die Ereignisse validieren oder weitere Analysen durchführen.")
                            
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Laden der manuellen Ergebnisse: {str(e)}")

def validate_csv_file(self, csv_path):
    """Check if a CSV file contains valid event data"""
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = None
            
            for row in reader:
                if not row or row[0].startswith('#'):
                    continue
                
                if header is None:
                    header = [col.lower().strip() for col in row]
                    # Check for required columns
                    has_entry = any('einflug' in col or 'entry' in col for col in header)
                    has_exit = any('ausflug' in col or 'exit' in col for col in header)
                    return has_entry and has_exit
                else:
                    break
    except Exception:
        pass
    return False

def select_csv_file(self, csv_files):
    """Show dialog to select from multiple CSV files"""
    # Create simple selection dialog
    selection_window = tk.Toplevel(self.root)
    selection_window.title("CSV-Datei auswählen")
    selection_window.geometry("500x300")
    selection_window.transient(self.root)
    selection_window.grab_set()
    
    main_frame = ttk.Frame(selection_window, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(main_frame, text="Mehrere CSV-Dateien gefunden. Wählen Sie eine aus:", 
                font=('Arial', 11, 'bold')).pack(anchor=tk.W, pady=(0, 10))
    
    # Listbox for CSV files
    listbox_frame = ttk.Frame(main_frame)
    listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    listbox = tk.Listbox(listbox_frame, font=('Arial', 9))
    scrollbar_list = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
    listbox.configure(yscrollcommand=scrollbar_list.set)
    
    for i, (csv_file, csv_path) in enumerate(csv_files):
        event_count = self.count_events_in_csv(csv_path)
        listbox.insert(tk.END, f"{csv_file} ({event_count} Ereignisse)")
    
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar_list.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Select first item by default
    if csv_files:
        listbox.selection_set(0)
    
    # Result variable
    selected_csv = [None]
    
    def select_csv():
        selection = listbox.curselection()
        if selection:
            selected_csv[0] = csv_files[selection[0]]
        selection_window.destroy()
    
    # Buttons
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X)
    
    ttk.Button(button_frame, text="Auswählen", command=select_csv).pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(button_frame, text="Abbrechen", command=selection_window.destroy).pack(side=tk.LEFT)
    
    # Wait for window to close
    selection_window.wait_window()
    
    return selected_csv[0] if selected_csv[0] else (None, None)

def find_associated_video(self, folder_path, folder_name):
    """Try to find the video file associated with a results folder"""
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
    
    # Check parent directory for video with same name as folder
    parent_dir = os.path.dirname(folder_path)
    for ext in video_extensions:
        video_path = os.path.join(parent_dir, f"{folder_name}{ext}")
        if os.path.exists(video_path):
            return video_path
    
    # Check folder itself for video files
    try:
        for file in os.listdir(folder_path):
            if any(file.lower().endswith(ext) for ext in video_extensions):
                return os.path.join(folder_path, file)
    except:
        pass
    
    # Check if folder name suggests a video file pattern
    for ext in video_extensions:
        # Try common patterns
        potential_paths = [
            os.path.join(parent_dir, f"{folder_name}{ext}"),
            os.path.join(os.path.dirname(parent_dir), f"{folder_name}{ext}"),
        ]
        
        for path in potential_paths:
            if os.path.exists(path):
                return path
    
    return None
