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
import tempfile
import customtkinter as ctk
from PIL import Image, ImageDraw
import updater

LAYOUT_PREVIEWS = {
    '2X6_overlay_layout': {
        'file': '2X6_overlay_layout.png',
        'slots': [
            (0.041, 0.027, 0.419, 0.195), (0.525, 0.027, 0.435, 0.195),
            (0.041, 0.238, 0.419, 0.195), (0.525, 0.238, 0.435, 0.195),
            (0.041, 0.450, 0.419, 0.195), (0.525, 0.450, 0.435, 0.195),
            (0.041, 0.662, 0.419, 0.194), (0.525, 0.662, 0.435, 0.194),
        ],
    },
    '4X6_1_shot_horizontal': {
        'file': '4X6_1_shot_horizontal.png',
        'slots': [(0.012, 0.016, 0.977, 0.968)],
    },
    '4X6_1_shot_vertical': {
        'file': '4X6_1_shot_vertical.png',
        'slots': [(0.036, 0.020, 0.935, 0.952)],
    },
    '4X6_3_shot_vertical': {
        'file': '4X6_3_shot_vertical.png',
        'slots': [
            (0.041, 0.027, 0.919, 0.499),
            (0.041, 0.542, 0.435, 0.195),
            (0.525, 0.542, 0.435, 0.195),
        ],
    },
    '4X6_4_shot': {
        'file': '4X6_4_shot.png',
        'slots': [
            (0.027, 0.041, 0.304, 0.301),
            (0.348, 0.041, 0.305, 0.301),
            (0.669, 0.041, 0.304, 0.301),
            (0.027, 0.368, 0.597, 0.592),
        ],
    },
}


LAYOUT_DISPLAY_NAMES = {
    '2X6_overlay_layout': '2×6 Strip',
    '4X6_1_shot_horizontal': '4×6 — 1 Shot Horizontal',
    '4X6_1_shot_vertical': '4×6 — 1 Shot Vertical',
    '4X6_3_shot_vertical': '4×6 — 3 Shot',
    '4X6_4_shot': '4×6 — 4 Shot',
}


def get_layout_previews_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / 'assets' / 'layout_previews'
    return Path(__file__).parent / 'assets' / 'layout_previews'


EMPTY_SLOT_COLOR = (156, 163, 175)  # Visible gray for empty photo slots


def is_layout_slot_fill(r, g, b):
    """Gray slot fill only — preserve black/white labels and borders."""
    return 30 <= r <= 50 and 30 <= g <= 50 and 30 <= b <= 50


def is_layout_interior_fill(r, g, b):
    """Near-black interior used by 1-shot layout templates."""
    return r <= 12 and g <= 12 and b <= 12


def layout_overlay_with_holes(layout_img, layout_key):
    rgba = layout_img.convert('RGBA')
    px = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if is_layout_slot_fill(r, g, b) or (
                layout_key in ('4X6_1_shot_horizontal', '4X6_1_shot_vertical')
                and is_layout_interior_fill(r, g, b)
            ):
                px[x, y] = (r, g, b, 0)
    return rgba


def fill_slot_placeholder(canvas, box, color=EMPTY_SLOT_COLOR):
    x, y, w, h = box
    if w > 0 and h > 0:
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((x, y, x + w - 1, y + h - 1), fill=color)


def paste_slot_backgrounds(canvas, layout_key, slot_background_map, transparent_base=False):
    """Draw uploaded backgrounds into layout slot areas."""
    w, h = canvas.size
    slots = LAYOUT_PREVIEWS[layout_key]['slots']
    empty_fill = (0, 0, 0, 0) if transparent_base else (*EMPTY_SLOT_COLOR, 255)

    for slot_idx, slot_rect in enumerate(slots):
        bg_path = slot_background_map.get(slot_idx)
        if not bg_path:
            continue
        try:
            x = int(slot_rect[0] * w)
            y = int(slot_rect[1] * h)
            sw = int(slot_rect[2] * w)
            sh = int(slot_rect[3] * h)
            slot_fill = Image.new('RGBA', (sw, sh), empty_fill)
            paste_cover(slot_fill, Image.open(bg_path), (0, 0, sw, sh))
            canvas.paste(slot_fill, (x, y), slot_fill)
        except Exception:
            continue


def paste_full_background(canvas, bg_path):
    """Scale a background image to cover the entire canvas."""
    w, h = canvas.size
    if w <= 0 or h <= 0:
        return
    paste_cover(canvas, Image.open(bg_path), (0, 0, w, h))


def build_layout_composite(layout_key, layout_path, slot_background_map, full_background_path=None):
    """Layout preview (bottom) → backgrounds (top). Used when no overlay is available."""
    layout_layer = Image.open(layout_path).convert('RGBA')
    background_layer = Image.new('RGBA', layout_layer.size, (0, 0, 0, 0))
    if full_background_path:
        paste_full_background(background_layer, full_background_path)
    elif slot_background_map:
        paste_slot_backgrounds(
            background_layer, layout_key, slot_background_map, transparent_base=True
        )

    composite = layout_layer.copy()
    composite.alpha_composite(background_layer)
    return composite


def build_combined_preview(
    layout_key, layout_path, slot_background_map, overlay_path, full_background_path=None
):
    """Layout preview (bottom) → backgrounds (middle) → overlay (top)."""
    overlay_layer = Image.open(overlay_path).convert('RGBA')
    ow, oh = overlay_layer.size

    layout_layer = Image.open(layout_path).convert('RGBA')
    if layout_layer.size != (ow, oh):
        layout_layer = layout_layer.resize((ow, oh), Image.Resampling.LANCZOS)

    background_layer = Image.new('RGBA', (ow, oh), (0, 0, 0, 0))
    if full_background_path:
        paste_full_background(background_layer, full_background_path)
    elif slot_background_map:
        paste_slot_backgrounds(
            background_layer, layout_key, slot_background_map, transparent_base=True
        )

    composite = layout_layer.copy()
    composite.alpha_composite(background_layer)
    composite.alpha_composite(overlay_layer)
    return composite


def paste_cover(canvas, image, box):
    x, y, w, h = box
    if w <= 0 or h <= 0:
        return
    img = image.convert('RGBA') if canvas.mode == 'RGBA' else image.convert('RGB')
    scale = max(w / img.width, h / img.height)
    nw = max(1, int(img.width * scale))
    nh = max(1, int(img.height * scale))
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    cropped = resized.crop((left, top, left + w, top + h))
    if canvas.mode == 'RGBA' and cropped.mode == 'RGBA':
        canvas.paste(cropped, (x, y), cropped)
    else:
        canvas.paste(cropped.convert('RGB'), (x, y))


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


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class RoundedDropdown(ctk.CTkFrame):
    """Dropdown that opens a rounded menu popup instead of the native sharp menu."""

    def __init__(self, master, variable, values=None, command=None, state="normal",
                 width=200, height=36, corner_radius=8, fg_color=None, border_color=None,
                 text_color=None, font=None, **kwargs):
        super().__init__(master, fg_color=fg_color or ("#2d2e3a", "#2d2e3a"), corner_radius=corner_radius,
                         border_width=1, border_color=border_color or "#3f3f46", width=width, height=height, **kwargs)
        self._variable = variable
        self._values = list(values or [])
        self._command = command
        self._state = "normal" if state == "readonly" else state
        self._width = width
        self._height = height
        self._corner_radius = corner_radius
        self._text_color = text_color or "#e4e4e7"
        self._font = font or ("Segoe UI", 10)
        self._popup = None
        self.grid_propagate(False)
        self._label = ctk.CTkLabel(
            self, text=self._variable.get() or "Select...", anchor="w", width=width - 30, height=height - 8,
            text_color=self._text_color, font=self._font,
            fg_color="transparent"
        )
        self._label.place(relx=0, rely=0, x=10, y=2)
        self._label.bind("<Button-1>", self._on_click)
        self._label.configure(cursor="hand2")
        self.bind("<Button-1>", self._on_click)
        self.configure(cursor="hand2")
        self._variable.trace_add("write", self._on_var_write)

    def _on_var_write(self, *args):
        self._label.configure(text=self._variable.get() or "Select...")

    def _on_click(self, event=None):
        if self._state == "disabled" or not self._values:
            return
        self._show_popup()

    def _show_popup(self):
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.destroy()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 2
        popup_width = max(self._width, 120)
        max_h = 280
        item_h = 36
        n = len(self._values)
        popup_height = min(n * item_h + 12, max_h)
        self._popup = ctk.CTkToplevel(self)
        self._popup.overrideredirect(True)
        self._popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
        self._popup.attributes("-topmost", True)
        self._popup.withdraw()
        try:
            fg = self.cget("fg_color")
            bd = self.cget("border_color")
        except Exception:
            fg = "#2d2e3a"
            bd = "#3f3f46"
        frame = ctk.CTkFrame(
            self._popup, fg_color=fg, corner_radius=self._corner_radius,
            border_width=1, border_color=bd
        )
        frame.place(x=0, y=0, relwidth=1, relheight=1)
        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent", corner_radius=max(0, self._corner_radius - 2),
                                       width=popup_width - 16, height=popup_height - 16)
        scroll.place(x=6, y=6)
        for v in self._values:
            btn = ctk.CTkButton(
                scroll, text=v, anchor="w", height=32, fg_color="transparent",
                hover_color=("#3d3e4a", "#3d3e4a"), text_color=self._text_color,
                font=self._font, corner_radius=6,
                command=lambda val=v: self._select(val)
            )
            btn.pack(fill="x", pady=1)
        self._popup.deiconify()
        self._popup.focus_set()
        self._popup.bind("<Escape>", self._close_popup)
        # Delay binding FocusOut so clicking an option is processed first
        self._popup.after(150, lambda: self._popup.bind("<FocusOut>", self._delayed_close))

    def _delayed_close(self, event=None):
        """Close popup after a short delay so focus has settled (avoids closing on button click)."""
        if self._popup and self._popup.winfo_exists():
            self._popup.after(100, self._close_popup)

    def _select(self, value):
        self._variable.set(value)
        if self._command:
            self._command(value)
        self._close_popup()

    def _close_popup(self, event=None):
        if self._popup and self._popup.winfo_exists():
            try:
                self._popup.unbind("<FocusOut>")
            except Exception:
                pass
            try:
                self._popup.unbind("<Escape>")
            except Exception:
                pass
            self._popup.destroy()
            self._popup = None

    def configure(self, **kwargs):
        if "values" in kwargs:
            self._values = list(kwargs.pop("values"))
        if "state" in kwargs:
            s = kwargs.pop("state")
            self._state = "normal" if s == "readonly" else s
        if "variable" in kwargs:
            self._variable = kwargs.pop("variable")
            self._label.configure(text=self._variable.get() or "Select...")
        super().configure(**kwargs)

    def cget(self, key):
        if key == "values":
            return self._values
        if key == "state":
            return self._state
        if key == "variable":
            return self._variable
        return super().cget(key)

    def get(self):
        return self._variable.get()

    def set(self, value):
        self._variable.set(value)


class EventFolderGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Event File Generator v{updater.APP_VERSION}")
        self.window_width = 920
        self.preview_panel_width = 300
        self.base_height = 840  # Base height without optional sections
        self.layout_choice_index = 0
        self.root.geometry(f"{self.window_width}x{self.base_height}")
        self.root.resizable(False, True)  # Allow vertical resizing
        
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
        self._preview_image = None
        self._preview_pil = None
        
        self.github_token = ""
        self._update_in_progress = False

        # Load saved state
        self.load_state()
        
        self.setup_menu()
        self.setup_ui()
        self.scan_templates()
        
        # Save state when window closes
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_theme(self):
        """Setup color theme based on Windows theme."""
        ctk.set_appearance_mode("dark" if self.theme == "dark" else "light")
        if self.theme == 'dark':
            # DARK THEME COLORS - soft gradients, modern
            self.colors = {
                'bg_main': '#1a1b26',           # Main background
                'bg_frame': '#252631',           # Frame / card background
                'bg_entry': '#2d2e3a',           # Entry field background
                'bg_button': '#3d3e4a',          # Secondary button
                'bg_button_hover': '#4d4e5a',   # Button hover
                'fg_button': '#e4e4e7',         # Button text
                'fg_text': '#a1a1aa',           # Muted text
                'fg_label': '#fafafa',          # Label text
                'fg_entry': '#e4e4e7',          # Entry text
                'border': '#3f3f46',            # Border
                'accent': '#0078d4',             # Accent / primary
                'primary': '#486966',            # Primary action (generate)
                'primary_hover': '#5a7a77',     # Primary hover
                'status_success': '#22c55e',    # Success (green)
                'status_success_bg': '#14532d',  # Success alert bg
                'status_error': '#ef4444',     # Error (red)
                'status_error_bg': '#450a0a',   # Error alert bg
                'status_warning': '#f59e0b',   # Warning (amber)
                'status_warning_bg': '#422006', # Warning alert bg
                'status_info_bg': '#1e3a5f',   # Info / default alert bg
            }
        else:
            # LIGHT THEME COLORS
            self.colors = {
                'bg_main': '#f8fafc',
                'bg_frame': '#f1f5f9',
                'bg_entry': '#ffffff',
                'bg_button': '#e2e8f0',
                'bg_button_hover': '#cbd5e1',
                'fg_button': '#1e293b',
                'fg_text': '#64748b',
                'fg_label': '#0f172a',
                'fg_entry': '#1e293b',
                'border': '#e2e8f0',
                'accent': '#0078d4',
                'primary': '#486966',
                'primary_hover': '#5a7a77',
                'status_success': '#15803d',
                'status_success_bg': '#dcfce7',
                'status_error': '#dc2626',
                'status_error_bg': '#fee2e2',
                'status_warning': '#d97706',
                'status_warning_bg': '#fef3c7',
                'status_info_bg': '#dbeafe',
            }
        # UI constants for modern look
        self.corner_radius = 8
        self.entry_height = 36
        self.label_font = ("Segoe UI", 11, "bold")
        self.body_font = ("Segoe UI", 10)
        self.small_font = ("Segoe UI", 9)
        self.pad_label = (0, 6)
        self.pad_section = (0, 16)
        self.root.configure(fg_color=self.colors['bg_main'])
    
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
                    self.github_token = config.get('github_token', "") or ""
            except Exception:
                # If file is corrupted, use defaults
                pass
        
        self.template_path.set(default_template)
        self.destination_path.set(default_destination)
    
    def _read_config(self):
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def save_state(self):
        """Save current state to config file."""
        try:
            config = self._read_config()
            config['template_path'] = self.template_path.get()
            config['destination_path'] = self.destination_path.get()
            if self.github_token:
                config['github_token'] = self.github_token
            elif 'github_token' in config:
                del config['github_token']
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception:
            # Silently fail if we can't save
            pass
    
    def on_closing(self):
        """Handle window closing - save state before exit."""
        self.save_state()
        self.root.destroy()
    
    def set_status(self, text, kind="default"):
        """Update status inline alert (success, error, warning, accent, default)."""
        self.status_label.configure(text=text)
        colors_map = {
            "success": (self.colors['status_success'], self.colors['status_success_bg']),
            "error": (self.colors['status_error'], self.colors['status_error_bg']),
            "warning": (self.colors['status_warning'], self.colors['status_warning_bg']),
            "accent": (self.colors['accent'], self.colors['status_info_bg']),
            "default": (self.colors['fg_text'], self.colors['status_info_bg']),
        }
        text_color, bg_color = colors_map.get(kind, colors_map["default"])
        self.status_label.configure(text_color=text_color)
        self.status_alert_frame.configure(fg_color=bg_color)
    
    def setup_menu(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Template Folder Location...", command=self.show_template_folder_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Check for Updates...", command=self.check_for_updates)
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

    def _ask_github_token(self):
        from tkinter import simpledialog
        token = simpledialog.askstring(
            "GitHub Token",
            "This repo is private, so updates need a GitHub personal access token\n"
            "with repo read access.\n\n"
            "Create one at github.com/settings/tokens and paste it here:",
            show="*",
            parent=self.root,
        )
        token = (token or "").strip()
        if not token:
            return False
        self.github_token = token
        self.save_state()
        return True

    def check_for_updates(self):
        """Look for a newer portable on GitHub Releases and install it."""
        if self._update_in_progress:
            return
        self._update_in_progress = True
        self.set_status("Checking for updates...", "accent")

        def work():
            try:
                release = updater.fetch_latest_release(self.github_token)
                self.root.after(0, lambda r=release: self._on_update_check_result(r, None))
            except Exception as exc:
                self.root.after(0, lambda e=exc: self._on_update_check_result(None, e))

        threading.Thread(target=work, daemon=True).start()

    def _on_update_check_result(self, release, error):
        self._update_in_progress = False
        if error:
            if isinstance(error, updater.UpdateAuthError):
                if self._ask_github_token():
                    self.check_for_updates()
                    return
                self.set_status("Update check cancelled", "warning")
                return
            self.set_status("Update check failed", "error")
            messagebox.showerror("Check for Updates", str(error), parent=self.root)
            return

        latest = release["tag"]
        if not updater.is_newer(latest):
            self.set_status(f"Up to date (v{updater.APP_VERSION})", "success")
            messagebox.showinfo(
                "Check for Updates",
                f"You already have the latest version (v{updater.APP_VERSION}).",
                parent=self.root,
            )
            return

        if not updater.is_frozen():
            self.set_status(f"Update available: {latest}", "warning")
            messagebox.showinfo(
                "Update Available",
                f"Version {latest} is available (you have v{updater.APP_VERSION}).\n\n"
                "You're running from source, so the portable was not replaced.\n"
                "Use the built EXE/app, or pull the latest code and rebuild.",
                parent=self.root,
            )
            return

        install = messagebox.askyesno(
            "Update Available",
            f"Version {latest} is available (you have v{updater.APP_VERSION}).\n\n"
            "Download and install it now? The app will restart when it finishes.",
            parent=self.root,
        )
        if not install:
            self.set_status(f"Update available: {latest}", "warning")
            return
        self._download_and_install_update(release)

    def _download_and_install_update(self, release):
        self._update_in_progress = True
        self.set_status("Downloading update...", "accent")

        def work():
            try:
                asset = updater.matching_asset(release)
                suffix = ".zip" if sys.platform == "darwin" else ".exe"
                dest = Path(tempfile.gettempdir()) / f"EventFileGenerator-update{suffix}"

                def progress(read, total):
                    if total:
                        pct = int(read * 100 / total)
                        self.root.after(
                            0,
                            lambda p=pct: self.set_status(f"Downloading update... {p}%", "accent"),
                        )

                updater.download_asset(asset, dest, token=self.github_token, progress_cb=progress)
                self.root.after(0, lambda d=dest: self._apply_downloaded_update(d, None))
            except Exception as exc:
                self.root.after(0, lambda e=exc: self._apply_downloaded_update(None, e))

        threading.Thread(target=work, daemon=True).start()

    def _apply_downloaded_update(self, dest, error):
        if error:
            self._update_in_progress = False
            if isinstance(error, updater.UpdateAuthError) and self._ask_github_token():
                self.check_for_updates()
                return
            self.set_status("Update failed", "error")
            messagebox.showerror("Check for Updates", str(error), parent=self.root)
            return
        try:
            self.set_status("Installing update...", "accent")
            self.save_state()
            updater.launch_replacer(dest)
            self.root.destroy()
        except Exception as exc:
            self._update_in_progress = False
            self.set_status("Update failed", "error")
            messagebox.showerror("Check for Updates", str(exc), parent=self.root)
    
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
        # ttk progress bar style (indeterminate - CTk has no indeterminate)
        style = ttk.Style()
        style.configure('TProgressbar', background=self.colors['accent'], troughcolor=self.colors['bg_frame'])
        
        # Root grid: left form + right preview panel
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=0)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Scrollable main content (scrollbar when content overflows)
        content_width = 552
        scrollable_frame = ctk.CTkScrollableFrame(
            self.root, fg_color="transparent",
            corner_radius=0, scrollbar_button_color=self.colors['bg_frame'],
            scrollbar_button_hover_color=self.colors['bg_button_hover']
        )
        scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=(24, 12), pady=24)
        scrollable_frame.grid_columnconfigure(0, weight=1)
        main_frame = scrollable_frame  # use same variable for rest of setup_ui

        right_panel = ctk.CTkFrame(
            self.root, fg_color=self.colors['bg_frame'], corner_radius=self.corner_radius,
            width=self.preview_panel_width, border_width=1, border_color=self.colors['border']
        )
        right_panel.grid(row=0, column=1, sticky="ns", padx=(12, 24), pady=24)
        right_panel.grid_propagate(False)
        right_panel.grid_columnconfigure(0, weight=1)
        preview_wrap = self.preview_panel_width - 32
        
        # Event Type + Template in one row (2 columns)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        selector_row_width = (content_width - 12) // 2  # half minus gap

        event_type_label = ctk.CTkLabel(
            main_frame, text="Event Type:",
            font=self.label_font, text_color=self.colors['fg_label'], anchor="w"
        )
        event_type_label.grid(row=0, column=0, sticky="w", pady=self.pad_label)

        template_label2 = ctk.CTkLabel(
            main_frame, text="Template:",
            font=self.label_font, text_color=self.colors['fg_label'], anchor="w"
        )
        template_label2.grid(row=0, column=1, sticky="w", pady=self.pad_label)

        def on_template_chosen(value):
            self.on_template_selected(None)
            self.update_path_preview()

        self.template_combo = RoundedDropdown(
            main_frame, variable=self.selected_template, values=[],
            state="readonly", width=selector_row_width, height=self.entry_height,
            corner_radius=self.corner_radius, fg_color=self.colors['bg_entry'],
            border_color=self.colors['border'], text_color=self.colors['fg_entry'],
            font=self.body_font, command=on_template_chosen
        )
        self.template_combo.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=self.pad_section)

        self.subfolder_combo = RoundedDropdown(
            main_frame, variable=self.selected_subfolder, values=[],
            state="disabled", width=selector_row_width, height=self.entry_height,
            corner_radius=self.corner_radius, fg_color=self.colors['bg_entry'],
            border_color=self.colors['border'], text_color=self.colors['fg_entry'],
            font=self.body_font, command=self.on_subfolder_selected
        )
        self.subfolder_combo.grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=self.pad_section)

        template_row_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        template_row_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, self.pad_section[1]))
        template_row_frame.grid_columnconfigure(0, weight=1)

        self.preview_button = ctk.CTkButton(
            template_row_frame, text="Preview Subfolder Contents",
            command=self.preview_template, state="disabled",
            fg_color=self.colors['bg_button'], hover_color=self.colors['bg_button_hover'],
            text_color=self.colors['fg_button'], font=self.small_font,
            corner_radius=self.corner_radius, height=36, width=180
        )
        self.preview_button.grid(row=0, column=0, sticky="w")
        
        # Destination
        dest_label = ctk.CTkLabel(
            main_frame, text="Destination Folder:",
            font=self.label_font, text_color=self.colors['fg_label'], anchor="w"
        )
        dest_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=self.pad_label)
        
        dest_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        dest_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=self.pad_section)
        dest_frame.grid_columnconfigure(0, weight=1)
        
        dest_entry = ctk.CTkEntry(
            dest_frame, textvariable=self.destination_path, width=454, height=self.entry_height,
            corner_radius=self.corner_radius, fg_color=self.colors['bg_entry'],
            border_color=self.colors['border'], text_color=self.colors['fg_entry'],
            font=self.body_font
        )
        dest_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        dest_entry.bind("<KeyRelease>", lambda e: self.update_path_preview())
        dest_entry.bind("<FocusOut>", lambda e: self.update_path_preview())
        
        browse_btn2 = ctk.CTkButton(
            dest_frame, text="Browse", command=self.browse_destination_folder,
            fg_color=self.colors['bg_button'], hover_color=self.colors['bg_button_hover'],
            text_color=self.colors['fg_button'], font=self.small_font,
            corner_radius=self.corner_radius, height=36, width=90
        )
        browse_btn2.grid(row=0, column=1)
        
        # Client Name
        client_name_label = ctk.CTkLabel(
            main_frame, text="Client Name:",
            font=self.label_font, text_color=self.colors['fg_label'], anchor="w"
        )
        client_name_label.grid(row=5, column=0, sticky="w", pady=self.pad_label)
        
        folder_entry = ctk.CTkEntry(
            main_frame, textvariable=self.folder_name, width=content_width, height=self.entry_height,
            corner_radius=self.corner_radius, fg_color=self.colors['bg_entry'],
            border_color=self.colors['border'], text_color=self.colors['fg_entry'],
            font=self.body_font
        )
        folder_entry.grid(row=6, column=0, columnspan=2, sticky="ew", pady=self.pad_section)
        folder_entry.bind("<KeyRelease>", lambda e: self.update_path_preview())
        folder_entry.bind("<FocusOut>", lambda e: self.update_path_preview())
        
        # Event Name
        event_name_label = ctk.CTkLabel(
            main_frame, text="Event Name:",
            font=self.label_font, text_color=self.colors['fg_label'], anchor="w"
        )
        event_name_label.grid(row=7, column=0, sticky="w", pady=self.pad_label)
        
        subfolder_entry = ctk.CTkEntry(
            main_frame, textvariable=self.subfolder_name, width=content_width, height=self.entry_height,
            corner_radius=self.corner_radius, fg_color=self.colors['bg_entry'],
            border_color=self.colors['border'], text_color=self.colors['fg_entry'],
            font=self.body_font
        )
        subfolder_entry.grid(row=8, column=0, columnspan=2, sticky="ew", pady=self.pad_section)
        subfolder_entry.bind("<KeyRelease>", lambda e: self.update_path_preview())
        subfolder_entry.bind("<FocusOut>", lambda e: self.update_path_preview())
        
        # Background files section (hidden by default, shown for AI Removal/Greenscreen)
        self.background_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.background_frame.grid(row=9, column=0, columnspan=2, sticky="ew", pady=self.pad_section)
        self.background_frame.grid_columnconfigure(0, weight=1)
        self.background_frame.grid_remove()
        
        self.background_label = ctk.CTkLabel(
            self.background_frame, text="Background Images (required: 3-4):",
            font=self.label_font, text_color=self.colors['fg_label'], anchor="w"
        )
        self.background_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=self.pad_label)
        
        self.background_list_frame = ctk.CTkFrame(self.background_frame, fg_color="transparent")
        self.background_list_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        self.background_list_frame.grid_columnconfigure(0, weight=1)
        
        self.background_textbox = ctk.CTkTextbox(
            self.background_list_frame, height=72, width=content_width,
            corner_radius=self.corner_radius, fg_color=self.colors['bg_entry'],
            text_color=self.colors['fg_entry'], border_color=self.colors['border'],
            font=self.small_font, state="disabled", wrap="word"
        )
        self.background_textbox.grid(row=0, column=0, sticky="ew")
        
        background_buttons_frame = ctk.CTkFrame(self.background_frame, fg_color="transparent")
        background_buttons_frame.grid(row=2, column=0, columnspan=3, sticky="w")
        
        self.add_background_btn = ctk.CTkButton(
            background_buttons_frame, text="Add Background Files",
            command=self.browse_background_files,
            fg_color=self.colors['bg_button'], hover_color=self.colors['bg_button_hover'],
            text_color=self.colors['fg_button'], font=self.small_font,
            corner_radius=self.corner_radius, height=36, width=160
        )
        self.add_background_btn.grid(row=0, column=0, padx=(0, 8))
        
        self.clear_background_btn = ctk.CTkButton(
            background_buttons_frame, text="Clear All", command=self.clear_background_files,
            fg_color=self.colors['status_error'], hover_color="#b91c1c",
            text_color="white", font=self.small_font,
            corner_radius=self.corner_radius, height=36, width=90
        )
        self.clear_background_btn.grid(row=0, column=1)
        
        # Overlay Image
        overlay_label = ctk.CTkLabel(
            main_frame, text="Overlay Image (optional):",
            font=self.label_font, text_color=self.colors['fg_label'], anchor="w"
        )
        overlay_label.grid(row=10, column=0, sticky="w", pady=self.pad_label)
        
        overlay_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        overlay_frame.grid(row=11, column=0, columnspan=3, sticky="ew", pady=self.pad_section)
        overlay_frame.grid_columnconfigure(0, weight=1)
        
        overlay_entry = ctk.CTkEntry(
            overlay_frame, textvariable=self.overlay_file_path, width=374, height=self.entry_height,
            corner_radius=self.corner_radius, fg_color=self.colors['bg_entry'],
            border_color=self.colors['border'], text_color=self.colors['fg_entry'],
            font=self.body_font, state="disabled"
        )
        overlay_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        
        browse_btn3 = ctk.CTkButton(
            overlay_frame, text="Browse", command=self.browse_overlay_file,
            fg_color=self.colors['bg_button'], hover_color=self.colors['bg_button_hover'],
            text_color=self.colors['fg_button'], font=self.small_font,
            corner_radius=self.corner_radius, height=36, width=90
        )
        browse_btn3.grid(row=0, column=1)
        
        clear_btn = ctk.CTkButton(
            overlay_frame, text="Clear", command=self.clear_overlay_file,
            fg_color=self.colors['bg_button'], hover_color=self.colors['bg_button_hover'],
            text_color=self.colors['fg_button'], font=self.small_font,
            corner_radius=self.corner_radius, height=36, width=70
        )
        clear_btn.grid(row=0, column=2, padx=(8, 0))
        
        # Overlay Background section (hidden by default)
        self.overlay_background_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.overlay_background_frame.grid(row=12, column=0, columnspan=3, sticky="ew", pady=self.pad_section)
        self.overlay_background_frame.grid_columnconfigure(0, weight=1)
        self.overlay_background_frame.grid_remove()
        
        overlay_background_label = ctk.CTkLabel(
            self.overlay_background_frame, text="Overlay Background (optional):",
            font=self.label_font, text_color=self.colors['fg_label'], anchor="w"
        )
        overlay_background_label.grid(row=0, column=0, sticky="w", pady=self.pad_label)
        
        overlay_background_entry_frame = ctk.CTkFrame(self.overlay_background_frame, fg_color="transparent")
        overlay_background_entry_frame.grid(row=1, column=0, columnspan=3, sticky="ew")
        overlay_background_entry_frame.grid_columnconfigure(0, weight=1)
        
        overlay_background_entry = ctk.CTkEntry(
            overlay_background_entry_frame, textvariable=self.overlay_background_file_path,
            width=374, height=self.entry_height, state="disabled",
            corner_radius=self.corner_radius, fg_color=self.colors['bg_entry'],
            border_color=self.colors['border'], text_color=self.colors['fg_entry'],
            font=self.body_font
        )
        overlay_background_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        
        browse_overlay_bg_btn = ctk.CTkButton(
            overlay_background_entry_frame, text="Browse", command=self.browse_overlay_background_file,
            fg_color=self.colors['bg_button'], hover_color=self.colors['bg_button_hover'],
            text_color=self.colors['fg_button'], font=self.small_font,
            corner_radius=self.corner_radius, height=36, width=90
        )
        browse_overlay_bg_btn.grid(row=0, column=1)
        
        clear_overlay_bg_btn = ctk.CTkButton(
            overlay_background_entry_frame, text="Clear", command=self.clear_overlay_background_file,
            fg_color=self.colors['bg_button'], hover_color=self.colors['bg_button_hover'],
            text_color=self.colors['fg_button'], font=self.small_font,
            corner_radius=self.corner_radius, height=36, width=70
        )
        clear_overlay_bg_btn.grid(row=0, column=2, padx=(8, 0))
        
        # Status as inline alert (left column)
        self.status_alert_frame = ctk.CTkFrame(
            main_frame, fg_color=self.colors['status_info_bg'], corner_radius=self.corner_radius,
            border_width=0, height=40
        )
        self.status_alert_frame.grid(row=13, column=0, columnspan=2, sticky="ew", pady=(8, 8))
        self.status_alert_frame.grid_columnconfigure(0, weight=1)
        self.status_alert_frame.grid_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self.status_alert_frame, text="Ready",
            font=self.small_font, text_color=self.colors['fg_text'],
            anchor="w", padx=12, pady=10
        )
        self.status_label.grid(row=0, column=0, sticky="ew", padx=12, pady=8)
        
        # Progress bar (ttk indeterminate)
        self.progress = ttk.Progressbar(
            main_frame, mode='indeterminate', length=content_width
        )
        self.progress.grid(row=14, column=0, columnspan=2, pady=(0, 0), sticky="ew")

        # Right panel: template banner, path preview, combined preview, generate
        self.template_choice_banner = ctk.CTkFrame(
            right_panel, fg_color=self.colors['status_warning_bg'], corner_radius=self.corner_radius,
            border_width=2, border_color=self.colors['status_warning']
        )
        self.template_choice_banner.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 10))
        self.template_choice_banner.grid_columnconfigure(0, weight=1)

        self.template_choice_heading = ctk.CTkLabel(
            self.template_choice_banner, text="SELECTED TEMPLATE",
            font=("Segoe UI", 9, "bold"), text_color=self.colors['status_warning'], anchor="w"
        )
        self.template_choice_heading.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))

        self.template_choice_event_caption = ctk.CTkLabel(
            self.template_choice_banner, text="EVENT TYPE",
            font=("Segoe UI", 8, "bold"), text_color=self.colors['fg_text'], anchor="w"
        )
        self.template_choice_event_caption.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 0))

        self.template_choice_event_type = ctk.CTkLabel(
            self.template_choice_banner, text="—",
            font=("Segoe UI", 18, "bold"), text_color=self.colors['fg_label'],
            anchor="w", justify="left", wraplength=preview_wrap
        )
        self.template_choice_event_type.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 6))

        self.template_choice_template_caption = ctk.CTkLabel(
            self.template_choice_banner, text="TEMPLATE",
            font=("Segoe UI", 8, "bold"), text_color=self.colors['fg_text'], anchor="w"
        )
        self.template_choice_template_caption.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 0))

        self.template_choice_subfolder = ctk.CTkLabel(
            self.template_choice_banner, text="Choose Event Type & Template",
            font=("Segoe UI", 14, "bold"), text_color=self.colors['fg_label'],
            anchor="w", justify="left", wraplength=preview_wrap
        )
        self.template_choice_subfolder.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 4))

        self.template_choice_layout = ctk.CTkLabel(
            self.template_choice_banner, text="",
            font=("Segoe UI", 11), text_color=self.colors['fg_text'],
            anchor="w", justify="left", wraplength=preview_wrap
        )
        self.template_choice_layout.grid(row=5, column=0, sticky="ew", padx=12, pady=(0, 10))

        path_preview_label = ctk.CTkLabel(
            right_panel, text="Path Preview:",
            font=("Segoe UI", 10, "bold"), text_color=self.colors['fg_label'], anchor="w"
        )
        path_preview_label.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))

        self.path_preview = ctk.CTkLabel(
            right_panel, text="", font=self.small_font, text_color=self.colors['fg_text'],
            anchor="nw", justify="left", wraplength=preview_wrap
        )
        self.path_preview.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 10))

        preview_label = ctk.CTkLabel(
            right_panel, text="Layout Preview:",
            font=("Segoe UI", 10, "bold"), text_color=self.colors['fg_label'], anchor="w"
        )
        preview_label.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 6))

        self.preview_frame = ctk.CTkFrame(
            right_panel, fg_color=self.colors['bg_entry'], corner_radius=self.corner_radius,
            border_width=1, border_color=self.colors['border'], height=320
        )
        self.preview_frame.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 8))
        self.preview_frame.grid_propagate(False)
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)

        self.preview_image_label = ctk.CTkLabel(
            self.preview_frame, text="Select a template subfolder",
            font=self.small_font, text_color=self.colors['fg_text'],
            anchor="center", justify="center", wraplength=preview_wrap - 24
        )
        self.preview_image_label.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        self.layout_choice_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        self.layout_choice_frame.grid(row=5, column=0, sticky="ew", padx=16, pady=(0, 8))
        self.layout_choice_frame.grid_columnconfigure(1, weight=1)
        self.layout_choice_frame.grid_remove()

        self.layout_prev_btn = ctk.CTkButton(
            self.layout_choice_frame, text="◀", width=36, height=28,
            command=self.show_previous_layout_background,
            fg_color=self.colors['bg_button'], hover_color=self.colors['bg_button_hover'],
            text_color=self.colors['fg_button'], font=self.body_font,
            corner_radius=self.corner_radius
        )
        self.layout_prev_btn.grid(row=0, column=0, padx=(0, 6))

        self.layout_choice_counter = ctk.CTkLabel(
            self.layout_choice_frame, text="",
            font=self.small_font, text_color=self.colors['fg_text'], anchor="center"
        )
        self.layout_choice_counter.grid(row=0, column=1, sticky="ew")

        self.layout_next_btn = ctk.CTkButton(
            self.layout_choice_frame, text="▶", width=36, height=28,
            command=self.show_next_layout_background,
            fg_color=self.colors['bg_button'], hover_color=self.colors['bg_button_hover'],
            text_color=self.colors['fg_button'], font=self.body_font,
            corner_radius=self.corner_radius
        )
        self.layout_next_btn.grid(row=0, column=2, padx=(6, 0))

        self.generate_button = ctk.CTkButton(
            right_panel, text="Generate Event Folder", command=self.generate_folder,
            fg_color=self.colors['primary'], hover_color=self.colors['primary_hover'],
            text_color="#e4e4e7", font=("Segoe UI", 11, "bold"),
            corner_radius=self.corner_radius, height=44, width=preview_wrap
        )
        self.generate_button.grid(row=6, column=0, sticky="ew", padx=16, pady=(0, 16))

        self.update_template_choice_banner()
    
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
            self.update_preview()
    
    def clear_overlay_file(self):
        """Clear the selected overlay file."""
        self.overlay_file_path.set("")
        self.update_preview()
    
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
            self.update_preview()
    
    def clear_overlay_background_file(self):
        """Clear the selected overlay background file."""
        self.overlay_background_file_path.set("")
        self.update_preview()
    
    def browse_background_files(self):
        """Browse for background image files (3 or 4 based on template)."""
        # Get required count based on selected subfolder
        subfolder_name = self.selected_subfolder.get()
        required_count = self.get_required_background_count(subfolder_name, self.selected_template.get())
        
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
        self.layout_choice_index = 0
        self.update_background_listbox()
    
    def update_background_listbox(self):
        """Update the background files listbox display."""
        self.background_textbox.configure(state="normal")
        self.background_textbox.delete("0.0", "end")
        for i, file_path in enumerate(self.background_files, 1):
            filename = os.path.basename(file_path)
            self.background_textbox.insert("end", f"{i}. {filename}\n")
        self.background_textbox.configure(state="disabled")
        self.update_preview()
    
    def is_trading_cards_ai(self, template_name, subfolder_name):
        """Trading Cards template with an AI background subfolder."""
        template_lower = template_name.lower() if template_name else ""
        subfolder_lower = subfolder_name.lower() if subfolder_name else ""
        return "trading card" in template_lower and "ai background" in subfolder_lower

    def uses_background1_jpg_naming(self, template_name, subfolder_name):
        """Background files copy as background1.jpg, background2.jpg, etc."""
        if self.is_trading_cards_ai(template_name, subfolder_name):
            return True
        template_lower = template_name.lower() if template_name else ""
        subfolder_lower = subfolder_name.lower() if subfolder_name else ""
        return (
            "ai removal" in template_lower
            and (
                "4x61" in subfolder_lower
                or (
                    "4x6" in subfolder_lower
                    and ("1 shot" in subfolder_lower or "1shot" in subfolder_lower or "1-shot" in subfolder_lower)
                )
            )
        )

    def should_show_background_section(self, template_name, subfolder_name=None):
        """Check if background section should be shown for the selected template and subfolder."""
        template_lower = template_name.lower() if template_name else ""
        subfolder_lower = subfolder_name.lower() if subfolder_name else ""

        if self.is_trading_cards_ai(template_name, subfolder_name):
            return True
        
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
        if "ai removal" in template_lower or "greenscreen" in template_lower:
            # Check for "4x61 shot" or "4x61shot" (no space)
            if "4x61" in subfolder_lower and ("shot" in subfolder_lower or "1" in subfolder_lower):
                return True
            # Also check for variations with space: "4x6 1 shot", "4x6-1shot", etc.
            for shot in shots_1:
                if "4x6" in subfolder_lower and shot in subfolder_lower:
                    return True
        
        return False
    
    def uses_background_choice_carousel(self, template_name, subfolder_name):
        """Subfolders where one background is shown at a time with prev/next arrows."""
        return "choice" in (subfolder_name or "").lower()

    def get_layout_preview_key(self, template_name, subfolder_name):
        """Map the selected subfolder to a bundled layout preview image key."""
        if not subfolder_name:
            return None

        subfolder_lower = subfolder_name.lower()
        template_lower = (template_name or "").lower()

        if "trading card" in template_lower:
            if "ai background choice" in subfolder_lower:
                return "4X6_1_shot_vertical"
            return None

        if "vertical squares" in subfolder_lower and "4" in subfolder_lower and "shot" in subfolder_lower:
            return None

        if "2x6" in subfolder_lower and any(
            token in subfolder_lower for token in ("3 shot", "4 shot", "3shot", "4shot", "3-shot", "4-shot")
        ):
            return "2X6_overlay_layout"

        if "4x6" in subfolder_lower:
            if any(token in subfolder_lower for token in ("1 shot", "1shot", "1-shot")):
                if "vertical" in subfolder_lower or "square crop" in subfolder_lower:
                    return "4X6_1_shot_vertical"
                if "horizontal" in subfolder_lower or "horzontal" in subfolder_lower:
                    return "4X6_1_shot_horizontal"
                return "4X6_1_shot_horizontal"
            if any(token in subfolder_lower for token in ("3 shot", "3shot", "3-shot")):
                return "4X6_3_shot_vertical"
            if any(token in subfolder_lower for token in ("4 shot", "4shot", "4-shot")):
                return "4X6_4_shot"

        return None

    def get_layout_display_description(self, template_name, subfolder_name):
        """Human-readable print layout description for the template banner."""
        layout_key = self.get_layout_preview_key(template_name, subfolder_name)
        if layout_key:
            if layout_key == "2X6_overlay_layout":
                subfolder_lower = (subfolder_name or "").lower()
                if any(t in subfolder_lower for t in ("3 shot", "3shot", "3-shot")):
                    return "2×6 Strip — 3 Photos (dual strip)"
                return "2×6 Strip — 4 Photos (dual strip)"
            return LAYOUT_DISPLAY_NAMES.get(layout_key, layout_key.replace("_", " "))

        subfolder_lower = (subfolder_name or "").lower()
        template_lower = (template_name or "").lower()
        if "trading card" in template_lower:
            if "ai background choice" in subfolder_lower:
                return "Trading Card — AI Background Choice"
            if "ai background removal" in subfolder_lower:
                return "Trading Card — AI Background Removal"
            if "non ai" in subfolder_lower:
                return "Trading Card — Non AI"
            return "Trading Card"
        if "vertical squares" in subfolder_lower:
            return "4×6 — 4 Shot Vertical Squares"
        return None

    def update_template_choice_banner(self):
        """Update the prominent selected-template banner above the path preview."""
        if not hasattr(self, 'template_choice_banner'):
            return

        template_name = self.selected_template.get()
        subfolder_name = self.selected_subfolder.get()
        layout_desc = self.get_layout_display_description(template_name, subfolder_name)

        if template_name and subfolder_name:
            self.template_choice_banner.configure(
                fg_color=self.colors['primary'],
                border_color=self.colors['primary_hover']
            )
            caption_color = "#cbd5e1"
            self.template_choice_heading.configure(text_color="#e4e4e7")
            self.template_choice_event_caption.configure(text_color=caption_color)
            self.template_choice_template_caption.configure(text_color=caption_color)
            self.template_choice_event_type.configure(
                text=template_name,
                text_color="#ffffff"
            )
            self.template_choice_subfolder.configure(
                text=subfolder_name,
                text_color="#ffffff"
            )
            layout_text = f"Print Layout: {layout_desc}" if layout_desc else ""
            self.template_choice_layout.configure(
                text=layout_text,
                text_color="#d1d5db"
            )
        elif template_name:
            self.template_choice_banner.configure(
                fg_color=self.colors['status_warning_bg'],
                border_color=self.colors['status_warning']
            )
            self.template_choice_heading.configure(text_color=self.colors['status_warning'])
            self.template_choice_event_caption.configure(text_color=self.colors['fg_text'])
            self.template_choice_template_caption.configure(text_color=self.colors['fg_text'])
            self.template_choice_event_type.configure(
                text=template_name,
                text_color=self.colors['fg_label']
            )
            self.template_choice_subfolder.configure(
                text="Select a Template →",
                text_color=self.colors['status_warning']
            )
            self.template_choice_layout.configure(
                text="Choose the template subfolder on the left.",
                text_color=self.colors['fg_text']
            )
        else:
            self.template_choice_banner.configure(
                fg_color=self.colors['status_warning_bg'],
                border_color=self.colors['status_warning']
            )
            self.template_choice_heading.configure(text_color=self.colors['status_warning'])
            self.template_choice_event_caption.configure(text_color=self.colors['fg_text'])
            self.template_choice_template_caption.configure(text_color=self.colors['fg_text'])
            self.template_choice_event_type.configure(
                text="—",
                text_color=self.colors['fg_text']
            )
            self.template_choice_subfolder.configure(
                text="Choose Event Type & Template",
                text_color=self.colors['fg_label']
            )
            self.template_choice_layout.configure(
                text="Pick both dropdowns on the left before generating.",
                text_color=self.colors['fg_text']
            )

    def get_preview_background_files(self):
        """Background files shown in the choice/carousel preview."""
        return [path for path in self.background_files if Path(path).exists()]

    def get_preview_overlay_background_path(self):
        """Single overlay background scaled to fill the entire preview."""
        overlay_bg = self.overlay_background_file_path.get().strip()
        if not overlay_bg or not Path(overlay_bg).exists():
            return None
        template_name = self.selected_template.get()
        subfolder_name = self.selected_subfolder.get()
        if self.should_show_background_section(template_name, subfolder_name):
            return overlay_bg
        return None

    def should_preview_slot_backgrounds(self):
        """Per-slot previews only for choice/carousel templates."""
        return self.uses_background_choice_carousel(
            self.selected_template.get(), self.selected_subfolder.get()
        )

    def build_slot_background_map(self, layout_key):
        """Assign uploaded backgrounds to layout slot indices."""
        files = self.get_preview_background_files()
        subfolder_lower = (self.selected_subfolder.get() or "").lower()
        mapping = {}
        slots = LAYOUT_PREVIEWS[layout_key]['slots']

        if layout_key == "2X6_overlay_layout":
            is_3_shot = any(token in subfolder_lower for token in ("3 shot", "3shot", "3-shot"))
            pairs = [(0, 1), (2, 3), (4, 5), (6, 7)]
            pair_count = 3 if is_3_shot else 4
            for pair_idx in range(pair_count):
                bg_path = files[pair_idx] if pair_idx < len(files) else None
                for slot_idx in pairs[pair_idx]:
                    mapping[slot_idx] = bg_path
            return mapping

        if layout_key in ("4X6_1_shot_horizontal", "4X6_1_shot_vertical"):
            if files:
                if self.uses_background_choice_carousel(
                    self.selected_template.get(), self.selected_subfolder.get()
                ):
                    idx = self.layout_choice_index % len(files)
                    mapping[0] = files[idx]
                else:
                    mapping[0] = files[0]
            return mapping

        # 3/4 shot slot files are not previewed; overlay background fills the whole canvas.
        if len(files) == 1 and len(slots) > 1:
            return mapping

        for slot_idx in range(len(slots)):
            mapping[slot_idx] = files[slot_idx] if slot_idx < len(files) else None
        return mapping

    def show_previous_layout_background(self):
        files = self.get_preview_background_files()
        if not files:
            return
        self.layout_choice_index = (self.layout_choice_index - 1) % len(files)
        self.update_preview()

    def show_next_layout_background(self):
        files = self.get_preview_background_files()
        if not files:
            return
        self.layout_choice_index = (self.layout_choice_index + 1) % len(files)
        self.update_preview()
    
    def get_required_background_count(self, subfolder_name, template_name=None):
        """Get the maximum number of background images based on template and subfolder."""
        if self.is_trading_cards_ai(template_name, subfolder_name):
            return 10

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
            self.template_combo.configure(values=[])
            self.subfolder_combo.configure(state="disabled", values=[])
            self.selected_subfolder.set("")
            self.preview_button.configure(state="disabled")
            self.set_status("Template folder not found", "error")
            return
        
        # Get all folders in the template directory
        templates = []
        try:
            for item in template_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    templates.append(item.name)
        except PermissionError:
            self.subfolder_combo.configure(state="disabled", values=[])
            self.selected_subfolder.set("")
            self.preview_button.configure(state="disabled")
            self.set_status("Permission denied accessing template folder", "error")
            return
        
        templates.sort()
        self.template_combo.configure(values=templates)
        
        if templates:
            self.set_status(f"Found {len(templates)} template(s)", "success")
        else:
            self.subfolder_combo.configure(state="disabled", values=[])
            self.selected_subfolder.set("")
            self.preview_button.configure(state="disabled")
            self.set_status("No templates found", "warning")
    
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
            self.subfolder_combo.configure(state="disabled", values=[])
            self.selected_subfolder.set("")
            self.preview_button.configure(state="disabled")
            # Hide background section
            self.background_frame.grid_remove()
            self.update_preview()
            return
        
        template_dir = Path(self.template_path.get())
        template_path = template_dir / template_name
        
        if not template_path.exists():
            self.subfolder_combo.configure(state="disabled", values=[])
            self.selected_subfolder.set("")
            self.preview_button.configure(state="disabled")
            # Hide background section
            self.background_frame.grid_remove()
            self.update_preview()
            return
        
        # Show/hide background section based on template and subfolder
        # We'll update this when subfolder is selected
        # For now, just hide it if template doesn't match
        if (
            "ai removal" in template_name.lower()
            or "greenscreen" in template_name.lower()
            or "trading card" in template_name.lower()
        ):
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
            self.subfolder_combo.configure(state="readonly", values=subfolders)
            self.set_status(f"Found {len(subfolders)} subfolder(s) in '{template_name}'", "success")
        else:
            self.subfolder_combo.configure(state="disabled", values=[])
            self.selected_subfolder.set("")
            self.set_status(f"No subfolders found in '{template_name}'", "warning")
            self.preview_button.configure(state="disabled")
        
        # Update path preview when template changes
        self.update_path_preview()
        self.update_preview()
    
    def on_subfolder_selected(self, event=None):
        """Enable preview button when subfolder is selected."""
        if self.selected_subfolder.get():
            self.preview_button.configure(state="normal")
        
        # Show/hide background section based on template and subfolder
        template_name = self.selected_template.get()
        subfolder_name = self.selected_subfolder.get()
        self.layout_choice_index = 0
        if self.should_show_background_section(template_name, subfolder_name):
            self.background_frame.grid()
            # Update label to show required count or indicate multiple allowed
            subfolder_lower = subfolder_name.lower() if subfolder_name else ""
            is_multi_background = (
                self.is_trading_cards_ai(template_name, subfolder_name)
                or "4x61" in subfolder_lower
                or "1 shot" in subfolder_lower
                or "1shot" in subfolder_lower
                or "1-shot" in subfolder_lower
            )
            if hasattr(self, 'background_label'):
                if self.is_trading_cards_ai(template_name, subfolder_name):
                    self.background_label.configure(text="Background Images (up to 10):")
                elif is_multi_background:
                    self.background_label.configure(text="Background Images (multiple allowed):")
                else:
                    required_count = self.get_required_background_count(subfolder_name, template_name)
                    self.background_label.configure(text=f"Background Images (required: {required_count}):")
            # Show overlay background section only for 3/4 shot patterns, not for 1 shot / trading cards
            if not is_multi_background:
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
        self.update_preview()
    
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
        
        # Update window geometry
        self.root.geometry(f"{self.window_width}x{height}")
    
    def get_overlay_preview_path(self):
        """Return custom overlay path or the template subfolder overlay PNG."""
        custom_overlay = self.overlay_file_path.get().strip()
        if custom_overlay:
            overlay_path = Path(custom_overlay)
            if overlay_path.exists() and overlay_path.is_file():
                return overlay_path

        template_name = self.selected_template.get()
        subfolder_name = self.selected_subfolder.get()
        if not template_name or not subfolder_name:
            return None

        template_overlay = (
            Path(self.template_path.get()) / template_name / subfolder_name / "overlay.png"
        )
        if template_overlay.exists() and template_overlay.is_file():
            return template_overlay

        return None

    def update_preview(self):
        """Update combined layout + overlay preview."""
        if not hasattr(self, 'preview_image_label'):
            return

        template_name = self.selected_template.get()
        subfolder_name = self.selected_subfolder.get()
        layout_key = self.get_layout_preview_key(template_name, subfolder_name)
        overlay_path = self.get_overlay_preview_path()
        uses_carousel = self.uses_background_choice_carousel(template_name, subfolder_name)
        background_files = self.get_preview_background_files()

        if uses_carousel and background_files:
            self.layout_choice_frame.grid()
            idx = self.layout_choice_index % len(background_files)
            self.layout_choice_counter.configure(text=f"Background {idx + 1} of {len(background_files)}")
        else:
            self.layout_choice_frame.grid_remove()

        if not layout_key and not overlay_path:
            self._preview_image = None
            self._preview_pil = None
            self.preview_image_label.configure(
                image=None,
                text="Select a template subfolder"
            )
            return

        try:
            composite = None
            if layout_key:
                layout_path = get_layout_previews_dir() / LAYOUT_PREVIEWS[layout_key]['file']
                if not layout_path.exists():
                    raise FileNotFoundError(f"Missing layout asset: {layout_path.name}")
                slot_map = (
                    self.build_slot_background_map(layout_key)
                    if self.should_preview_slot_backgrounds()
                    else {}
                )
                full_background_path = self.get_preview_overlay_background_path()
                if overlay_path:
                    composite = build_combined_preview(
                        layout_key,
                        layout_path,
                        slot_map,
                        overlay_path,
                        full_background_path=full_background_path,
                    )
                else:
                    composite = build_layout_composite(
                        layout_key,
                        layout_path,
                        slot_map,
                        full_background_path=full_background_path,
                    )
            elif overlay_path:
                composite = Image.open(overlay_path).convert('RGBA')

            if composite is None:
                raise ValueError("No preview available")

            max_w = self.preview_panel_width - 56
            max_h = 296
            composite.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            self._preview_pil = composite.copy()
            self._preview_image = ctk.CTkImage(
                light_image=self._preview_pil,
                dark_image=self._preview_pil,
                size=(self._preview_pil.width, self._preview_pil.height)
            )
            self.preview_image_label.configure(
                image=self._preview_image,
                text=""
            )
        except Exception as exc:
            self._preview_image = None
            self._preview_pil = None
            message = "Could not render preview"
            if isinstance(exc, FileNotFoundError):
                message = str(exc)
            self.preview_image_label.configure(
                image=None,
                text=message
            )
    
    def update_path_preview(self):
        """Update the path preview display based on current inputs."""
        self.update_template_choice_banner()
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
            self.path_preview.configure(text=str(full_path), text_color=self.colors['fg_text'])
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
                self.path_preview.configure(
                    text=f"Complete the following: {', '.join(missing)}",
                    text_color=self.colors['status_warning']
                )
            else:
                self.path_preview.configure(text="", text_color=self.colors['fg_text'])
    
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
        self.generate_button.configure(state="disabled")
        self.progress.start()
        self.set_status("Copying files...", "accent")
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
                        
                        uses_numbered_backgrounds = self.uses_background1_jpg_naming(template_name, subfolder_name)

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
                                
                                if uses_numbered_backgrounds:
                                    # For 4X6 1 shot / Trading Cards AI: copy as background1.jpg, background2.jpg, etc.
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
        self.generate_button.configure(state="normal")
        
        status_text = f"Successfully created '{folder_name}' ({file_count} files, {folder_count} folders)"
        if overlay_copied:
            status_text += " + overlay.png"
        if overlay_background_copied:
            status_text += " + background.jpg"
        if background_copied > 0:
            status_text += f" + {background_copied} background file(s)"
        self.set_status(status_text, "success")
        
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
                
                uses_numbered_backgrounds = self.uses_background1_jpg_naming(template_name, subfolder_name)
                is_3_4_shot = (
                    ("3 shot" in subfolder_lower or "3shot" in subfolder_lower or "3-shot" in subfolder_lower) or
                    ("4 shot" in subfolder_lower or "4shot" in subfolder_lower or "4-shot" in subfolder_lower)
                )
                
                if uses_numbered_backgrounds:
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
        self.generate_button.configure(state="normal")
        self.set_status("Error occurred", "error")
        messagebox.showerror("Error", error_msg)


def main():
    root = ctk.CTk()
    app = EventFolderGenerator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
