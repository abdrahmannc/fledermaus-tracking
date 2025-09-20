import tkinter as tk
from tkinter import messagebox, ttk
from wsgiref.validate import validator

# Fix matplotlib font issues on Windows

# Check for 3D Stereo Extension availability
try:
    pass
    # Also check the main 3D analysis availability
    from gui import analysis_3d_and_stereo_vision as analysis_3d
    STEREO_3D_AVAILABLE = analysis_3d.check_3d_availability()
except ImportError:
    STEREO_3D_AVAILABLE = False


def add_compact_parameter_entry(self, parent, label_text, default_value, var_name, row, col=0):
            """Adds a compact parameter entry in grid layout for 14-inch screens"""
            # Create a frame for this parameter
            param_frame = ttk.Frame(parent)
            param_frame.grid(row=row, column=col, sticky="ew", padx=2, pady=1)
            
            # Label - smaller width for compact layout
            label = ttk.Label(param_frame, text=label_text, width=8, font=("Arial", 8))
            label.pack(side="left", padx=(0, 2))
            
            # Entry - smaller width for compact layout
            var = tk.StringVar(value=str(default_value))
            setattr(self, var_name, var)
            entry = ttk.Entry(param_frame, textvariable=var, width=6, font=("Arial", 8))
            entry.pack(side="right")
            
            # Configure parent grid
            parent.columnconfigure(col, weight=1)




def add_parameter_entry(self, parent, label, default, attr):
        """Hilfsfunktion zum Erstellen beschrifteter Parametereingabefelder"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(frame, text=label, width=18, anchor=tk.W).pack(side=tk.LEFT)
        entry = ttk.Entry(frame, width=8)
        entry.insert(0, str(default))
        entry.pack(side=tk.RIGHT)
        setattr(self, f"entry_{attr}", entry)
        

   
     
def add_labeled_entry(self, parent, label, default, attr):
        frame = tk.Frame(parent, bg="#282c34")
        frame.pack(fill=tk.X, pady=1)
        tk.Label(frame, text=label, fg="#bbb", bg="#282c34").pack(side=tk.LEFT)
        entry = tk.Entry(frame, width=8)
        entry.insert(0, str(default))
        entry.pack(side=tk.RIGHT)
        setattr(self, f"entry_{attr}", entry)



          # Mouse wheel scrolling
def _on_mousewheel(event):
                try:
                    if canvas.winfo_exists():
                        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                except tk.TclError:
                    pass  # Canvas was destroyed
                canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
            
            
            
       
        # Add mouse wheel scrolling
def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                pass  # Canvas was destroyed
        
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Store reference for cleanup
            parent._canvas_mousewheel_binding = (_on_mousewheel, canvas)
        
        # Pack scrolling elements
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
        # Create grid of event thumbnails
            grid_container = ttk.Frame(scrollable_frame, padding=10)
            grid_container.pack(fill=tk.BOTH, expand=True)
            
            # Calculate grid layout (4 columns)
            cols = 4
            
            # Generate thumbnails for each event
            self.generate_event_thumbnails(grid_container, events, cols)












            # Mouse wheel scrolling
def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
            main_frame = ttk.Frame(scrollable_frame, padding=15)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title
            title_label = ttk.Label(main_frame, text="Validierungshistorie", 
                                   font=('Arial', 14, 'bold'), foreground="#2B5D8A")
            title_label.pack(anchor=tk.W, pady=(0, 15))
            
            # Progress info
            progress_frame = ttk.LabelFrame(main_frame, text="Fortschritt", padding=10)
            progress_frame.pack(fill=tk.X, pady=(0, 15))
            
            ttk.Label(progress_frame, text=f"Gesamte Ereignisse: {progress['total_events']}").pack(anchor=tk.W)
            ttk.Label(progress_frame, text=f"Validierte Ereignisse: {progress['validated_events']}").pack(anchor=tk.W)
            ttk.Label(progress_frame, text=f"Verbleibende Ereignisse: {progress['remaining_events']}").pack(anchor=tk.W)
            ttk.Label(progress_frame, text=f"Fortschritt: {progress['progress_percent']:.1f}%").pack(anchor=tk.W)
            
            # Session history
            if validator.session_data:
                session_frame = ttk.LabelFrame(main_frame, text="Sitzungshistorie", padding=10)
                session_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
                
                # Create text widget for session history
                text_widget = tk.Text(session_frame, height=10, wrap=tk.WORD)
                scrollbar = ttk.Scrollbar(session_frame, orient=tk.VERTICAL, command=text_widget.yview)
                text_widget.configure(yscrollcommand=scrollbar.set)
                
                text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
                # Add session information
                for session_id, session_info in validator.session_data.items():
                    text_widget.insert(tk.END, f"Sitzung: {session_id}\n")
                    text_widget.insert(tk.END, f"  Start: {session_info.get('start_time', 'Unbekannt')}\n")
                    text_widget.insert(tk.END, f"  Ende: {session_info.get('end_time', 'Laufend')}\n")
                    text_widget.insert(tk.END, f"  Ereignisse: {session_info.get('total_events', 0)}\n")
                    text_widget.insert(tk.END, f"  Validiert: {session_info.get('validated_count', 0)}\n\n")
                
                text_widget.config(state=tk.DISABLED)
            
            # Close button
                ttk.Button(main_frame, text="Schließen", 
                      command=history_window.destroy).pack(pady=(10, 0))
            
        #except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden der Validierungshistorie: {str(e)}")
        
        
        
        
                # Add mouse wheel scrolling support
def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                pass  # Canvas was destroyed
        
        
        
        
              # Add mouse wheel scrolling support
def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                pass  # Canvas was destroyed
        
        
        
        
               
        # Enhanced mouse wheel scrolling
def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except tk.TclError:
                pass  # Canvas was destroyed
        
        
        
        
       # Add mouse wheel scrolling support
def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except tk.TclError:
                pass  # Canvas was destroyed
        
        
        
        
        
            
def initialize_3d_button_state(self):
            """Initialize the 3D Analysis button state"""
            if STEREO_3D_AVAILABLE and hasattr(self, 'btn_3d_teil3'):
                # 3D Analysis button is always available since it opens its own interface
                self.btn_3d_teil3.config(state=tk.NORMAL)
      