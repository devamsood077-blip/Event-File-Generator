#!/usr/bin/env python3
"""
Event File Generator
Creates new event folders by copying files from template folders.
"""

import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import threading
import sys
import json

# System theme detection (Windows and macOS)
def get_system_theme():
    """Detect system theme (Light/Dark mode) for Windows and macOS."""
    if sys.platform == 'win32':
        # Windows theme detection
        try:
            import winreg
            # Check Windows 10/11 theme setting
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )
            try:
                # 0 = Light mode, 1 = Dark mode
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return 'dark' if value == 0 else 'light'
            except FileNotFoundError:
                return 'light'  # Default to light if key doesn't exist
            finally:
                winreg.CloseKey(key)
        except Exception:
            return 'light'  # Default to light on error
    elif sys.platform == 'darwin':
        # macOS theme detection
        try:
            import subprocess
            result = subprocess.run(
                ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
                capture_output=True,
                text=True,
                timeout=1
            )
            # If command succeeds, dark mode is enabled (returns "Dark")
            # If command fails, light mode is active
            if result.returncode == 0 and result.stdout.strip() == 'Dark':
                return 'dark'
            else:
                return 'light'
        except Exception:
            return 'light'  # Default to light on error
    else:
        # Linux or other platforms - default to light
        return 'light'


class EventFolderGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Event File Generator")
        self.root.geometry("600x650")
        self.root.resizable(False, True)  # Allow vertical resizing
        self.base_height = 650  # Base height without optional sections
        
        # Config file path for saving state
        # Handle both script and EXE modes
        if getattr(sys, 'frozen', False):
            # Running as compiled EXE
            base_path = Path(sys.executable).parent
        else:
            # Running as script
            base_path = Path(__file__).parent
        self.config_file = base_path / "event_generator_config.json"
        
        # Detect system theme (Windows/macOS)
        self.theme = get_system_theme()
        self.setup_theme()
        
        # Variables
        self.template_path = tk.StringVar()
        self.destination_path = tk.StringVar()
        self.selected_template = tk.StringVar()
        self.selected_subfolder = tk.StringVar()
        self.folder_name = tk.StringVar()
        self.subfolder_name = tk.StringVar()
        self.overlay_file_path = tk.StringVar()
        self.overlay_background_file_path = tk.StringVar()
        self.background_files = []  # List to store background file paths
        
        # Load saved state
        self.load_state()
        
        self.setup_menu()
        self.setup_ui()
        self.scan_templates()
        
        # Save state when window closes
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_theme(self):
        """Setup color theme based on Windows theme."""
        if self.theme == 'dark':
            # DARK THEME COLORS - Customize these hex codes:
            self.colors = {
                'bg_main': '#1e1e1e',           # Main background
                'bg_frame': '#252526',           # Frame background
                'bg_entry': '#889C9B',           # Entry field background
                'bg_button': '#3B3936',          # Button background
                'bg_button_hover': '#4a4845',    # Button hover
                'fg_button': '#B2BEBF',          # Button text color
                'fg_text': '#cccccc',            # Text color
                'fg_label': '#ffffff',           # Label text color
                'fg_entry': '#1a1a1a',           # Entry text color (dark for contrast)
                'border': '#3c3c3c',             # Border color
                'accent': '#0078d4',             # Accent color
                'status_success': '#4ec9b0',     # Success status color
                'status_error': '#f48771',      # Error status color
                'status_warning': '#ce9178',     # Warning status color
            }
        else:
            # LIGHT THEME COLORS - Customize these hex codes:
            self.colors = {
                'bg_main': '#ffffff',           # Main background
                'bg_frame': '#f3f3f3',           # Frame background
                'bg_entry': '#889C9B',           # Entry field background
                'bg_button': '#3B3936',          # Button background
                'bg_button_hover': '#4a4845',    # Button hover
                'fg_button': '#B2BEBF',          # Button text color
                'fg_text': '#323130',            # Text color
                'fg_label': '#201f1e',           # Label text color
                'fg_entry': '#1a1a1a',           # Entry text color (dark for contrast)
                'border': '#edebe9',             # Border color
                'accent': '#0078d4',             # Accent color
                'status_success': '#107c10',     # Success status color
                'status_error': '#d13438',       # Error status color
                'status_warning': '#ffaa44',     # Warning status color
            }
        
        # Apply root window background
        self.root.configure(bg=self.colors['bg_main'])
    
    def load_state(self):
        """Load saved state from config file."""
        default_template = os.path.expanduser("~")
        default_destination = os.path.expanduser("~")
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    default_template = config.get('template_path', default_template)
                    default_destination = config.get('destination_path', default_destination)
            except Exception:
                # If file is corrupted, use defaults
                pass
        
        self.template_path.set(default_template)
        self.destination_path.set(default_destination)
    
    def save_state(self):
        """Save current state to config file."""
        try:
            config = {
                'template_path': self.template_path.get(),
                'destination_path': self.destination_path.get()
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception:
            # Silently fail if we can't save
            pass
    
    def on_closing(self):
        """Handle window closing - save state before exit."""
        self.save_state()
        self.root.destroy()
    
    def setup_menu(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Template Folder Location...", command=self.show_template_folder_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Options menu
        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=options_menu)
        
        # Theme submenu
        self.theme_var = tk.StringVar(value=self.theme)
        theme_menu = tk.Menu(options_menu, tearoff=0)
        options_menu.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_radiobutton(
            label="Light Theme", 
            variable=self.theme_var,
            value='light',
            command=lambda: self.switch_theme('light')
        )
        theme_menu.add_radiobutton(
            label="Dark Theme", 
            variable=self.theme_var,
            value='dark',
            command=lambda: self.switch_theme('dark')
        )
    
    def show_template_folder_dialog(self):
        """Show dialog to select template folder location."""
        folder = filedialog.askdirectory(
            title="Select Template Folder Location",
            initialdir=self.template_path.get()
        )
        if folder:
            self.template_path.set(folder)
            self.save_state()  # Save the new template path
            self.scan_templates()
            messagebox.showinfo(
                "Template Folder Updated",
                f"Template folder location has been set to:\n{folder}\n\nTemplates have been refreshed."
            )
    
    def switch_theme(self, theme):
        """Switch between light and dark theme."""
        if self.theme == theme:
            return  # Already using this theme
        
        self.theme = theme
        if hasattr(self, 'theme_var'):
            self.theme_var.set(theme)
        self.setup_theme()
        
        # Rebuild the UI with new theme
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.setup_menu()
        self.setup_ui()
        self.scan_templates()
    
    def setup_ui(self):
        # Configure ttk styles for theme
        style = ttk.Style()
        style.theme_use('vista' if sys.platform == 'win32' else 'default')
        
        # Configure styles with theme colors
        style.configure('TFrame', background=self.colors['bg_main'])
        style.configure('TLabel', background=self.colors['bg_main'], foreground=self.colors['fg_label'])
        style.configure('TEntry', 
                       fieldbackground=self.colors['bg_entry'], 
                       foreground=self.colors['fg_entry'], 
                       bordercolor=self.colors['border'], 
                       insertcolor=self.colors['fg_entry'],
                       selectbackground=self.colors['accent'],
                       selectforeground='white')
        style.configure('TButton', background=self.colors['bg_button'], foreground=self.colors['fg_button'],
                       borderwidth=0, focuscolor='none')
        style.map('TButton', 
                  background=[('active', self.colors['bg_button_hover'])],
                  foreground=[('active', self.colors['fg_button'])])
        style.configure('TCombobox', 
                       fieldbackground=self.colors['bg_entry'], 
                       foreground=self.colors['fg_entry'],
                       bordercolor=self.colors['border'], 
                       arrowcolor=self.colors['fg_entry'],
                       selectbackground=self.colors['accent'],
                       selectforeground='white')
        style.map('TCombobox',
                  fieldbackground=[('readonly', self.colors['bg_entry'])],
                  foreground=[('readonly', self.colors['fg_entry'])])
        style.configure('TProgressbar', background=self.colors['accent'], troughcolor=self.colors['bg_frame'])
        
        # Main frame - bg_main color
        main_frame = tk.Frame(self.root, bg=self.colors['bg_main'], padx=20, pady=20)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Event Type label - fg_label color
        event_type_label = tk.Label(
            main_frame, 
            text="Event Type:", 
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['bg_main'],
            fg=self.colors['fg_label']
        )
        event_type_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Template combobox - bg_entry, fg_entry colors
        self.template_combo = ttk.Combobox(
            main_frame, 
            textvariable=self.selected_template,
            state="readonly",
            width=57
        )
        self.template_combo.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        self.template_combo.bind('<<ComboboxSelected>>', lambda e: (self.on_template_selected(e), self.update_path_preview()))
        
        # Template label - fg_label color
        template_label2 = tk.Label(
            main_frame, 
            text="Template:", 
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['bg_main'],
            fg=self.colors['fg_label']
        )
        template_label2.grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        # Template row frame - holds dropdown and preview button side by side
        template_row_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        template_row_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        template_row_frame.grid_columnconfigure(0, weight=1)
        
        # Subfolder combobox - bg_entry, fg_entry colors
        self.subfolder_combo = ttk.Combobox(
            template_row_frame,
            textvariable=self.selected_subfolder,
            state="readonly",
            width=40
        )
        self.subfolder_combo.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        self.subfolder_combo.config(state="disabled")
        self.subfolder_combo.bind('<<ComboboxSelected>>', self.on_subfolder_selected)
        
        # Preview button - bg_button color (side by side with dropdown)
        self.preview_button = tk.Button(
            template_row_frame,
            text="Preview Subfolder Contents",
            command=self.preview_template,
            state="disabled",
            bg=self.colors['bg_button'],
            fg=self.colors['fg_button'],
            activebackground=self.colors['bg_button_hover'],
            activeforeground=self.colors['fg_button'],
            disabledforeground=self.colors['fg_button'],
            font=("Segoe UI", 9),
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2"
        )
        self.preview_button.grid(row=0, column=1, sticky=tk.W)
        # Bind hover effect
        def on_preview_enter(e):
            if self.preview_button['state'] != 'disabled':
                self.preview_button.config(bg=self.colors['bg_button_hover'])
        def on_preview_leave(e):
            if self.preview_button['state'] != 'disabled':
                self.preview_button.config(bg=self.colors['bg_button'])
        self.preview_button.bind('<Enter>', on_preview_enter)
        self.preview_button.bind('<Leave>', on_preview_leave)
        
        # Destination label - fg_label color
        dest_label = tk.Label(
            main_frame, 
            text="Destination Folder:", 
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['bg_main'],
            fg=self.colors['fg_label']
        )
        dest_label.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # Destination frame - bg_frame color
        dest_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        dest_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        dest_frame.grid_columnconfigure(0, weight=1)
        
        # Entry field - bg_entry, fg_entry colors
        dest_entry = ttk.Entry(dest_frame, textvariable=self.destination_path, width=50)
        dest_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        dest_entry.bind('<KeyRelease>', lambda e: self.update_path_preview())
        dest_entry.bind('<FocusOut>', lambda e: self.update_path_preview())
        
        # Button - bg_button color
        browse_btn2 = tk.Button(
            dest_frame, 
            text="Browse", 
            command=self.browse_destination_folder,
            bg=self.colors['bg_button'],
            fg=self.colors['fg_button'],
            activebackground=self.colors['bg_button_hover'],
            activeforeground=self.colors['fg_button'],
            font=("Segoe UI", 9),
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2"
        )
        browse_btn2.grid(row=0, column=1)
        # Bind hover effect
        browse_btn2.bind('<Enter>', lambda e: browse_btn2.config(bg=self.colors['bg_button_hover']))
        browse_btn2.bind('<Leave>', lambda e: browse_btn2.config(bg=self.colors['bg_button']))
        
        # Client Name label - fg_label color
        client_name_label = tk.Label(
            main_frame, 
            text="Client Name:", 
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['bg_main'],
            fg=self.colors['fg_label']
        )
        client_name_label.grid(row=7, column=0, sticky=tk.W, pady=(0, 5))
        
        # Entry field - bg_entry, fg_entry colors
        folder_entry = ttk.Entry(main_frame, textvariable=self.folder_name, width=57)
        folder_entry.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        folder_entry.bind('<KeyRelease>', lambda e: self.update_path_preview())
        folder_entry.bind('<FocusOut>', lambda e: self.update_path_preview())
        
        # Event Name label - fg_label color
        event_name_label = tk.Label(
            main_frame, 
            text="Event Name:", 
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['bg_main'],
            fg=self.colors['fg_label']
        )
        event_name_label.grid(row=9, column=0, sticky=tk.W, pady=(0, 5))
        
        # Entry field - bg_entry, fg_entry colors
        subfolder_entry = ttk.Entry(main_frame, textvariable=self.subfolder_name, width=57)
        subfolder_entry.grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        subfolder_entry.bind('<KeyRelease>', lambda e: self.update_path_preview())
        subfolder_entry.bind('<FocusOut>', lambda e: self.update_path_preview())
        
        # Background files section (hidden by default, shown for AI Removal/Greenscreen)
        self.background_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        self.background_frame.grid(row=11, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        self.background_frame.grid_columnconfigure(0, weight=1)
        self.background_frame.grid_remove()  # Hidden by default
        
        # Background label - fg_label color (will be updated dynamically)
        self.background_label = tk.Label(
            self.background_frame,
            text="Background Images (required: 3-4):",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['bg_main'],
            fg=self.colors['fg_label']
        )
        self.background_label.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        # Background files list frame
        self.background_list_frame = tk.Frame(self.background_frame, bg=self.colors['bg_main'])
        self.background_list_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        self.background_list_frame.grid_columnconfigure(0, weight=1)
        
        # Background files listbox
        self.background_listbox = tk.Listbox(
            self.background_list_frame,
            height=3,
            bg=self.colors['bg_entry'],
            fg=self.colors['fg_entry'],
            selectbackground=self.colors['accent'],
            selectforeground='white',
            font=("Segoe UI", 9)
        )
        self.background_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # Scrollbar for listbox
        background_scrollbar = tk.Scrollbar(self.background_list_frame, orient=tk.VERTICAL, command=self.background_listbox.yview)
        background_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.background_listbox.config(yscrollcommand=background_scrollbar.set)
        
        # Background buttons frame
        background_buttons_frame = tk.Frame(self.background_frame, bg=self.colors['bg_main'])
        background_buttons_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W)
        
        # Add background button
        self.add_background_btn = tk.Button(
            background_buttons_frame,
            text="Add Background Files",
            command=self.browse_background_files,
            bg=self.colors['bg_button'],
            fg=self.colors['fg_button'],
            activebackground=self.colors['bg_button_hover'],
            activeforeground=self.colors['fg_button'],
            font=("Segoe UI", 9),
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2"
        )
        self.add_background_btn.grid(row=0, column=0, padx=(0, 5))
        self.add_background_btn.bind('<Enter>', lambda e: self.add_background_btn.config(bg=self.colors['bg_button_hover']))
        self.add_background_btn.bind('<Leave>', lambda e: self.add_background_btn.config(bg=self.colors['bg_button']))
        
        # Clear background button
        self.clear_background_btn = tk.Button(
            background_buttons_frame,
            text="Clear All",
            command=self.clear_background_files,
            bg=self.colors['bg_button'],
            fg=self.colors['fg_button'],
            activebackground=self.colors['bg_button_hover'],
            activeforeground=self.colors['fg_button'],
            font=("Segoe UI", 9),
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2"
        )
        self.clear_background_btn.grid(row=0, column=1)
        self.clear_background_btn.bind('<Enter>', lambda e: self.clear_background_btn.config(bg=self.colors['bg_button_hover']))
        self.clear_background_btn.bind('<Leave>', lambda e: self.clear_background_btn.config(bg=self.colors['bg_button']))
        
        # Overlay label - fg_label color
        overlay_label = tk.Label(
            main_frame, 
            text="Overlay Image (optional):", 
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['bg_main'],
            fg=self.colors['fg_label']
        )
        overlay_label.grid(row=12, column=0, sticky=tk.W, pady=(0, 5))
        
        # Overlay frame - bg_frame color
        overlay_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        overlay_frame.grid(row=13, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        overlay_frame.grid_columnconfigure(0, weight=1)
        
        # Entry field - bg_entry, fg_entry colors
        overlay_entry = ttk.Entry(overlay_frame, textvariable=self.overlay_file_path, width=50, state="readonly")
        overlay_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # Buttons - bg_button color
        browse_btn3 = tk.Button(
            overlay_frame, 
            text="Browse", 
            command=self.browse_overlay_file,
            bg=self.colors['bg_button'],
            fg=self.colors['fg_button'],
            activebackground=self.colors['bg_button_hover'],
            activeforeground=self.colors['fg_button'],
            font=("Segoe UI", 9),
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2"
        )
        browse_btn3.grid(row=0, column=1)
        browse_btn3.bind('<Enter>', lambda e: browse_btn3.config(bg=self.colors['bg_button_hover']))
        browse_btn3.bind('<Leave>', lambda e: browse_btn3.config(bg=self.colors['bg_button']))
        
        clear_btn = tk.Button(
            overlay_frame, 
            text="Clear", 
            command=self.clear_overlay_file,
            bg=self.colors['bg_button'],
            fg=self.colors['fg_button'],
            activebackground=self.colors['bg_button_hover'],
            activeforeground=self.colors['fg_button'],
            font=("Segoe UI", 9),
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2"
        )
        clear_btn.grid(row=0, column=2, padx=(5, 0))
        clear_btn.bind('<Enter>', lambda e: clear_btn.config(bg=self.colors['bg_button_hover']))
        clear_btn.bind('<Leave>', lambda e: clear_btn.config(bg=self.colors['bg_button']))
        
        # Overlay Background section (hidden by default, shown for AI Removal/Greenscreen with 2X6/4X6 3/4 shot)
        self.overlay_background_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        self.overlay_background_frame.grid(row=14, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        self.overlay_background_frame.grid_columnconfigure(0, weight=1)
        self.overlay_background_frame.grid_remove()  # Hidden by default
        
        # Overlay Background label - fg_label color
        overlay_background_label = tk.Label(
            self.overlay_background_frame, 
            text="Overlay Background (optional):", 
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['bg_main'],
            fg=self.colors['fg_label']
        )
        overlay_background_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Overlay Background frame - bg_frame color
        overlay_background_entry_frame = tk.Frame(self.overlay_background_frame, bg=self.colors['bg_main'])
        overlay_background_entry_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 0))
        overlay_background_entry_frame.grid_columnconfigure(0, weight=1)
        
        # Entry field - bg_entry, fg_entry colors
        overlay_background_entry = ttk.Entry(overlay_background_entry_frame, textvariable=self.overlay_background_file_path, width=50, state="readonly")
        overlay_background_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # Buttons - bg_button color
        browse_overlay_bg_btn = tk.Button(
            overlay_background_entry_frame, 
            text="Browse", 
            command=self.browse_overlay_background_file,
            bg=self.colors['bg_button'],
            fg=self.colors['fg_button'],
            activebackground=self.colors['bg_button_hover'],
            activeforeground=self.colors['fg_button'],
            font=("Segoe UI", 9),
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2"
        )
        browse_overlay_bg_btn.grid(row=0, column=1)
        browse_overlay_bg_btn.bind('<Enter>', lambda e: browse_overlay_bg_btn.config(bg=self.colors['bg_button_hover']))
        browse_overlay_bg_btn.bind('<Leave>', lambda e: browse_overlay_bg_btn.config(bg=self.colors['bg_button']))
        
        clear_overlay_bg_btn = tk.Button(
            overlay_background_entry_frame, 
            text="Clear", 
            command=self.clear_overlay_background_file,
            bg=self.colors['bg_button'],
            fg=self.colors['fg_button'],
            activebackground=self.colors['bg_button_hover'],
            activeforeground=self.colors['fg_button'],
            font=("Segoe UI", 9),
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2"
        )
        clear_overlay_bg_btn.grid(row=0, column=2, padx=(5, 0))
        clear_overlay_bg_btn.bind('<Enter>', lambda e: clear_overlay_bg_btn.config(bg=self.colors['bg_button_hover']))
        clear_overlay_bg_btn.bind('<Leave>', lambda e: clear_overlay_bg_btn.config(bg=self.colors['bg_button']))
        
        # Path preview label - shows the full path that will be created
        path_preview_label = tk.Label(
            main_frame,
            text="Path Preview:",
            font=("Segoe UI", 9, "bold"),
            bg=self.colors['bg_main'],
            fg=self.colors['fg_label']
        )
        path_preview_label.grid(row=15, column=0, sticky=tk.W, pady=(10, 5))
        
        # Path preview display - fg_text color, wrapped text
        self.path_preview = tk.Label(
            main_frame,
            text="",
            font=("Segoe UI", 8),
            bg=self.colors['bg_main'],
            fg=self.colors['fg_text'],
            wraplength=560,
            justify=tk.LEFT,
            anchor=tk.W
        )
        self.path_preview.grid(row=16, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Generate button - special color #486966 background, #B2BEBF text
        self.generate_button = tk.Button(
            main_frame,
            text="Generate Event Folder",
            command=self.generate_folder,
            bg='#486966',
            fg='#B2BEBF',
            activebackground='#5a7a77',
            activeforeground='#B2BEBF',
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2"
        )
        self.generate_button.grid(row=17, column=0, columnspan=2, pady=10)
        # Bind hover effect
        self.generate_button.bind('<Enter>', lambda e: self.generate_button.config(bg='#5a7a77'))
        self.generate_button.bind('<Leave>', lambda e: self.generate_button.config(bg='#486966'))
        
        # Status label - fg_text color
        self.status_label = tk.Label(
            main_frame,
            text="Ready",
            font=("Segoe UI", 9),
            bg=self.colors['bg_main'],
            fg=self.colors['fg_text']
        )
        self.status_label.grid(row=17, column=0, columnspan=2, pady=(10, 0))
        
        # Progress bar - accent color
        self.progress = ttk.Progressbar(
            main_frame,
            mode='indeterminate',
            length=560
        )
        self.progress.grid(row=18, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
    
    
    def browse_destination_folder(self):
        folder = filedialog.askdirectory(
            title="Select Destination Folder",
            initialdir=self.destination_path.get()
        )
        if folder:
            self.destination_path.set(folder)
            self.save_state()  # Save the new destination path
            self.update_path_preview()
    
    def browse_overlay_file(self):
        """Browse for overlay image file."""
        file_path = filedialog.askopenfilename(
            title="Select Overlay Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("PNG files", "*.png"),
                ("All files", "*.*")
            ],
            initialdir=os.path.dirname(self.overlay_file_path.get()) if self.overlay_file_path.get() else os.path.expanduser("~")
        )
        if file_path:
            self.overlay_file_path.set(file_path)
    
    def clear_overlay_file(self):
        """Clear the selected overlay file."""
        self.overlay_file_path.set("")
    
    def browse_overlay_background_file(self):
        """Browse for overlay background image file."""
        file_path = filedialog.askopenfilename(
            title="Select Overlay Background Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("All files", "*.*")
            ],
            initialdir=os.path.dirname(self.overlay_background_file_path.get()) if self.overlay_background_file_path.get() else os.path.expanduser("~")
        )
        if file_path:
            self.overlay_background_file_path.set(file_path)
    
    def clear_overlay_background_file(self):
        """Clear the selected overlay background file."""
        self.overlay_background_file_path.set("")
    
    def browse_background_files(self):
        """Browse for background image files (3 or 4 based on template)."""
        # Get required count based on selected subfolder
        subfolder_name = self.selected_subfolder.get()
        required_count = self.get_required_background_count(subfolder_name)
        
        # Calculate how many more files can be added
        remaining_slots = required_count - len(self.background_files)
        if remaining_slots <= 0:
            messagebox.showinfo("Maximum Reached", f"You can only select up to {required_count} background files.")
            return
        
        file_paths = filedialog.askopenfilenames(
            title=f"Select Background Images (up to {remaining_slots} more, {required_count} total required)",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("PNG files", "*.png"),
                ("All files", "*.*")
            ],
            initialdir=os.path.expanduser("~")
        )
        
        if file_paths:
            # Limit to remaining slots
            files_to_add = list(file_paths)[:remaining_slots]
            self.background_files.extend(files_to_add)
            self.update_background_listbox()
            
            if len(file_paths) > remaining_slots:
                messagebox.showinfo("Limit Reached", f"Only {remaining_slots} file(s) were added. Maximum of {required_count} files allowed.")
    
    def clear_background_files(self):
        """Clear all selected background files."""
        self.background_files = []
        self.update_background_listbox()
    
    def update_background_listbox(self):
        """Update the background files listbox display."""
        self.background_listbox.delete(0, tk.END)
        for i, file_path in enumerate(self.background_files, 1):
            filename = os.path.basename(file_path)
            self.background_listbox.insert(tk.END, f"{i}. {filename}")
    
    def should_show_background_section(self, template_name, subfolder_name=None):
        """Check if background section should be shown for the selected template and subfolder."""
        template_lower = template_name.lower() if template_name else ""
        subfolder_lower = subfolder_name.lower() if subfolder_name else ""
        
        # Check if it's AI Removal or Green Screen
        is_ai_or_green = "ai removal" in template_lower or "greenscreen" in template_lower
        
        if not is_ai_or_green:
            return False
        
        # Check if subfolder matches the specific patterns:
        # - 2X6 3 shot, 2X6 4 shot, 4X6 3 shot, 4X6 4 shot (for gif/greenscreen naming)
        # - 4X61 shot (no space between 4X6 and 1) for simple background naming
        # Also handle variations like "2x6 - 3 shot", "2x6-3shot", "4x61shot", etc.
        patterns = ["2x6", "4x6"]
        shots_3_4 = ["3 shot", "4 shot", "3shot", "4shot", "3-shot", "4-shot"]
        shots_1 = ["1 shot", "1shot", "1-shot"]
        
        # Check for 3/4 shot patterns
        for pattern in patterns:
            for shot in shots_3_4:
                if pattern in subfolder_lower and shot in subfolder_lower:
                    return True
        
        # Check for 4X61 shot pattern (no space between 4X6 and 1, only for AI Removal)
        if "ai removal" in template_lower:
            # Check for "4x61 shot" or "4x61shot" (no space)
            if "4x61" in subfolder_lower and ("shot" in subfolder_lower or "1" in subfolder_lower):
                return True
            # Also check for variations with space: "4x6 1 shot", "4x6-1shot", etc.
            for shot in shots_1:
                if "4x6" in subfolder_lower and shot in subfolder_lower:
                    return True
        
        return False
    
    def get_required_background_count(self, subfolder_name):
        """Get the required number of background images based on subfolder name."""
        subfolder_lower = subfolder_name.lower() if subfolder_name else ""
        
        if "3 shot" in subfolder_lower or "3shot" in subfolder_lower or "3-shot" in subfolder_lower:
            return 3
        elif "4 shot" in subfolder_lower or "4shot" in subfolder_lower or "4-shot" in subfolder_lower:
            return 4
        elif "4x61" in subfolder_lower or "1 shot" in subfolder_lower or "1shot" in subfolder_lower or "1-shot" in subfolder_lower:
            # For 4X61 shot (no space) or 4X6 1 shot, allow multiple images (no strict limit, but cap at 20 for UI)
            return 20  # Allow up to 20 images for 1 shot templates
        
        return 4  # Default to 4 if not specified
    
    def scan_templates(self):
        """Scan the template folder for available templates."""
        template_dir = Path(self.template_path.get())
        
        if not template_dir.exists():
            self.template_combo['values'] = []
            self.subfolder_combo.config(state="disabled", values=[])
            self.selected_subfolder.set("")
            self.preview_button.config(state="disabled")
            self.status_label.config(text="Template folder not found", fg=self.colors['status_error'])
            return
        
        # Get all folders in the template directory
        templates = []
        try:
            for item in template_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    templates.append(item.name)
        except PermissionError:
            self.subfolder_combo.config(state="disabled", values=[])
            self.selected_subfolder.set("")
            self.preview_button.config(state="disabled")
            self.status_label.config(text="Permission denied accessing template folder", fg=self.colors['status_error'])
            return
        
        templates.sort()
        self.template_combo['values'] = templates
        
        if templates:
            self.status_label.config(text=f"Found {len(templates)} template(s)", fg=self.colors['status_success'])
        else:
            self.subfolder_combo.config(state="disabled", values=[])
            self.selected_subfolder.set("")
            self.preview_button.config(state="disabled")
            self.status_label.config(text="No templates found", fg=self.colors['status_warning'])
    
    def scan_subfolders(self, template_path):
        """Scan the template folder for available subfolders."""
        subfolders = []
        try:
            for item in template_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    subfolders.append(item.name)
        except Exception:
            pass
        
        subfolders.sort()
        return subfolders
    
    def on_template_selected(self, event=None):
        """Populate subfolder dropdown when template is selected."""
        template_name = self.selected_template.get()
        if not template_name:
            self.subfolder_combo.config(state="disabled", values=[])
            self.selected_subfolder.set("")
            self.preview_button.config(state="disabled")
            # Hide background section
            self.background_frame.grid_remove()
            return
        
        template_dir = Path(self.template_path.get())
        template_path = template_dir / template_name
        
        if not template_path.exists():
            self.subfolder_combo.config(state="disabled", values=[])
            self.selected_subfolder.set("")
            self.preview_button.config(state="disabled")
            # Hide background section
            self.background_frame.grid_remove()
            return
        
        # Show/hide background section based on template and subfolder
        # We'll update this when subfolder is selected
        # For now, just hide it if template doesn't match
        if "ai removal" in template_name.lower() or "greenscreen" in template_name.lower():
            # Will show when subfolder is selected
            self.background_frame.grid_remove()
            self.overlay_background_frame.grid_remove()
        else:
            self.background_frame.grid_remove()
            self.overlay_background_frame.grid_remove()
            # Clear background files if template doesn't need them
            self.background_files = []
            self.update_background_listbox()
            # Clear overlay background file
            self.overlay_background_file_path.set("")
        
        # Scan for subfolders
        subfolders = self.scan_subfolders(template_path)
        
        if subfolders:
            self.subfolder_combo.config(state="readonly", values=subfolders)
            self.status_label.config(
                text=f"Found {len(subfolders)} subfolder(s) in '{template_name}'",
                fg=self.colors['status_success']
            )
        else:
            self.subfolder_combo.config(state="disabled", values=[])
            self.selected_subfolder.set("")
            self.status_label.config(
                text=f"No subfolders found in '{template_name}'",
                fg=self.colors['status_warning']
            )
            self.preview_button.config(state="disabled")
        
        # Update path preview when template changes
        self.update_path_preview()
    
    def on_subfolder_selected(self, event=None):
        """Enable preview button when subfolder is selected."""
        if self.selected_subfolder.get():
            self.preview_button.config(state="normal")
        
        # Show/hide background section based on template and subfolder
        template_name = self.selected_template.get()
        subfolder_name = self.selected_subfolder.get()
        if self.should_show_background_section(template_name, subfolder_name):
            self.background_frame.grid()
            # Update label to show required count or indicate multiple allowed
            subfolder_lower = subfolder_name.lower() if subfolder_name else ""
            is_1shot = "4x61" in subfolder_lower or "1 shot" in subfolder_lower or "1shot" in subfolder_lower or "1-shot" in subfolder_lower
            if hasattr(self, 'background_label'):
                if is_1shot:
                    self.background_label.config(text="Background Images (multiple allowed):")
                else:
                    required_count = self.get_required_background_count(subfolder_name)
                    self.background_label.config(text=f"Background Images (required: {required_count}):")
            # Show overlay background section only for 3/4 shot patterns, not for 1 shot
            if not is_1shot:
                self.overlay_background_frame.grid()
            else:
                self.overlay_background_frame.grid_remove()
                self.overlay_background_file_path.set("")
        else:
            self.background_frame.grid_remove()
            self.overlay_background_frame.grid_remove()
            # Clear background files if template doesn't need them
            self.background_files = []
            self.update_background_listbox()
            # Clear overlay background file
            self.overlay_background_file_path.set("")
        
        # Update window height based on visible sections
        self.update_window_height()
        self.update_path_preview()
    
    def update_window_height(self):
        """Update window height based on visible sections."""
        if not hasattr(self, 'background_frame') or not hasattr(self, 'overlay_background_frame'):
            return
        
        # Base height
        height = self.base_height
        
        # Check if background section is visible
        # winfo_ismapped() returns False for grid_remove()'d widgets
        try:
            background_visible = self.background_frame.winfo_ismapped()
        except:
            background_visible = False
        
        # Check if overlay background section is visible
        try:
            overlay_bg_visible = self.overlay_background_frame.winfo_ismapped()
        except:
            overlay_bg_visible = False
        
        # Add height for visible sections
        # Background section adds approximately 100px
        if background_visible:
            height += 100
        
        # Overlay background section adds approximately 60px
        if overlay_bg_visible:
            height += 60
        
        # Update window geometry (keep width at 600)
        self.root.geometry(f"600x{height}")
    
    def update_path_preview(self):
        """Update the path preview display based on current inputs."""
        # Check if path_preview widget exists (might not be created yet during UI setup)
        if not hasattr(self, 'path_preview'):
            return
        
        destination = self.destination_path.get().strip()
        client_name = self.folder_name.get().strip()
        template_name = self.selected_template.get()  # Event Type (e.g., "BnW")
        subfolder_name = self.selected_subfolder.get()  # Template Subfolder (e.g., "4x6 1 shot Horizontal")
        event_name = self.subfolder_name.get().strip()  # Event Name (e.g., "Sood")
        
        # Build the path preview
        if destination and client_name and template_name and subfolder_name and event_name:
            # Main folder: Client Name - Event Type - Template Subfolder
            # Remove "Horizontal" or "Vertical" from subfolder name if present
            clean_subfolder = subfolder_name.replace(" Horizontal", "").replace(" Vertical", "").strip()
            main_folder_name = f"{client_name} - {template_name} - {clean_subfolder}"
            # Full path includes event name as subfolder
            full_path = Path(destination) / main_folder_name / event_name
            self.path_preview.config(text=str(full_path), fg=self.colors['fg_text'])
        else:
            # Show what's missing
            missing = []
            if not destination:
                missing.append("Destination")
            if not client_name:
                missing.append("Client Name")
            if not template_name:
                missing.append("Event Type")
            if not subfolder_name:
                missing.append("Template")
            if not event_name:
                missing.append("Event Name")
            
            if missing:
                self.path_preview.config(
                    text=f"Complete the following: {', '.join(missing)}",
                    fg=self.colors['status_warning']
                )
            else:
                self.path_preview.config(text="", fg=self.colors['fg_text'])
    
    def get_template_structure(self, template_path):
        """Get the structure of a template folder (subfolders and file counts)."""
        structure = {
            'subfolders': [],
            'total_files': 0,
            'total_subfolders': 0
        }
        
        try:
            for item in template_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    structure['subfolders'].append(item.name)
                    structure['total_subfolders'] += 1
                    # Count files in subfolder
                    try:
                        file_count = sum(1 for f in item.rglob('*') if f.is_file())
                        structure['total_files'] += file_count
                    except:
                        pass
        except Exception as e:
            pass
        
        structure['subfolders'].sort()
        return structure
    
    def preview_template(self):
        """Show a preview of what will be copied from the selected subfolder."""
        if not self.selected_template.get():
            messagebox.showwarning("No Template Selected", "Please select a template first.")
            return
        
        if not self.selected_subfolder.get():
            messagebox.showwarning("No Subfolder Selected", "Please select a subfolder first.")
            return
        
        template_dir = Path(self.template_path.get())
        template_name = self.selected_template.get()
        subfolder_name = self.selected_subfolder.get()
        subfolder_path = template_dir / template_name / subfolder_name
        
        if not subfolder_path.exists():
            messagebox.showerror("Error", f"Subfolder '{subfolder_name}' not found")
            return
        
        # Count files and folders in the subfolder
        file_count, folder_count = self.count_files_and_folders(subfolder_path)
        
        # Build preview message
        preview_text = f"Template: {template_name}\n"
        preview_text += f"Subfolder: {subfolder_name}\n\n"
        preview_text += "-" * 50 + "\n"
        preview_text += f"Files to copy: {file_count}\n"
        preview_text += f"Folders to copy: {folder_count}\n\n"
        preview_text += "All files and subfolders will be copied recursively."
        
        messagebox.showinfo("Subfolder Preview", preview_text)
    
    def count_files_and_folders(self, path):
        """Count total files and folders in a directory tree."""
        file_count = 0
        folder_count = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    file_count += 1
                elif item.is_dir():
                    folder_count += 1
        except:
            pass
        return file_count, folder_count
    
    def copy_directory(self, src, dst):
        """Recursively copy directory and all its contents."""
        try:
            # Count what we're copying for feedback
            file_count, folder_count = self.count_files_and_folders(src)
            
            # Copy everything recursively
            shutil.copytree(src, dst, dirs_exist_ok=False)
            
            return True, file_count, folder_count
        except FileExistsError:
            return False, 0, 0
        except Exception as e:
            raise Exception(f"Error copying files: {str(e)}")
    
    def generate_folder(self):
        """Generate the new event folder with template files."""
        # Validate inputs
        if not self.selected_template.get():
            messagebox.showerror("Error", "Please select a template")
            return
        
        if not self.selected_subfolder.get():
            messagebox.showerror("Error", "Please select a subfolder")
            return
        
        if not self.folder_name.get().strip():
            messagebox.showerror("Error", "Please enter a client name")
            return
        
        if not self.subfolder_name.get().strip():
            messagebox.showerror("Error", "Please enter a subfolder name")
            return
        
        template_dir = Path(self.template_path.get())
        destination_dir = Path(self.destination_path.get())
        template_name = self.selected_template.get()
        subfolder_name = self.selected_subfolder.get()
        client_name = self.folder_name.get().strip()
        event_name = self.subfolder_name.get().strip()
        
        # Validate paths
        if not template_dir.exists():
            messagebox.showerror("Error", "Template folder does not exist")
            return
        
        if not destination_dir.exists():
            messagebox.showerror("Error", "Destination folder does not exist")
            return
        
        # Use the selected subfolder as the source
        source_path = template_dir / template_name / subfolder_name
        if not source_path.exists():
            messagebox.showerror("Error", f"Subfolder '{subfolder_name}' not found in template '{template_name}'")
            return
        
        # Create folder structure: CLIENT NAME - Event Type - Template Subfolder / Event Name
        # Remove "Horizontal" or "Vertical" from subfolder name if present
        clean_subfolder = subfolder_name.replace(" Horizontal", "").replace(" Vertical", "").strip()
        main_folder_name = f"{client_name} - {template_name} - {clean_subfolder}"
        main_folder_path = destination_dir / main_folder_name
        
        # Event name subfolder inside main folder
        event_folder_path = main_folder_path / event_name
        
        # Check if event folder already exists
        if event_folder_path.exists():
            response = messagebox.askyesno(
                "Folder Exists",
                f"Event folder '{event_name}' already exists in '{main_folder_name}'. Do you want to overwrite it?"
            )
            if not response:
                return
            # Remove existing event folder
            try:
                shutil.rmtree(event_folder_path)
            except Exception as e:
                messagebox.showerror("Error", f"Could not remove existing folder: {str(e)}")
                return
        
        # Ensure the main folder exists (but not the event subfolder - copytree will create it)
        try:
            main_folder_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Could not create main folder: {str(e)}")
            return
        
        # Disable button and show progress
        self.generate_button.config(state="disabled")
        self.progress.start()
        self.status_label.config(text="Copying files...", fg=self.colors['accent'])
        self.root.update()
        
        # Run copy in a separate thread to keep UI responsive
        def copy_thread():
            try:
                # Copy template files into the event name subfolder
                success, file_count, folder_count = self.copy_directory(source_path, event_folder_path)
                if success:
                    # Copy overlay file if provided
                    overlay_copied = False
                    if self.overlay_file_path.get().strip():
                        overlay_source = Path(self.overlay_file_path.get())
                        if overlay_source.exists() and overlay_source.is_file():
                            overlay_dest = event_folder_path / "overlay.png"
                            try:
                                shutil.copy2(overlay_source, overlay_dest)
                                overlay_copied = True
                            except Exception as e:
                                # Overlay copy failed, but continue
                                print(f"Warning: Could not copy overlay file: {e}")
                    
                    # Copy overlay background file if provided (for AI Removal/Green Screen templates)
                    overlay_background_copied = False
                    template_name_check = self.selected_template.get()
                    subfolder_name_check = self.selected_subfolder.get()
                    if self.should_show_background_section(template_name_check, subfolder_name_check):
                        if self.overlay_background_file_path.get().strip():
                            overlay_bg_source = Path(self.overlay_background_file_path.get())
                            if overlay_bg_source.exists() and overlay_bg_source.is_file():
                                overlay_bg_dest = event_folder_path / "background.jpg"
                                try:
                                    shutil.copy2(overlay_bg_source, overlay_bg_dest)
                                    overlay_background_copied = True
                                except Exception as e:
                                    # Overlay background copy failed, but continue
                                    print(f"Warning: Could not copy overlay background file: {e}")
                    
                    # Copy background files if provided
                    background_copied = 0
                    if self.background_files:
                        template_name = self.selected_template.get()
                        subfolder_name = self.selected_subfolder.get()
                        subfolder_lower = subfolder_name.lower() if subfolder_name else ""
                        template_lower = template_name.lower() if template_name else ""
                        
                        # Check if this is a 4X61 shot (no space) or 4X6 1 shot in AI Removal (simple background naming)
                        is_4x6_1shot_ai = (
                            "ai removal" in template_lower and 
                            ("4x61" in subfolder_lower or ("4x6" in subfolder_lower and ("1 shot" in subfolder_lower or "1shot" in subfolder_lower or "1-shot" in subfolder_lower)))
                        )
                        
                        # Check if this is a 3/4 shot pattern (gif/greenscreen naming)
                        is_3_4_shot = (
                            ("3 shot" in subfolder_lower or "3shot" in subfolder_lower or "3-shot" in subfolder_lower) or
                            ("4 shot" in subfolder_lower or "4shot" in subfolder_lower or "4-shot" in subfolder_lower)
                        )
                        
                        for i, bg_file_path in enumerate(self.background_files, 1):
                            bg_source = Path(bg_file_path)
                            if bg_source.exists() and bg_source.is_file():
                                # Get the file extension
                                ext = bg_source.suffix.lower()
                                
                                if is_4x6_1shot_ai:
                                    # For 4X6 1 shot in AI Removal: copy as background1.jpg, background2.jpg, etc.
                                    bg_dest = event_folder_path / f"background{i}.jpg"
                                    try:
                                        shutil.copy2(bg_source, bg_dest)
                                        background_copied += 1
                                    except Exception as e:
                                        print(f"Warning: Could not copy background file {i}: {e}")
                                elif is_3_4_shot and self.should_show_background_section(template_name, subfolder_name):
                                    # For 3/4 shot patterns: copy as both gif_background and greenscreen_background
                                    # Copy as gif_background_X.jpg
                                    gif_dest = event_folder_path / f"gif_background_{i}.jpg"
                                    try:
                                        shutil.copy2(bg_source, gif_dest)
                                        background_copied += 1
                                    except Exception as e:
                                        print(f"Warning: Could not copy gif_background file {i}: {e}")
                                    
                                    # Copy as greenscreen_background_X.jpg
                                    greenscreen_dest = event_folder_path / f"greenscreen_background_{i}.jpg"
                                    try:
                                        shutil.copy2(bg_source, greenscreen_dest)
                                    except Exception as e:
                                        print(f"Warning: Could not copy greenscreen_background file {i}: {e}")
                                else:
                                    # For other templates, use old naming
                                    bg_dest = event_folder_path / f"background{i}{ext}"
                                    try:
                                        shutil.copy2(bg_source, bg_dest)
                                        background_copied += 1
                                    except Exception as e:
                                        print(f"Warning: Could not copy background file {i}: {e}")
                    
                    self.root.after(0, lambda: self.on_copy_success(
                        main_folder_name, event_folder_path, file_count, folder_count, event_name, overlay_copied, background_copied, overlay_background_copied
                    ))
                else:
                    self.root.after(0, lambda: self.on_copy_error("Subfolder already exists"))
            except Exception as e:
                self.root.after(0, lambda: self.on_copy_error(str(e)))
        
        threading.Thread(target=copy_thread, daemon=True).start()
    
    def on_copy_success(self, folder_name, folder_path, file_count, folder_count, event_name, overlay_copied, background_copied=0, overlay_background_copied=False):
        """Handle successful folder creation."""
        self.progress.stop()
        self.generate_button.config(state="normal")
        
        status_text = f"Successfully created '{folder_name}' ({file_count} files, {folder_count} folders)"
        if overlay_copied:
            status_text += " + overlay.png"
        if overlay_background_copied:
            status_text += " + background.jpg"
        if background_copied > 0:
            status_text += f" + {background_copied} background file(s)"
        self.status_label.config(text=status_text, fg=self.colors['status_success'])
        
        success_msg = f"Event folder '{folder_name}' created successfully!\n\n"
        success_msg += f"Location: {folder_path}\n\n"
        success_msg += f"Copied: {file_count} files and {folder_count} folders"
        if overlay_copied:
            success_msg += "\nOverlay image copied as 'overlay.png'"
        if overlay_background_copied:
            success_msg += "\nOverlay background image copied as 'background.jpg'"
        if background_copied > 0:
            # Determine the naming pattern based on template and subfolder
            try:
                template_name = self.selected_template.get()
                subfolder_name = self.selected_subfolder.get()
                subfolder_lower = subfolder_name.lower() if subfolder_name else ""
                template_lower = template_name.lower() if template_name else ""
                
                is_4x6_1shot_ai = (
                    "ai removal" in template_lower and 
                    ("4x61" in subfolder_lower or ("4x6" in subfolder_lower and ("1 shot" in subfolder_lower or "1shot" in subfolder_lower or "1-shot" in subfolder_lower)))
                )
                is_3_4_shot = (
                    ("3 shot" in subfolder_lower or "3shot" in subfolder_lower or "3-shot" in subfolder_lower) or
                    ("4 shot" in subfolder_lower or "4shot" in subfolder_lower or "4-shot" in subfolder_lower)
                )
                
                if is_4x6_1shot_ai:
                    success_msg += f"\n{background_copied} background image(s) copied as 'background1.jpg', 'background2.jpg', etc."
                elif is_3_4_shot:
                    success_msg += f"\n{background_copied} background image(s) copied as 'gif_background_1.jpg', 'greenscreen_background_1.jpg', etc."
                else:
                    success_msg += f"\n{background_copied} background image(s) copied"
            except:
                success_msg += f"\n{background_copied} background image(s) copied"
        success_msg += "\n\nWould you like to open the folder?"
        
        response = messagebox.askyesno("Success", success_msg)
        
        if response:
            if sys.platform == 'win32':
                os.startfile(folder_path)
            elif sys.platform == 'darwin':
                os.system(f'open "{folder_path}"')
            else:
                os.system(f'xdg-open "{folder_path}"')
    
    def on_copy_error(self, error_msg):
        """Handle copy errors."""
        self.progress.stop()
        self.generate_button.config(state="normal")
        self.status_label.config(text="Error occurred", fg=self.colors['status_error'])
        messagebox.showerror("Error", error_msg)


def main():
    root = tk.Tk()
    app = EventFolderGenerator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
