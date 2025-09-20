

import os
import tkinter as tk
from tkinter import messagebox, ttk
import cv2
from datetime import datetime

# Fix matplotlib font issues on Windows





def check_existing_analysis(self, video_path):
    """Check if a video has been analyzed before and return analysis information"""
    try:
        from utils.result_organizer import create_video_result_structure
        
        # Get the expected result folder for this video (checking only, no creation)
        structure = create_video_result_structure(video_path, user_choice=None)
        result_folder = structure["base"]
        
        analysis_info = {
            "exists": False,
            "folder_path": result_folder,
            "video_name": structure["video_name"],
            "files": {},
            "analysis_count": 0,
            "last_analysis": None
        }
        
        if not os.path.exists(result_folder):
            return analysis_info
        
        # Check for analysis files
        
        # Look for CSV files
        csv_files = []
        for file in os.listdir(result_folder):
            if file.lower().endswith('.csv'):
                csv_files.append(file)
                
        # Look for PDF reports
        pdf_files = []
        for file in os.listdir(result_folder):
            if file.lower().endswith('.pdf'):
                pdf_files.append(file)
                
        # Look for marked videos
        video_files = []
        for file in os.listdir(result_folder):
            if file.lower().startswith('marked_video') and file.lower().endswith('.avi'):
                video_files.append(file)
        
        if csv_files or pdf_files or video_files:
            analysis_info["exists"] = True
            analysis_info["files"]["csv"] = csv_files
            analysis_info["files"]["pdf"] = pdf_files
            analysis_info["files"]["videos"] = video_files
            analysis_info["analysis_count"] = len(set(csv_files + pdf_files + video_files))
            
            # Get last modification time
            try:
                all_files = csv_files + pdf_files + video_files
                if all_files:
                    latest_file = max(all_files, key=lambda f: os.path.getmtime(os.path.join(result_folder, f)))
                    analysis_info["last_analysis"] = datetime.fromtimestamp(
                        os.path.getmtime(os.path.join(result_folder, latest_file))
                    ).strftime("%d.%m.%Y %H:%M")
            except:
                analysis_info["last_analysis"] = "Unbekannt"
        
        return analysis_info
        
    except Exception as e:
        print(f"[ERROR] Failed to check existing analysis: {e}")
        return {"exists": False, "folder_path": None, "video_name": None, "files": {}, "analysis_count": 0, "last_analysis": None}

def show_analysis_history_dialog(self, analysis_info):
    """Show dialog with existing analysis information and options"""
    dialog = tk.Toplevel(self.root)
    dialog.title("Vorherige Analyse gefunden")
    
    # Make dialog larger to show all content including bottom buttons
    dialog.geometry("750x650")
    dialog.minsize(650, 550)  # Set minimum size
    dialog.resizable(True, True)  # Allow resizing for different screen sizes
    dialog.transient(self.root)
    dialog.grab_set()
    
    # Center the dialog
    dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
    
    # Create a main container with scrollable capability
    canvas = tk.Canvas(dialog)
    scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    def _on_mousewheel(event):
        try:
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except tk.TclError:
            pass

    def _bind_to_mousewheel(event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def _unbind_from_mousewheel(event):
        try:
            canvas.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass
    
    canvas.bind('<Enter>', _bind_to_mousewheel)
    canvas.bind('<Leave>', _unbind_from_mousewheel)
    
    # Pack scrolling elements
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    main_frame = ttk.Frame(scrollable_frame, padding=15)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    title_label = ttk.Label(main_frame, text="Video bereits analysiert!", 
                            font=('Arial', 14, 'bold'), foreground="#2B5D8A")
    title_label.pack(anchor=tk.W, pady=(0, 15))
    
    # Video info
    info_frame = ttk.LabelFrame(main_frame, text="Video-Information", padding=10)
    info_frame.pack(fill=tk.X, pady=(0, 15))
    
    ttk.Label(info_frame, text=f"Video: {analysis_info['video_name']}", 
                font=('Arial', 10, 'bold')).pack(anchor=tk.W)
    ttk.Label(info_frame, text=f"Letzte Analyse: {analysis_info['last_analysis']}", 
                font=('Arial', 9)).pack(anchor=tk.W)
    ttk.Label(info_frame, text=f"Ordner: {analysis_info['folder_path']}", 
                font=('Arial', 9), foreground="#666666").pack(anchor=tk.W)
    
    # Files found
    files_frame = ttk.LabelFrame(main_frame, text="Gefundene Analysedateien", padding=10)
    files_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
    
    # Create treeview for files
    tree_frame = ttk.Frame(files_frame)
    tree_frame.pack(fill=tk.BOTH, expand=True)
    
    tree = ttk.Treeview(tree_frame, columns=('type', 'date'), show='tree headings', height=8)
    tree.heading('#0', text='Datei', anchor=tk.W)
    tree.heading('type', text='Typ', anchor=tk.W)
    tree.heading('date', text='Datum', anchor=tk.W)
    
    tree.column('#0', width=300, minwidth=200)
    tree.column('type', width=100, minwidth=80)
    tree.column('date', width=150, minwidth=120)
    
    scrollbar_tree = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar_tree.set)
    
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar_tree.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Populate tree with files
    file_types = {
        'csv': ('📊 CSV-Daten', '#4CAF50'),
        'pdf': ('📄 PDF-Bericht', '#F44336'),
        'videos': ('🎥 Markiertes Video', '#2196F3')
    }
    
    for file_type, files in analysis_info['files'].items():
        if files:
            type_info = file_types.get(file_type, ('📁 Datei', '#666666'))
            for file in files:
                try:
                    file_path = os.path.join(analysis_info['folder_path'], file)
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%d.%m.%Y %H:%M")
                    tree.insert('', 'end', text=file, values=(type_info[0], mod_time), 
                                tags=(file_type,))
                except:
                    tree.insert('', 'end', text=file, values=(type_info[0], "Unbekannt"), 
                                tags=(file_type,))
                    
    # Configure tree colors
    tree.tag_configure('csv', foreground='#2E7D32')
    tree.tag_configure('pdf', foreground='#C62828')
    tree.tag_configure('videos', foreground='#1565C0')
    
    # Options frame
    options_frame = ttk.LabelFrame(main_frame, text="Was möchten Sie tun?", padding=10)
    options_frame.pack(fill=tk.X, pady=(0, 15))
    
    result = [None]  # Mutable container for result
    
    def load_existing():
        result[0] = "load_existing"
        dialog.destroy()
        
    def continue_new():
        result[0] = "continue_new" 
        dialog.destroy()
        
    def cancel():
        result[0] = "cancel"
        dialog.destroy()
    
    # Buttons with descriptions
    btn_frame1 = ttk.Frame(options_frame)
    btn_frame1.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Button(btn_frame1, text="📂 Vorherige Analyse laden", 
                command=load_existing, style='Accent.TButton').pack(side=tk.LEFT, padx=(0, 10))
    ttk.Label(btn_frame1, text="Lädt die bestehenden Ergebnisse für weitere Validierung", 
                font=('Arial', 9), foreground="#666666").pack(side=tk.LEFT)
    
    btn_frame2 = ttk.Frame(options_frame)
    btn_frame2.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Button(btn_frame2, text="🔄 Neue Analyse starten", 
                command=continue_new).pack(side=tk.LEFT, padx=(0, 10))
    ttk.Label(btn_frame2, text="Startet eine neue Analyse (erstellt zusätzliche Dateien)", 
                font=('Arial', 9), foreground="#666666").pack(side=tk.LEFT)
    
    btn_frame3 = ttk.Frame(options_frame)
    btn_frame3.pack(fill=tk.X)
    
    ttk.Button(btn_frame3, text="❌ Abbrechen", 
                command=cancel).pack(side=tk.LEFT, padx=(0, 10))
    ttk.Label(btn_frame3, text="Schließt den Dialog und wählt ein anderes Video", 
                font=('Arial', 9), foreground="#666666").pack(side=tk.LEFT)
    
    # Wait for user choice
    dialog.wait_window()
    
    return result[0]

def show_folder_choice_dialog(self, video_name, existing_folder_info):
    """Show dialog for choosing how to handle existing result folder"""
    dialog = tk.Toplevel(self.root)
    dialog.title("Ordner-Optionen")
    dialog.transient(self.root)
    dialog.grab_set()
    
    # Responsive sizing based on screen dimensions
    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    dialog_width = min(750, int(screen_width * 0.85))
    dialog_height = min(650, int(screen_height * 0.85))
    dialog.geometry(f"{dialog_width}x{dialog_height}")
    dialog.minsize(650, 550)
    dialog.resizable(True, True)
    
    # Center the dialog
    x = (screen_width - dialog_width) // 2
    y = (screen_height - dialog_height) // 2
    dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    # Configure grid layout for responsiveness
    dialog.grid_rowconfigure(0, weight=1)  # Main content area
    dialog.grid_columnconfigure(0, weight=1)
    
    # Create main container frame
    main_container = ttk.Frame(dialog)
    main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    main_container.grid_rowconfigure(0, weight=1)  # Content area
    main_container.grid_columnconfigure(0, weight=1)
    
    # Create scrollable content area
    canvas = tk.Canvas(main_container)
    scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    def _on_mousewheel(event):
        try:
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except tk.TclError:
            pass
    
    def _bind_to_mousewheel(event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def _unbind_from_mousewheel(event):
        try:
            canvas.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass
    
    canvas.bind('<Enter>', _bind_to_mousewheel)
    canvas.bind('<Leave>', _unbind_from_mousewheel)
    
    # Grid layout for scrollable area
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    
    main_frame = ttk.Frame(scrollable_frame, padding=15)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    title_label = ttk.Label(main_frame, text="Ordner bereits vorhanden!", 
                            font=('Arial', 14, 'bold'), foreground="#2B5D8A")
    title_label.pack(anchor=tk.W, pady=(0, 15))
    
    # Folder info
    info_frame = ttk.LabelFrame(main_frame, text="Bestehender Ordner", padding=10)
    info_frame.pack(fill=tk.X, pady=(0, 15))
    
    ttk.Label(info_frame, text=f"Video: {video_name}", 
                font=('Arial', 10, 'bold')).pack(anchor=tk.W)
    ttk.Label(info_frame, text=f"Ordner: {existing_folder_info['folder_path']}", 
                font=('Arial', 9)).pack(anchor=tk.W, pady=(5, 0))
    ttk.Label(info_frame, text=f"Dateien: {existing_folder_info['total_files']} gesamt, {existing_folder_info['analysis_count']} Analysedateien", 
                font=('Arial', 9)).pack(anchor=tk.W, pady=(2, 0))
    
    if existing_folder_info.get('latest_modification'):
        ttk.Label(info_frame, text=f"Letzte Änderung: {existing_folder_info['latest_modification']}", 
                    font=('Arial', 9)).pack(anchor=tk.W, pady=(2, 0))
    
    # File details
    if existing_folder_info['files']:
        files_frame = ttk.LabelFrame(main_frame, text="Vorhandene Dateien", padding=10)
        files_frame.pack(fill=tk.X, pady=(0, 15))
        
        files_text = tk.Text(files_frame, height=6, wrap=tk.WORD, font=('Courier', 9))
        files_scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=files_text.yview)
        files_text.configure(yscrollcommand=files_scrollbar.set)
        
        files_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        files_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add file information
        for file_type, files in existing_folder_info['files'].items():
            if files:
                files_text.insert(tk.END, f"{file_type.upper()}: {', '.join(files)}\n")
        
        files_text.config(state=tk.DISABLED)
    
    # Store user choice
    result = [None]
    
    def choose_reuse():
        result[0] = "reuse"
        dialog.destroy()
        
    def choose_new_version():
        result[0] = "new_version"
        dialog.destroy()
        
    def cancel():
        result[0] = "cancel"
        dialog.destroy()
    
    # Options frame (fixed at bottom)
    options_frame = ttk.LabelFrame(main_frame, text="Optionen", padding=10)
    options_frame.pack(fill=tk.X, pady=(15, 0), side=tk.BOTTOM)
    
    # Buttons with descriptions
    btn_frame1 = ttk.Frame(options_frame)
    btn_frame1.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Button(btn_frame1, text="🔄 Ordner wiederverwenden", 
                command=choose_reuse, style='Accent.TButton').pack(side=tk.LEFT, padx=(0, 10))
    ttk.Label(btn_frame1, text="Neue Dateien werden zum bestehenden Ordner hinzugefügt", 
                font=('Arial', 9), foreground="#666666").pack(side=tk.LEFT)
    
    btn_frame2 = ttk.Frame(options_frame)
    btn_frame2.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Button(btn_frame2, text="📁 Neue Version erstellen", 
                command=choose_new_version).pack(side=tk.LEFT, padx=(0, 10))
    ttk.Label(btn_frame2, text="Erstellt einen neuen Ordner mit Versionsnummer (z.B. video_1)", 
                font=('Arial', 9), foreground="#666666").pack(side=tk.LEFT)
    
    btn_frame3 = ttk.Frame(options_frame)
    btn_frame3.pack(fill=tk.X)
    
    ttk.Button(btn_frame3, text="❌ Abbrechen", 
                command=cancel).pack(side=tk.LEFT, padx=(0, 10))
    ttk.Label(btn_frame3, text="Schließt den Dialog und wählt ein anderes Video", 
                font=('Arial', 9), foreground="#666666").pack(side=tk.LEFT)
    
    # Wait for user choice
    dialog.wait_window()
    
    return result[0]





def show_video_info_dialog(self, video_path):
    """Show single dialog for all video information input"""
    dialog = tk.Toplevel(self.root)
    dialog.title("Video-Informationen für PDF-Bericht")
    dialog.transient(self.root)
    dialog.grab_set()
    
    # Responsive sizing based on screen dimensions
    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    dialog_width = min(750, int(screen_width * 0.85))
    dialog_height = min(650, int(screen_height * 0.85))
    dialog.geometry(f"{dialog_width}x{dialog_height}")
    dialog.minsize(650, 550)
    dialog.resizable(True, True)
    
    # Center the dialog
    x = (screen_width - dialog_width) // 2
    y = (screen_height - dialog_height) // 2
    dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    # Configure grid layout for responsiveness
    dialog.grid_rowconfigure(0, weight=1)  # Main content area
    dialog.grid_rowconfigure(1, weight=0)  # Button area (fixed)
    dialog.grid_columnconfigure(0, weight=1)
    
    # Create main container frame
    main_container = ttk.Frame(dialog)
    main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))
    main_container.grid_rowconfigure(0, weight=1)
    main_container.grid_columnconfigure(0, weight=1)
    
    # Create scrollable content area
    canvas = tk.Canvas(main_container)
    scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    def _on_mousewheel(event):
        try:
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except tk.TclError:
            pass

    def _bind_to_mousewheel(event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def _unbind_from_mousewheel(event):
        try:
            canvas.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass
    
    canvas.bind('<Enter>', _bind_to_mousewheel)
    canvas.bind('<Leave>', _unbind_from_mousewheel)
    
    # Grid layout for scrollable area
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    
    main_frame = ttk.Frame(scrollable_frame, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    title_label = ttk.Label(main_frame, text="PDF-Bericht Informationen", 
                            font=('Arial', 14, 'bold'), foreground="#2B5D8A")
    title_label.pack(anchor=tk.W, pady=(0, 15))
    
    # Parse date and time from filename
    from export.simple_pdf_report import parse_datetime_from_filename
    parsed_date, parsed_time = parse_datetime_from_filename(video_path)
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # Video info display
    info_frame = ttk.LabelFrame(main_frame, text="Video-Informationen", padding=10)
    info_frame.pack(fill=tk.X, pady=(0, 15))
    
    ttk.Label(info_frame, text=f"Dateiname: {os.path.basename(video_path)}", 
                font=('Arial', 10)).pack(anchor=tk.W)
    ttk.Label(info_frame, text=f"Erkanntes Datum: {parsed_date}", 
                font=('Arial', 10)).pack(anchor=tk.W, pady=(2, 0))
    ttk.Label(info_frame, text=f"Erkannte Zeit: {parsed_time}", 
                font=('Arial', 10)).pack(anchor=tk.W, pady=(2, 0))
    
    # Input fields frame
    fields_frame = ttk.LabelFrame(main_frame, text="Eingabe-Felder", padding=15)
    fields_frame.pack(fill=tk.X, pady=(0, 20))
    
    # Helper text
    helper_text = ttk.Label(fields_frame, 
                            text="Bitte füllen Sie die erforderlichen Felder aus (* = Pflichtfeld):",
                            font=('Arial', 9), foreground="#666666")
    helper_text.pack(anchor=tk.W, pady=(0, 15))
    
    # Video name field
    ttk.Label(fields_frame, text="Video-Name:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
    video_name_var = tk.StringVar(value=video_name)
    video_name_entry = ttk.Entry(fields_frame, textvariable=video_name_var, font=('Arial', 10))
    video_name_entry.pack(fill=tk.X, pady=(5, 15))
    
    # Location field (required)
    location_label_frame = ttk.Frame(fields_frame)
    location_label_frame.pack(fill=tk.X)
    ttk.Label(location_label_frame, text="* Aufnahmeort:", 
                font=('Arial', 10, 'bold'), foreground="#D2691E").pack(side=tk.LEFT)
    ttk.Label(location_label_frame, text="(z.B. Münster, Westfalen)", 
                font=('Arial', 9), foreground="#666666").pack(side=tk.LEFT, padx=(10, 0))
    
    location_var = tk.StringVar(value="")
    location_entry = ttk.Entry(fields_frame, textvariable=location_var, font=('Arial', 10))
    location_entry.pack(fill=tk.X, pady=(5, 15))
    
    # Observer field (required)
    observer_label_frame = ttk.Frame(fields_frame)
    observer_label_frame.pack(fill=tk.X)
    ttk.Label(observer_label_frame, text="* Beobachter:", 
                font=('Arial', 10, 'bold'), foreground="#D2691E").pack(side=tk.LEFT)
    ttk.Label(observer_label_frame, text="(Name der durchführenden Person)", 
                font=('Arial', 9), foreground="#666666").pack(side=tk.LEFT, padx=(10, 0))
    
    observer_var = tk.StringVar(value="")
    observer_entry = ttk.Entry(fields_frame, textvariable=observer_var, font=('Arial', 10))
    observer_entry.pack(fill=tk.X, pady=(5, 15))
    
    # Description field
    ttk.Label(fields_frame, text="Beschreibung (optional):", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
    desc_frame = ttk.Frame(fields_frame)
    desc_frame.pack(fill=tk.X, pady=(5, 15))
    
    description_var = tk.StringVar(value="")
    description_entry = ttk.Entry(desc_frame, textvariable=description_var, font=('Arial', 10))
    description_entry.pack(fill=tk.X)
    
    # Date and time fields
    datetime_label = ttk.Label(fields_frame, text="Aufnahme-Zeitpunkt:", font=('Arial', 10, 'bold'))
    datetime_label.pack(anchor=tk.W, pady=(5, 5))
    
    datetime_frame = ttk.Frame(fields_frame)
    datetime_frame.pack(fill=tk.X, pady=(0, 20))
    
    # Date field
    date_frame = ttk.Frame(datetime_frame)
    date_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    ttk.Label(date_frame, text="Datum:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
    date_var = tk.StringVar(value=parsed_date)
    date_entry = ttk.Entry(date_frame, textvariable=date_var, font=('Arial', 10))
    date_entry.pack(fill=tk.X, pady=(3, 0))
    
    # Time field
    time_frame = ttk.Frame(datetime_frame)
    time_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
    ttk.Label(time_frame, text="Uhrzeit:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
    time_var = tk.StringVar(value=parsed_time)
    time_entry = ttk.Entry(time_frame, textvariable=time_var, font=('Arial', 10))
    time_entry.pack(fill=tk.X, pady=(3, 0))
    
    # Result storage
    result = [None]
    
    def create_pdf():
        # Validate required fields
        if not location_var.get().strip():
            messagebox.showwarning("Fehlende Eingabe", "Bitte geben Sie einen Aufnahmeort an.")
            location_entry.focus()
            return
            
        if not observer_var.get().strip():
            messagebox.showwarning("Fehlende Eingabe", "Bitte geben Sie einen Beobachter an.")
            observer_entry.focus()
            return
        
        # Collect all information
        video_info = {
            'video_name': video_name_var.get().strip() or video_name,
            'location': location_var.get().strip(),
            'observer': observer_var.get().strip(),
            'description': description_var.get().strip() or "Keine Beschreibung",
            'recording_date': date_var.get().strip() or parsed_date,
            'recording_time': time_var.get().strip() or parsed_time
        }
        
        result[0] = video_info
        dialog.destroy()
        
    def cancel():
        result[0] = None
        dialog.destroy()
    
    # Fixed button frame at bottom (outside scrollable area)
    button_container = ttk.Frame(dialog)
    button_container.grid(row=1, column=0, sticky="ew", padx=20, pady=15)
    button_container.grid_columnconfigure(1, weight=1)  # Spacer column
    
    # Add a separator line above buttons
    separator = ttk.Separator(button_container, orient='horizontal')
    separator.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 15))
    
    # Cancel button
    cancel_btn = ttk.Button(button_container, text="❌ Abbrechen", command=cancel)
    cancel_btn.grid(row=1, column=0, sticky="w")
    
    # Create PDF button (prominent styling)
    create_btn = ttk.Button(button_container, text="📄 PDF erstellen", 
                            command=create_pdf, style='Accent.TButton')
    create_btn.grid(row=1, column=2, sticky="e")
    
    # Focus on location field if empty, otherwise on description
    if not location_var.get():
        location_entry.focus()
    else:
        description_entry.focus()
    
    # Wait for user choice
    dialog.wait_window()
    
    return result[0]

def show_previous_events_enhanced(self):
    """Enhanced previous events viewer with fast replay and event point navigation"""
    try:
        # Check if we have a video loaded
        if not hasattr(self, 'video_path') or not self.video_path:
            messagebox.showwarning("Kein Video", "Bitte laden Sie zuerst ein Video.")
            return
        
        # Import event point capture
        from validation.persistent_validator import EventPointCapture
        event_capture = EventPointCapture(self.video_path)
        
        # Load event points for fast navigation
        event_points = event_capture.load_event_points()
        
        if not event_points or not event_points.get('events'):
            # Try to load from CSV if no event points available
            from validation.persistent_validator import PersistentValidationManager
            validator = PersistentValidationManager(self.video_path)
            
            if validator.load_events_from_csv():
                # Capture event points from loaded events
                event_capture.capture_event_points(validator.events)
                event_points = event_capture.load_event_points()
            else:
                messagebox.showinfo("Keine Ereignisse", 
                                    "Keine gespeicherten Ereignisse für dieses Video gefunden.\n"
                                    "Führen Sie zuerst eine Erkennung durch.")
                return
        
        # Show enhanced event viewer with fast navigation
        self.show_enhanced_event_viewer(event_points)
        
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Laden der Ereignisse: {str(e)}")

def show_enhanced_event_viewer(self, event_points):
    """Show enhanced event viewer with fast navigation and replay"""
    viewer_window = tk.Toplevel(self.root)
    viewer_window.title("Ereignis-Navigation und schnelle Wiedergabe")
    viewer_window.transient(self.root)
    
    # Responsive sizing based on screen dimensions
    screen_width = viewer_window.winfo_screenwidth()
    screen_height = viewer_window.winfo_screenheight()
    window_width = min(800, int(screen_width * 0.85))
    window_height = min(600, int(screen_height * 0.85))
    viewer_window.geometry(f"{window_width}x{window_height}")
    viewer_window.minsize(700, 500)
    viewer_window.resizable(True, True)
    
    # Center the window
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    viewer_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # Configure grid layout for responsiveness
    viewer_window.grid_rowconfigure(0, weight=1)  # Main content area
    viewer_window.grid_rowconfigure(1, weight=0)  # Button area (fixed)
    viewer_window.grid_columnconfigure(0, weight=1)
    
    main_frame = ttk.Frame(viewer_window, padding=10)
    main_frame.grid(row=0, column=0, sticky="nsew")
    main_frame.grid_rowconfigure(2, weight=1)  # Event list area
    main_frame.grid_columnconfigure(0, weight=1)
    
    # Title
    title_label = ttk.Label(main_frame, text="Ereignis-Navigation", 
                            font=('Arial', 14, 'bold'), foreground="#2B5D8A")
    title_label.grid(row=0, column=0, sticky="w", pady=(0, 15))
    
    # Summary info
    events = event_points.get('events', [])
    total_events = len(events)
    total_duration = sum(event['duration'] for event in events)
    
    info_frame = ttk.LabelFrame(main_frame, text="Übersicht", padding=10)
    info_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
    
    ttk.Label(info_frame, text=f"Gesamte Ereignisse: {total_events}").pack(anchor=tk.W)
    ttk.Label(info_frame, text=f"Gesamtdauer: {total_duration:.1f} Sekunden").pack(anchor=tk.W)
    ttk.Label(info_frame, text=f"Durchschnittsdauer: {total_duration/total_events:.1f} Sekunden" if total_events > 0 else "").pack(anchor=tk.W)
    
    # Event list with fast navigation
    list_frame = ttk.LabelFrame(main_frame, text="Ereignisliste (Doppelklick für schnelle Navigation)", padding=10)
    list_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 0))
    list_frame.grid_rowconfigure(0, weight=1)
    list_frame.grid_columnconfigure(0, weight=1)
    
    # Create treeview for events
    tree_frame = ttk.Frame(list_frame)
    tree_frame.grid(row=0, column=0, sticky="nsew")
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)
    
    tree = ttk.Treeview(tree_frame, columns=('start', 'end', 'duration', 'type'), show='tree headings')
    tree.heading('#0', text='#', anchor=tk.W)
    tree.heading('start', text='Start (s)', anchor=tk.W)
    tree.heading('end', text='Ende (s)', anchor=tk.W)
    tree.heading('duration', text='Dauer (s)', anchor=tk.W)
    tree.heading('type', text='Typ', anchor=tk.W)
    
    tree.column('#0', width=50, minwidth=50)
    tree.column('start', width=100, minwidth=80)
    tree.column('end', width=100, minwidth=80)
    tree.column('duration', width=100, minwidth=80)
    tree.column('type', width=100, minwidth=80)
    
    # Add scrollbars
    v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
    h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=tree.xview)
    tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
    
    tree.grid(row=0, column=0, sticky="nsew")
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    h_scrollbar.grid(row=1, column=0, sticky="ew")
    
    # Populate event list
    for event in events:
        tree.insert('', tk.END, text=str(event['index'] + 1),
                    values=(f"{event['start_time']:.2f}",
                            f"{event['end_time']:.2f}",
                            f"{event['duration']:.2f}",
                            event.get('event_type', 'detection')))
    
    def on_event_double_click(event_item):
        """Handle double-click on event for fast navigation"""
        selection = tree.selection()
        if selection:
            item = tree.item(selection[0])
            event_index = int(item['text']) - 1
            
            if 0 <= event_index < len(events):
                selected_event = events[event_index]
                # Fast navigation to event
                self.navigate_to_event(selected_event)
                
    tree.bind('<Double-1>', on_event_double_click)
    
    # Action buttons (fixed at bottom)
    btn_frame = ttk.Frame(viewer_window)
    btn_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
    btn_frame.grid_columnconfigure(1, weight=1)  # Spacer column
    
    ttk.Button(btn_frame, text="🔄 Ereignisse neu laden", 
                command=lambda: self.refresh_event_points(viewer_window)).grid(row=0, column=0, sticky="w", padx=(0, 10))
    
    ttk.Button(btn_frame, text="📊 Validierungshistorie", 
                command=lambda: self.show_validation_history()).grid(row=0, column=2, sticky="e", padx=(10, 10))
    
    ttk.Button(btn_frame, text="❌ Schließen", 
                command=viewer_window.destroy).grid(row=0, column=3, sticky="e")

def navigate_to_event(self, event):
    """Navigate to specific event in video player"""
    try:
        if hasattr(self, 'detector') and hasattr(self.detector, 'cap'):
            # Navigate to event start frame
            start_frame = event['start_frame']
            self.detector.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            # Update current frame display if possible
            if hasattr(self.detector, 'current_frame'):
                self.detector.current_frame = start_frame
            
            messagebox.showinfo("Navigation", 
                                f"Zu Ereignis {event['index'] + 1} navigiert\n"
                                f"Start: {event['start_time']:.2f}s\n"
                                f"Dauer: {event['duration']:.2f}s")
        else:
            messagebox.showwarning("Video nicht geladen", 
                                    "Video ist nicht geladen. Bitte laden Sie das Video erneut.")
    except Exception as e:
        messagebox.showerror("Navigation-Fehler", f"Fehler beim Navigieren: {str(e)}")

def refresh_event_points(self, parent_window):
    """Refresh event points from current analysis"""
    try:
        if hasattr(self.detector, 'events') and self.detector.events:
            from validation.persistent_validator import EventPointCapture
            event_capture = EventPointCapture(self.video_path)
            event_capture.capture_event_points(self.detector.events)
            
            messagebox.showinfo("Aktualisiert", "Ereignispunkte wurden aktualisiert.")
            parent_window.destroy()
            self.show_previous_events_enhanced()
        else:
            messagebox.showwarning("Keine Ereignisse", "Keine aktuellen Ereignisse zum Aktualisieren.")
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Aktualisieren: {str(e)}")










def load_existing_analysis(self, analysis_info):
    """Load existing analysis results for further validation or review"""
    try:
        # Load the video file first
        self.load_video_file()
        
        # Find and load the most recent CSV file
        csv_files = analysis_info['files'].get('csv', [])
        if csv_files:
            # Use the most recent CSV file
            csv_file = max(csv_files, key=lambda f: os.path.getmtime(
                os.path.join(analysis_info['folder_path'], f)))
            csv_path = os.path.join(analysis_info['folder_path'], csv_file)
            
            # Load events from CSV
            events = self.load_events_from_csv(csv_path)
            
            if events:
                # Set loaded events to detector
                self.detector.events = events
                self.detector.video_path = self.video_path
                
                # Enable validation and export buttons
                self.btn_validate.config(state=tk.NORMAL)
                self.btn_replay_validation.config(state=tk.NORMAL)
                self.enable_export_buttons()
                
                # Update event display
                self.update_event_display()
                
                # Update status
                self.update_status(f"Bestehende Analyse geladen: {len(events)} Ereignisse | Bereit für Validierung")
                
                messagebox.showinfo("Analyse geladen", 
                                    f"Bestehende Analyse erfolgreich geladen:\n\n"
                                    f"📊 Ereignisse: {len(events)}\n"
                                    f"📁 Ordner: {analysis_info['video_name']}\n"
                                    f"📄 CSV-Datei: {csv_file}\n\n"
                                    f"Sie können jetzt weitere Validierungen durchführen oder "
                                    f"die Ergebnisse exportieren.")
            else:
                messagebox.showwarning("Keine Ereignisse", 
                                        f"Keine gültigen Ereignisse in {csv_file} gefunden.")
        else:
            messagebox.showwarning("Keine CSV-Dateien", 
                                    "Keine CSV-Dateien mit Erkennungsdaten gefunden.")
                                    
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Laden der bestehenden Analyse: {str(e)}")



def update_video_workflow_status(self, status="loaded"):
    """Update status display to show video workflow information"""
    if hasattr(self, 'video_path') and self.video_path:
        try:
            from utils.result_organizer import get_video_name_from_path
            video_name = get_video_name_from_path(self.video_path)
            
            # Add workflow info to status (now console only)
            workflow_status = f"Workflow: {video_name} ({status})"
            print(f"[STATUS] {workflow_status}")
        except:
            pass  # Don't fail if workflow status update fails





def show_validation_history(self):
    """Show validation history and progress"""
    try:
        from validation.persistent_validator import PersistentValidationManager
        validator = PersistentValidationManager(self.video_path)
        
        validator.get_validation_progress()
        
        # Create history window
        history_window = tk.Toplevel(self.root)
        history_window.title("Validierungshistorie")
        history_window.geometry("650x550")
        history_window.minsize(600, 500)
        history_window.resizable(True, True)
        history_window.transient(self.root)
        
        # Create main canvas with scrollbar for responsive design
        canvas = tk.Canvas(history_window)
        scrollbar = ttk.Scrollbar(history_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        
    except Exception as e:
        print(f"Error while displaying validation history: {e}")
