import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import os
import threading
import re
import sys
import platform
import shutil

IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

def subprocess_flags():
    """Return platform-appropriate subprocess creation flags."""
    if IS_WINDOWS:
        return subprocess.CREATE_NO_WINDOW
    return 0

class YtDlpGUI:
    def __init__(self, root):
        self.root = root
        
        def get_base_path():
            """Get the base directory of the application"""
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                return os.path.dirname(sys.executable)
            else:
                # Running as script
                return os.path.dirname(os.path.abspath(__file__))
        
        self.base_path = get_base_path()
        self.deps_path = os.path.join(self.base_path, "dependencies")
        
        def resource_path(relative_path):
            """Get absolute path to resource, works for dev and for PyInstaller"""
            try:
                # PyInstaller creates a temp folder and stores path in _MEIPASS
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")
            return os.path.join(base_path, relative_path)
        self.icon = tk.PhotoImage(file=resource_path("assets/logo.png"))
        self.root.iconphoto(False, self.icon)
        self.root.title("L's YouTube Downloader")
        self.root.geometry("1280x720")
        self.root.minsize(1280, 720)  # Set minimum size to prevent cutting off content
        self.root.configure(bg="#f0f0f0")
        
        # --- Button Styles ---
        style = ttk.Style()
        style.configure("Action.TButton",
                        font=("Arial", 10, "bold"),
                        padding=(16, 6))
        style.configure("Secondary.TButton",
                        font=("Arial", 9),
                        padding=(10, 4))
        
        # Configuration
        # Check for local ffmpeg first, then fall back to system paths
        local_ffmpeg = os.path.join(self.deps_path, "ffmpeg", "bin")
        if os.path.exists(local_ffmpeg):
            self.ffmpeg_location = local_ffmpeg
        elif IS_WINDOWS and os.path.exists("C:\\ffmpeg\\bin"):
            self.ffmpeg_location = "C:\\ffmpeg\\bin"
        else:
            # On Linux/macOS, ffmpeg is typically on PATH already
            ffmpeg_path = shutil.which("ffmpeg")
            self.ffmpeg_location = os.path.dirname(ffmpeg_path) if ffmpeg_path else ""
        
        # Find user's desktop path (cross-platform)
        if IS_WINDOWS:
            self.output_dir = os.path.join(os.environ.get('USERPROFILE', os.path.expanduser('~')), 'Desktop')
        else:
            self.output_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
            if not os.path.isdir(self.output_dir):
                self.output_dir = os.path.expanduser('~')
        
        # Track which widget should receive mousewheel events
        self._scroll_target = None
        
        # =====================================================================
        # TOP-LEVEL LAYOUT: Header -> Notebook (tabs) -> Console -> Status Bar
        # =====================================================================
        
        # --- Status Bar (pack BOTTOM first so it's always visible) ---
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # --- Header (shared across tabs) ---
        header_frame = ttk.Frame(root, padding=(15, 12, 15, 0))
        header_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(header_frame, text="L's YouTube Downloader", font=("Arial", 16, "bold"))
        title_label.pack(anchor=tk.W)
        
        # Output Directory (shared by both Downloader and Converter)
        output_dir_row = ttk.LabelFrame(header_frame, text="Output Directory")
        output_dir_row.pack(fill=tk.X, pady=(8, 0))
        
        output_dir_inner = ttk.Frame(output_dir_row)
        output_dir_inner.pack(fill=tk.X, padx=10, pady=6)
        
        self.output_dir_entry = ttk.Entry(output_dir_inner, width=70)
        self.output_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.output_dir_entry.insert(0, self.output_dir)
        
        browse_output_btn = ttk.Button(output_dir_inner, text="Browse...",
                                        command=self.browse_output_dir, style="Secondary.TButton")
        browse_output_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # --- Console Output (shared, pack before notebook so it claims space at bottom) ---
        console_frame = ttk.LabelFrame(root, text="Console Output")
        console_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=(0, 8))
        
        console_inner = ttk.Frame(console_frame)
        console_inner.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.console = tk.Text(console_inner, wrap=tk.WORD, bg="#1e1e1e", fg="#00FF00",
                               insertbackground="#00FF00", font=("Consolas", 9), height=12)
        self.console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        console_scroll = ttk.Scrollbar(console_inner, command=self.console.yview)
        console_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.console.config(yscrollcommand=console_scroll.set)
        
        # Console mousewheel: scrolls the console only, never the background
        def _console_mousewheel(event):
            self.console.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"
        self.console.bind("<MouseWheel>", _console_mousewheel)
        self.console.bind("<Enter>", lambda e: setattr(self, '_scroll_target', 'console'))
        self.console.bind("<Leave>", lambda e: setattr(self, '_scroll_target', None))
        
        # --- Notebook (tabs, fills remaining space between header and console) ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=(8, 8))
        
        # =============================================================
        # TAB 1: Downloader
        # =============================================================
        dl_tab = ttk.Frame(self.notebook)
        self.notebook.add(dl_tab, text="  Downloader  ")
        
        # Scrollable canvas for the downloader tab
        dl_canvas = tk.Canvas(dl_tab, bg="#f0f0f0", highlightthickness=0)
        dl_scrollbar = ttk.Scrollbar(dl_tab, orient="vertical", command=dl_canvas.yview)
        dl_frame = ttk.Frame(dl_canvas, padding=(15, 10))
        
        dl_frame.bind("<Configure>",
                      lambda e: dl_canvas.configure(scrollregion=dl_canvas.bbox("all")))
        dl_canvas_window = dl_canvas.create_window((0, 0), window=dl_frame, anchor="nw")
        dl_canvas.configure(yscrollcommand=dl_scrollbar.set)
        
        def _configure_dl_canvas(event):
            dl_canvas.itemconfig(dl_canvas_window, width=event.width)
            dl_canvas.configure(scrollregion=dl_canvas.bbox("all"))
        dl_canvas.bind("<Configure>", _configure_dl_canvas)
        
        dl_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        dl_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mousewheel for downloader canvas (only when hovering over it, not the console)
        def _dl_mousewheel(event):
            if self._scroll_target == 'console':
                return
            if dl_canvas.yview() != (0.0, 1.0):
                dl_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        dl_canvas.bind("<Enter>", lambda e: setattr(self, '_scroll_target', 'dl_canvas'))
        dl_canvas.bind("<Leave>", lambda e: setattr(self, '_scroll_target', None))
        
        def _global_mousewheel(event):
            if self._scroll_target == 'console':
                return
            if self._scroll_target == 'dl_canvas':
                _dl_mousewheel(event)
        root.bind_all("<MouseWheel>", _global_mousewheel)
        
        # --- YouTube URL ---
        url_frame = ttk.LabelFrame(dl_frame, text="YouTube URL")
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.url_entry = ttk.Entry(url_frame, width=70)
        self.url_entry.pack(fill=tk.X, padx=10, pady=8)
        
        # --- Options ---
        options_frame = ttk.LabelFrame(dl_frame, text="Options")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        age_frame = ttk.Frame(options_frame)
        age_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.age_limit_enabled = tk.BooleanVar(value=False)
        age_limit_check = ttk.Checkbutton(
            age_frame, text="Set Age Limit",
            variable=self.age_limit_enabled,
            command=self.update_age_limit_state
        )
        age_limit_check.pack(side=tk.LEFT)
        
        self.age_limit_inner = ttk.Frame(age_frame)
        self.age_limit_inner.pack(side=tk.LEFT, padx=(10, 0))
        
        self.age_limit_entry = ttk.Entry(self.age_limit_inner, width=6)
        self.age_limit_entry.pack(side=tk.LEFT)
        self.age_limit_entry.insert(0, "18")
        
        age_limit_unit = ttk.Label(self.age_limit_inner, text="years")
        age_limit_unit.pack(side=tk.LEFT, padx=(4, 0))
        
        age_limit_help = ttk.Label(
            age_frame, text="(videos above this age gate are skipped)",
            font=("Arial", 8), foreground="gray"
        )
        age_limit_help.pack(side=tk.LEFT, padx=(8, 0))
        
        self.update_age_limit_state()
        
        # --- Download Format ---
        format_frame = ttk.LabelFrame(dl_frame, text="Download Format")
        format_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.format_var = tk.StringVar(value="video")
        
        # Video row
        video_frame = ttk.Frame(format_frame)
        video_frame.pack(fill=tk.X, padx=10, pady=5)
        
        video_radio = ttk.Radiobutton(video_frame, text="Video", variable=self.format_var,
                                      value="video", command=self.update_format_selection)
        video_radio.grid(row=0, column=0, sticky=tk.W)
        
        self.video_format_var = tk.StringVar(value="mp4")
        self.video_formats_frame = ttk.Frame(video_frame)
        self.video_formats_frame.grid(row=0, column=1, padx=(20, 0))
        
        for fmt in ("MP4", "MKV", "WEBM", "AVI", "MOV"):
            ttk.Radiobutton(self.video_formats_frame, text=fmt,
                            variable=self.video_format_var,
                            value=fmt.lower()).pack(side=tk.LEFT, padx=10)
        
        # Audio row
        audio_frame = ttk.Frame(format_frame)
        audio_frame.pack(fill=tk.X, padx=10, pady=5)
        
        audio_radio = ttk.Radiobutton(audio_frame, text="Audio", variable=self.format_var,
                                      value="audio", command=self.update_format_selection)
        audio_radio.grid(row=0, column=0, sticky=tk.W)
        
        self.audio_format_var = tk.StringVar(value="mp3")
        self.audio_formats_frame = ttk.Frame(audio_frame)
        self.audio_formats_frame.grid(row=0, column=1, padx=(20, 0))
        
        for fmt in ("MP3", "AAC", "M4A", "OPUS", "FLAC", "WAV", "OGG", "ALAC"):
            ttk.Radiobutton(self.audio_formats_frame, text=fmt,
                            variable=self.audio_format_var,
                            value=fmt.lower()).pack(side=tk.LEFT, padx=10)
        
        self.update_format_selection()
        
        # --- Compression ---
        compression_frame = ttk.LabelFrame(dl_frame, text="Compression (Optional)")
        compression_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.compression_enabled = tk.BooleanVar(value=False)
        compression_check = ttk.Checkbutton(compression_frame, text="Enable Compression",
                                            variable=self.compression_enabled,
                                            command=self.update_compression_state)
        compression_check.pack(anchor=tk.W, padx=10, pady=(5, 10))
        
        self.compression_mode_var = tk.StringVar(value="simple")
        
        mode_frame = ttk.Frame(compression_frame)
        mode_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        ttk.Radiobutton(mode_frame, text="Simple Mode (Presets)",
                        variable=self.compression_mode_var, value="simple",
                        command=self.update_compression_mode).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Advanced Mode (Custom Settings)",
                        variable=self.compression_mode_var, value="advanced",
                        command=self.update_compression_mode).pack(anchor=tk.W)
        
        # Simple Mode
        self.simple_frame = ttk.Frame(compression_frame)
        self.simple_frame.pack(fill=tk.X, padx=30, pady=(5, 10))
        
        ttk.Label(self.simple_frame, text="Preset:").pack(anchor=tk.W)
        
        self.preset_var = tk.StringVar(value="discord_8mb")
        preset_combo = ttk.Combobox(self.simple_frame, textvariable=self.preset_var,
                                    state="readonly", width=40)
        preset_combo['values'] = (
            'Discord 8MB (Video)',
            'Discord 25MB (Nitro Classic)',
            'Discord 50MB (Nitro)',
            'Discord 100MB (Nitro Boost)',
            'Twitter/X 512MB',
            'Instagram 100MB',
            'WhatsApp 16MB',
            'Telegram 2GB'
        )
        preset_combo.current(0)
        preset_combo.pack(fill=tk.X, pady=(5, 0))
        
        # Advanced Mode
        self.advanced_frame = ttk.Frame(compression_frame)
        self.advanced_frame.pack(fill=tk.X, padx=30, pady=(5, 10))
        
        target_size_frame = ttk.Frame(self.advanced_frame)
        target_size_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(target_size_frame, text="Target File Size (MB):").pack(side=tk.LEFT)
        self.target_size_entry = ttk.Entry(target_size_frame, width=15)
        self.target_size_entry.pack(side=tk.LEFT, padx=(10, 0))
        self.target_size_entry.insert(0, "8")
        
        video_bitrate_frame = ttk.Frame(self.advanced_frame)
        video_bitrate_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(video_bitrate_frame, text="Video Bitrate (kbps):").pack(side=tk.LEFT)
        self.video_bitrate_entry = ttk.Entry(video_bitrate_frame, width=15)
        self.video_bitrate_entry.pack(side=tk.LEFT, padx=(10, 0))
        self.video_bitrate_entry.insert(0, "500")
        ttk.Label(video_bitrate_frame, text="(Leave empty to auto-calculate from file size)",
                  font=("Arial", 8), foreground="gray").pack(side=tk.LEFT, padx=(10, 0))
        
        audio_bitrate_frame = ttk.Frame(self.advanced_frame)
        audio_bitrate_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(audio_bitrate_frame, text="Audio Bitrate (kbps):").pack(side=tk.LEFT)
        self.audio_bitrate_entry = ttk.Entry(audio_bitrate_frame, width=15)
        self.audio_bitrate_entry.pack(side=tk.LEFT, padx=(10, 0))
        self.audio_bitrate_entry.insert(0, "128")
        
        self.update_compression_state()
        
        # --- Downloader Action Bar ---
        dl_action_frame = ttk.Frame(dl_frame)
        dl_action_frame.pack(fill=tk.X, pady=(5, 10))
        
        self.download_button = ttk.Button(dl_action_frame, text="Download",
                                            command=self.start_download, style="Action.TButton")
        self.download_button.pack(side=tk.LEFT)
        
        help_button = ttk.Button(dl_action_frame, text="Format Guide",
                                 command=self.show_format_guide, style="Secondary.TButton")
        help_button.pack(side=tk.RIGHT)
        
        # =============================================================
        # TAB 2: File Converter
        # =============================================================
        conv_tab = ttk.Frame(self.notebook)
        self.notebook.add(conv_tab, text="  File Converter  ")
        
        # Scrollable canvas for the converter tab
        conv_canvas = tk.Canvas(conv_tab, bg="#f0f0f0", highlightthickness=0)
        conv_scrollbar = ttk.Scrollbar(conv_tab, orient="vertical", command=conv_canvas.yview)
        conv_frame = ttk.Frame(conv_canvas, padding=(15, 10))
        
        conv_frame.bind("<Configure>",
                        lambda e: conv_canvas.configure(scrollregion=conv_canvas.bbox("all")))
        conv_canvas_window = conv_canvas.create_window((0, 0), window=conv_frame, anchor="nw")
        conv_canvas.configure(yscrollcommand=conv_scrollbar.set)
        
        def _configure_conv_canvas(event):
            conv_canvas.itemconfig(conv_canvas_window, width=event.width)
            conv_canvas.configure(scrollregion=conv_canvas.bbox("all"))
        conv_canvas.bind("<Configure>", _configure_conv_canvas)
        
        conv_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        conv_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mousewheel for converter canvas
        def _conv_mousewheel(event):
            if self._scroll_target == 'console':
                return
            if conv_canvas.yview() != (0.0, 1.0):
                conv_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        conv_canvas.bind("<Enter>", lambda e: setattr(self, '_scroll_target', 'conv_canvas'))
        conv_canvas.bind("<Leave>", lambda e: setattr(self, '_scroll_target', None))
        
        # Update global mousewheel handler to include converter canvas
        def _global_mousewheel_updated(event):
            if self._scroll_target == 'console':
                return
            if self._scroll_target == 'dl_canvas':
                _dl_mousewheel(event)
            elif self._scroll_target == 'conv_canvas':
                _conv_mousewheel(event)
        root.bind_all("<MouseWheel>", _global_mousewheel_updated)
        
        # Input file
        input_frame = ttk.LabelFrame(conv_frame, text="Input File")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        input_row = ttk.Frame(input_frame)
        input_row.pack(fill=tk.X, padx=10, pady=8)
        
        self.converter_input_entry = ttk.Entry(input_row, width=60)
        self.converter_input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(input_row, text="Browse...",
                   command=self.browse_converter_input,
                   style="Secondary.TButton").pack(side=tk.LEFT, padx=(5, 0))
        
        # Output format
        format_conv_frame = ttk.LabelFrame(conv_frame, text="Output Format")
        format_conv_frame.pack(fill=tk.X, pady=(0, 10))
        
        format_conv_inner = ttk.Frame(format_conv_frame)
        format_conv_inner.pack(fill=tk.X, padx=10, pady=8)
        
        self.converter_format_var = tk.StringVar(value="mp4")
        converter_format_combo = ttk.Combobox(
            format_conv_inner, textvariable=self.converter_format_var,
            state="readonly", width=20
        )
        converter_format_combo['values'] = (
            'mp4', 'mkv', 'webm', 'avi', 'mov',
            'mp3', 'aac', 'm4a', 'opus', 'flac', 'wav', 'ogg', 'alac'
        )
        converter_format_combo.pack(side=tk.LEFT)
        
        ttk.Label(format_conv_inner,
                  text="Supports video-to-video, audio-to-audio, and video-to-audio conversion.",
                  font=("Arial", 8), foreground="gray").pack(side=tk.LEFT, padx=(12, 0))
        
        # --- Converter Compression (mirrors Downloader compression) ---
        conv_compress_frame = ttk.LabelFrame(conv_frame, text="Compression (Optional)")
        conv_compress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.conv_compress_enabled = tk.BooleanVar(value=False)
        conv_compress_check = ttk.Checkbutton(
            conv_compress_frame, text="Enable Compression",
            variable=self.conv_compress_enabled,
            command=self.update_conv_compress_state
        )
        conv_compress_check.pack(anchor=tk.W, padx=10, pady=(5, 10))
        
        self.conv_compress_mode_var = tk.StringVar(value="simple")
        
        conv_mode_frame = ttk.Frame(conv_compress_frame)
        conv_mode_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        ttk.Radiobutton(conv_mode_frame, text="Simple Mode (Presets)",
                        variable=self.conv_compress_mode_var, value="simple",
                        command=self.update_conv_compress_mode).pack(anchor=tk.W)
        ttk.Radiobutton(conv_mode_frame, text="Advanced Mode (Custom Settings)",
                        variable=self.conv_compress_mode_var, value="advanced",
                        command=self.update_conv_compress_mode).pack(anchor=tk.W)
        
        # Simple Mode
        self.conv_simple_frame = ttk.Frame(conv_compress_frame)
        self.conv_simple_frame.pack(fill=tk.X, padx=30, pady=(5, 10))
        
        ttk.Label(self.conv_simple_frame, text="Preset:").pack(anchor=tk.W)
        
        self.conv_preset_var = tk.StringVar(value="Discord 8MB (Video)")
        conv_preset_combo = ttk.Combobox(self.conv_simple_frame, textvariable=self.conv_preset_var,
                                         state="readonly", width=40)
        conv_preset_combo['values'] = (
            'Discord 8MB (Video)',
            'Discord 25MB (Nitro Classic)',
            'Discord 50MB (Nitro)',
            'Discord 100MB (Nitro Boost)',
            'Twitter/X 512MB',
            'Instagram 100MB',
            'WhatsApp 16MB',
            'Telegram 2GB'
        )
        conv_preset_combo.current(0)
        conv_preset_combo.pack(fill=tk.X, pady=(5, 0))
        
        # Advanced Mode
        self.conv_advanced_frame = ttk.Frame(conv_compress_frame)
        self.conv_advanced_frame.pack(fill=tk.X, padx=30, pady=(5, 10))
        
        conv_target_frame = ttk.Frame(self.conv_advanced_frame)
        conv_target_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(conv_target_frame, text="Target File Size (MB):").pack(side=tk.LEFT)
        self.conv_target_size_entry = ttk.Entry(conv_target_frame, width=15)
        self.conv_target_size_entry.pack(side=tk.LEFT, padx=(10, 0))
        self.conv_target_size_entry.insert(0, "8")
        
        conv_vbitrate_frame = ttk.Frame(self.conv_advanced_frame)
        conv_vbitrate_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(conv_vbitrate_frame, text="Video Bitrate (kbps):").pack(side=tk.LEFT)
        self.conv_video_bitrate_entry = ttk.Entry(conv_vbitrate_frame, width=15)
        self.conv_video_bitrate_entry.pack(side=tk.LEFT, padx=(10, 0))
        self.conv_video_bitrate_entry.insert(0, "500")
        ttk.Label(conv_vbitrate_frame, text="(Leave empty to auto-calculate from file size)",
                  font=("Arial", 8), foreground="gray").pack(side=tk.LEFT, padx=(10, 0))
        
        conv_abitrate_frame = ttk.Frame(self.conv_advanced_frame)
        conv_abitrate_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(conv_abitrate_frame, text="Audio Bitrate (kbps):").pack(side=tk.LEFT)
        self.conv_audio_bitrate_entry = ttk.Entry(conv_abitrate_frame, width=15)
        self.conv_audio_bitrate_entry.pack(side=tk.LEFT, padx=(10, 0))
        self.conv_audio_bitrate_entry.insert(0, "128")
        
        self.update_conv_compress_state()
        
        # Convert button
        self.convert_button = ttk.Button(conv_frame, text="Convert",
                                         command=self.start_conversion, style="Action.TButton")
        self.convert_button.pack(anchor=tk.W, pady=(5, 0))
    
    def update_age_limit_state(self):
        """Show/hide the age limit entry"""
        if self.age_limit_enabled.get():
            self.age_limit_inner.pack(side=tk.LEFT, padx=(10, 0))
        else:
            self.age_limit_inner.pack_forget()
    
    def update_conv_compress_state(self):
        """Enable/disable converter compression options based on checkbox"""
        state = "normal" if self.conv_compress_enabled.get() else "disabled"
        
        for frame in (self.conv_simple_frame, self.conv_advanced_frame):
            for child in frame.winfo_children():
                if isinstance(child, (ttk.Combobox, ttk.Entry, ttk.Radiobutton)):
                    child.configure(state=state)
                elif isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, (ttk.Combobox, ttk.Entry, ttk.Radiobutton)):
                            subchild.configure(state=state)
        
        self.update_conv_compress_mode()
    
    def update_conv_compress_mode(self):
        """Show/hide converter compression mode frames based on selection"""
        if not self.conv_compress_enabled.get():
            self.conv_simple_frame.pack_forget()
            self.conv_advanced_frame.pack_forget()
        elif self.conv_compress_mode_var.get() == "simple":
            self.conv_advanced_frame.pack_forget()
            self.conv_simple_frame.pack(fill=tk.X, padx=30, pady=(5, 10))
        else:
            self.conv_simple_frame.pack_forget()
            self.conv_advanced_frame.pack(fill=tk.X, padx=30, pady=(5, 10))
    
    def get_conv_compression_settings(self, duration=None):
        """Calculate converter compression settings (mirrors get_compression_settings)."""
        if not self.conv_compress_enabled.get():
            return None
        
        if self.conv_compress_mode_var.get() == "simple":
            preset = self.conv_preset_var.get()
            
            preset_map = {
                'Discord 8MB (Video)': (8, 96),
                'Discord 25MB (Nitro Classic)': (25, 128),
                'Discord 50MB (Nitro)': (50, 128),
                'Discord 100MB (Nitro Boost)': (100, 192),
                'Twitter/X 512MB': (512, 192),
                'Instagram 100MB': (100, 192),
                'WhatsApp 16MB': (16, 96),
                'Telegram 2GB': (2048, 256)
            }
            
            target_size_mb, audio_bitrate = preset_map.get(preset, (8, 96))
            est = duration if duration else 180
            video_bitrate = self.calculate_bitrates_for_target_size(target_size_mb, est, audio_bitrate)
            
            return {
                'target_size': target_size_mb,
                'video_bitrate': video_bitrate,
                'audio_bitrate': audio_bitrate
            }
        else:
            try:
                target_size = float(self.conv_target_size_entry.get() or "8")
                video_bitrate_str = self.conv_video_bitrate_entry.get().strip()
                audio_bitrate = int(self.conv_audio_bitrate_entry.get() or "128")
                
                if video_bitrate_str:
                    video_bitrate = int(video_bitrate_str)
                else:
                    est = duration if duration else 180
                    video_bitrate = self.calculate_bitrates_for_target_size(target_size, est, audio_bitrate)
                
                return {
                    'target_size': target_size,
                    'video_bitrate': video_bitrate,
                    'audio_bitrate': audio_bitrate
                }
            except ValueError:
                self.update_console("Warning: Invalid compression settings, using defaults")
                return {
                    'target_size': 8,
                    'video_bitrate': 500,
                    'audio_bitrate': 96
                }
    
    def browse_output_dir(self):
        """Open folder dialog to select the output directory"""
        directory = filedialog.askdirectory(title="Select Output Directory", initialdir=self.output_dir_entry.get())
        if directory:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, directory)
    
    def browse_converter_input(self):
        """Open file dialog to select the input file for conversion"""
        filetypes = [
            ("Media Files", "*.mp4 *.mkv *.webm *.avi *.mov *.mp3 *.aac *.m4a *.opus *.flac *.wav *.ogg *.alac *.wma *.wmv *.ts *.flv"),
            ("All Files", "*.*")
        ]
        filepath = filedialog.askopenfilename(title="Select Input File", filetypes=filetypes)
        if filepath:
            self.converter_input_entry.delete(0, tk.END)
            self.converter_input_entry.insert(0, filepath)
    
    def start_conversion(self):
        """Start the local file conversion process"""
        input_path = self.converter_input_entry.get().strip()
        if not input_path:
            messagebox.showerror("Error", "Please select an input file.")
            return
        if not os.path.isfile(input_path):
            messagebox.showerror("Error", "The selected input file does not exist.")
            return
        
        if not self.update_output_directory():
            return
        
        output_format = self.converter_format_var.get()
        input_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(self.output_dir, f"{input_name}.{output_format}")
        
        # Prevent overwriting the input file
        if os.path.abspath(input_path) == os.path.abspath(output_path):
            messagebox.showerror("Error", "Output format is the same as input. Choose a different format.")
            return
        
        # Clear console and disable buttons
        self.console.delete(1.0, tk.END)
        self.convert_button.config(state=tk.DISABLED)
        self.download_button.config(state=tk.DISABLED)
        self.status_var.set("Converting...")
        
        target_size_mb = self.get_conv_compression_settings()
        threading.Thread(target=self.run_conversion,
                         args=(input_path, output_path, output_format, target_size_mb),
                         daemon=True).start()
    
    def get_media_duration(self, filepath):
        """Get the duration of a media file in seconds using ffprobe."""
        try:
            if self.ffmpeg_location:
                probe = os.path.join(self.ffmpeg_location, "ffprobe.exe" if IS_WINDOWS else "ffprobe")
                if not os.path.isfile(probe):
                    probe = "ffprobe"
            else:
                probe = "ffprobe"
            
            result = subprocess.run(
                [probe, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", filepath],
                capture_output=True, text=True, creationflags=subprocess_flags()
            )
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except Exception:
            pass
        return None
    
    def run_conversion(self, input_path, output_path, output_format, compression=None):
        """Run ffmpeg conversion in a separate thread.
        compression: dict with 'target_size', 'video_bitrate', 'audio_bitrate' or None."""
        try:
            # Determine ffmpeg executable path
            if self.ffmpeg_location:
                ffmpeg_exe = os.path.join(self.ffmpeg_location, "ffmpeg") if not IS_WINDOWS else os.path.join(self.ffmpeg_location, "ffmpeg.exe")
                if not os.path.isfile(ffmpeg_exe):
                    ffmpeg_exe = "ffmpeg"
            else:
                ffmpeg_exe = "ffmpeg"
            
            audio_only_formats = ('mp3', 'aac', 'm4a', 'opus', 'flac', 'wav', 'ogg', 'alac')
            is_audio_output = output_format in audio_only_formats
            duration = None
            skip_compression_due_to_size = False
            
            # --- File-size guard: skip compression if file is already under target ---
            if compression:
                target_size_mb = compression['target_size']
                input_size_bytes = os.path.getsize(input_path)
                input_size_mb = input_size_bytes / (1024 * 1024)
                
                if input_size_mb <= target_size_mb:
                    self.update_console("=" * 50)
                    self.update_console(f"Input file is already {input_size_mb:.1f}MB, which is")
                    self.update_console(f"under the {target_size_mb}MB target. Using stream copy")
                    self.update_console(f"to avoid unnecessary re-encoding and size bloat.")
                    self.update_console("=" * 50)
                    compression = None
                    skip_compression_due_to_size = True
                else:
                    # Recalculate bitrates with actual file duration for accuracy
                    duration = self.get_media_duration(input_path)
                    if not duration or duration <= 0:
                        self.update_console("Warning: Could not determine duration, estimating 3 minutes.")
                        duration = 180
                    compression = self.get_conv_compression_settings(duration)
            
            cmd = [ffmpeg_exe, "-i", input_path, "-y"]
            
            # --- Compression path: use pre-calculated bitrates ---
            if compression and not is_audio_output:
                video_bitrate = compression['video_bitrate']
                audio_bitrate = compression['audio_bitrate']
                target_size_mb = compression['target_size']
                
                # Re-use cached duration if available, otherwise fetch
                if not duration or duration <= 0:
                    duration = self.get_media_duration(input_path) or 180
                
                self.update_console("=" * 50)
                self.update_console(f"COMPRESSING to ~{target_size_mb}MB")
                self.update_console(f"Duration: {int(duration // 60)}m {int(duration % 60)}s")
                self.update_console(f"Video bitrate: {video_bitrate}kbps  |  Audio bitrate: {audio_bitrate}kbps")
                self.update_console("=" * 50)
                
                # Format-specific compressed encoding
                if output_format == "webm":
                    cmd.extend(['-c:v', 'libvpx-vp9',
                                '-b:v', f'{video_bitrate}k', '-maxrate', f'{video_bitrate}k',
                                '-bufsize', f'{video_bitrate * 2}k',
                                '-c:a', 'libopus', '-b:a', f'{audio_bitrate}k', '-ar', '48000'])
                else:
                    cmd.extend(['-c:v', 'libx264',
                                '-b:v', f'{video_bitrate}k', '-maxrate', f'{video_bitrate}k',
                                '-bufsize', f'{video_bitrate * 2}k', '-preset', 'medium',
                                '-c:a', 'aac', '-b:a', f'{audio_bitrate}k', '-ar', '48000'])
            elif is_audio_output:
                # Audio output: strip video, encode audio
                cmd.append("-vn")
                if compression:
                    # Compressed audio: calculate bitrate from target size and duration
                    if not duration:
                        duration = self.get_media_duration(input_path)
                        if not duration or duration <= 0:
                            duration = 180
                    audio_kbps = max(32, int((compression['target_size'] * 8192) / duration * 0.98))
                    self.update_console(f"Compressing audio to ~{compression['target_size']}MB ({audio_kbps}kbps)")
                    codec_map = {
                        'mp3': ['-c:a', 'libmp3lame'], 'aac': ['-c:a', 'aac'],
                        'm4a': ['-c:a', 'aac'], 'opus': ['-c:a', 'libopus'],
                        'ogg': ['-c:a', 'libvorbis'],
                    }
                    cmd.extend(codec_map.get(output_format, ['-c:a', 'libmp3lame']))
                    cmd.extend(['-b:a', f'{audio_kbps}k'])
                else:
                    codec_map = {
                        'mp3': ['-c:a', 'libmp3lame', '-b:a', '320k'],
                        'aac': ['-c:a', 'aac', '-b:a', '320k'],
                        'm4a': ['-c:a', 'aac', '-b:a', '320k'],
                        'opus': ['-c:a', 'libopus', '-b:a', '320k'],
                        'flac': ['-c:a', 'flac'],
                        'wav': ['-c:a', 'pcm_s16le'],
                        'ogg': ['-c:a', 'libvorbis', '-b:a', '320k'],
                        'alac': ['-c:a', 'alac'],
                    }
                    cmd.extend(codec_map.get(output_format, ['-c:a', 'copy']))
            else:
                # Video output without compression: use stream copy if skipped due to size, otherwise high quality
                if skip_compression_due_to_size:
                    cmd.extend(['-c:v', 'copy', '-c:a', 'copy'])
                else:
                    codec_map = {
                        'mp4': ['-c:v', 'libx264', '-crf', '18', '-preset', 'slow', '-c:a', 'aac', '-b:a', '320k'],
                        'mkv': ['-c:v', 'copy', '-c:a', 'copy'],
                        'webm': ['-c:v', 'libvpx-vp9', '-crf', '30', '-b:v', '0', '-c:a', 'libopus', '-b:a', '320k'],
                        'avi': ['-c:v', 'copy', '-c:a', 'mp3', '-b:a', '320k'],
                        'mov': ['-c:v', 'libx264', '-crf', '18', '-preset', 'slow', '-c:a', 'aac', '-b:a', '320k'],
                    }
                    cmd.extend(codec_map.get(output_format, ['-c:v', 'copy', '-c:a', 'copy']))
            
            cmd.append(output_path)
            
            self.update_console(f"Converting: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
            self.update_console(f"Running: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess_flags()
            )
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.update_console(output.strip())
            
            if process.poll() == 0:
                self.update_console(f"\nConversion completed successfully!")
                self.update_console(f"Output: {output_path}")
                self.status_var.set("Conversion completed")
            else:
                self.update_console(f"\nConversion failed with return code: {process.poll()}")
                self.status_var.set("Conversion failed")
        except Exception as e:
            self.update_console(f"Error: {str(e)}")
            self.status_var.set("Error occurred")
        finally:
            self.convert_button.config(state=tk.NORMAL)
            self.download_button.config(state=tk.NORMAL)
    
    def update_format_selection(self):
        """Update UI based on selected format option"""
        # Enable/disable format options based on the selected main format
        if self.format_var.get() == "video":
            # Enable video format options when video is selected
            for child in self.video_formats_frame.winfo_children():
                child.configure(state="normal")
            # Disable audio format options when video is selected
            for child in self.audio_formats_frame.winfo_children():
                child.configure(state="disabled")
        else:
            # Disable video format options when audio is selected
            for child in self.video_formats_frame.winfo_children():
                child.configure(state="disabled")
            # Enable audio format options when audio is selected
            for child in self.audio_formats_frame.winfo_children():
                child.configure(state="normal")
    
    def update_compression_state(self):
        """Enable/disable compression options based on checkbox"""
        state = "normal" if self.compression_enabled.get() else "disabled"
        
        # Update all compression controls
        for child in self.simple_frame.winfo_children():
            if isinstance(child, (ttk.Combobox, ttk.Entry, ttk.Radiobutton)):
                child.configure(state=state)
            elif isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, (ttk.Combobox, ttk.Entry, ttk.Radiobutton)):
                        subchild.configure(state=state)
        
        for child in self.advanced_frame.winfo_children():
            if isinstance(child, (ttk.Combobox, ttk.Entry, ttk.Radiobutton)):
                child.configure(state=state)
            elif isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, (ttk.Combobox, ttk.Entry, ttk.Radiobutton)):
                        subchild.configure(state=state)
        
        # Update mode-specific frames
        self.update_compression_mode()
    
    def update_compression_mode(self):
        """Show/hide compression mode frames based on selection"""
        if not self.compression_enabled.get():
            self.simple_frame.pack_forget()
            self.advanced_frame.pack_forget()
        elif self.compression_mode_var.get() == "simple":
            self.advanced_frame.pack_forget()
            self.simple_frame.pack(fill=tk.X, padx=30, pady=(5, 10))
        else:
            self.simple_frame.pack_forget()
            self.advanced_frame.pack(fill=tk.X, padx=30, pady=(5, 10))

    def show_format_guide(self):
        """Display format guide in a popup window"""
        guide_window = tk.Toplevel(self.root)
        guide_window.title("Format Guide")
        guide_window.geometry("700x400")
        guide_window.resizable(False, False)
        
        # Main frame
        frame = ttk.Frame(guide_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(frame, text="Format Guide", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 10), yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Format guide content
        format_guide = """VIDEO FORMATS:

• MP4 (MPEG-4)
  Best for: Universal compatibility, sharing, social media
  Quality: Excellent
  File size: Medium
  Notes: Most widely supported format, plays on virtually all devices and platforms

• MKV (Matroska)
  Best for: High-quality archiving, multiple audio tracks/subtitles
  Quality: Excellent (supports highest quality)
  File size: Large
  Notes: Popular for video enthusiasts, supports advanced features

• WEBM
  Best for: Web streaming, online video
  Quality: Very good
  File size: Small to medium
  Notes: Optimized for web browsers, efficient compression

• AVI (Audio Video Interleave)
  Best for: Legacy compatibility, older systems
  Quality: Good
  File size: Large
  Notes: Older format with wide support, less efficient compression

• MOV (QuickTime)
  Best for: Apple devices, professional video editing
  Quality: Excellent
  File size: Medium to large
  Notes: Native format for Apple ecosystem, good for editing


AUDIO FORMATS:

• MP3 (MPEG Audio Layer 3)
  Best for: Universal audio playback, music libraries
  Quality: Good (lossy compression)
  File size: Small
  Notes: Most compatible audio format, plays everywhere

• AAC (Advanced Audio Coding)
  Best for: Better quality than MP3 at same bitrate
  Quality: Very good (lossy compression)
  File size: Small
  Notes: Modern successor to MP3, used by Apple and YouTube

• M4A (MPEG-4 Audio)
  Best for: Apple devices, iTunes
  Quality: Very good (lossy compression)
  File size: Small
  Notes: Container format for AAC, excellent Apple compatibility

• OPUS
  Best for: Modern applications, VoIP, streaming
  Quality: Excellent (lossy compression, best efficiency)
  File size: Very small
  Notes: Most efficient modern codec, excellent quality-to-size ratio

• FLAC (Free Lossless Audio Codec)
  Best for: Audiophiles, music archiving
  Quality: Perfect (lossless)
  File size: Large (50-60% of original)
  Notes: No quality loss, perfect reproduction of original

• WAV (Waveform Audio)
  Best for: Professional audio, editing
  Quality: Perfect (uncompressed)
  File size: Very large
  Notes: Uncompressed audio, used in professional settings

• OGG (Ogg Vorbis)
  Best for: Open-source applications, gaming
  Quality: Very good (lossy compression)
  File size: Small
  Notes: Free and open-source alternative to MP3

• ALAC (Apple Lossless)
  Best for: Apple ecosystem with lossless quality
  Quality: Perfect (lossless)
  File size: Large (similar to FLAC)
  Notes: Apple's lossless format, perfect for iTunes/Apple Music"""
        
        text_widget.insert(1.0, format_guide)
        text_widget.config(state=tk.DISABLED)  # Make read-only
        
        # Close button
        close_button = ttk.Button(frame, text="Close", command=guide_window.destroy,
                                   style="Secondary.TButton")
        close_button.pack(pady=(15, 0))

    def update_output_directory(self):
        """Update the output directory based on user input. Returns True if directory is valid, False otherwise."""
        self.output_dir = self.output_dir_entry.get().strip()
        if not os.path.isdir(self.output_dir):
            response = messagebox.askyesno("Info", "The specified output directory does not exist. Do you want to create it?")
            if response:
                os.makedirs(self.output_dir)
                return True
            else:
                self.output_dir_entry.focus_set()
                return False
        return True
    
    def validate_url(self, url):
        """Basic validation for YouTube URLs"""
        pattern = r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$'
        return bool(re.match(pattern, url))
    
    def update_console(self, text):
        """Update the console with new text"""
        self.console.insert(tk.END, text + "\n")
        self.console.see(tk.END)  # Auto-scroll to the end
        self.root.update_idletasks()
    
    def start_download(self):
        """Start the download process"""
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
        
        if not self.validate_url(url):
            messagebox.showwarning("Warning", "URL does not appear to be a valid YouTube URL")    
            return
        
        # Clear console
        self.console.delete(1.0, tk.END)
        
        # Disable download button during download
        self.download_button.config(state=tk.DISABLED)
        self.status_var.set("Downloading...")
        
        # Start download in a separate thread
        threading.Thread(target=self.run_download, args=(url,), daemon=True).start()
    
    def run_download(self, url):
        """Run the yt-dlp command in a separate thread"""
        try:
            # Update output directory from the entry field
            if not self.update_output_directory():
                self.status_var.set("Download cancelled")
                self.download_button.config(state=tk.NORMAL)
                return
            
            # Build the command based on selected options
            cmd = self.build_command(url)
            
            self.update_console(f"Running command: {' '.join(cmd)}")
            
            # Run the command and capture output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess_flags()
            )
            
            # Stream the output
            merge_notified = False
            compress_notified = False
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    output_lower = output.lower()
                    
                    # Notify user about merging/processing stages
                    if not merge_notified and ('merging' in output_lower or 'muxing' in output_lower):
                        self.update_console("\n" + "=" * 60)
                        self.update_console("MERGING VIDEO AND AUDIO STREAMS...")
                        if self.compression_enabled.get():
                            self.update_console("This may take several minutes due to compression.")
                        self.update_console("=" * 60 + "\n")
                        merge_notified = True
                    
                    if not compress_notified and self.compression_enabled.get() and \
                       ('destination' in output_lower or 'post-process' in output_lower):
                        self.update_console("\n" + "=" * 60)
                        self.update_console("COMPRESSING VIDEO TO TARGET SIZE...")
                        self.update_console("Please wait - this process cannot be rushed.")
                        self.update_console("FFmpeg is re-encoding the video.")
                        self.update_console("=" * 60 + "\n")
                        compress_notified = True
                    
                    self.update_console(output.strip())
            
            return_code = process.poll()
            
            if return_code == 0:
                self.update_console("Download completed successfully!")
                self.status_var.set("Download completed")
            else:
                self.update_console(f"Download failed with return code: {return_code}")
                self.status_var.set("Download failed")
                
        except Exception as e:
            self.update_console(f"Error: {str(e)}")
            self.status_var.set("Error occurred")
            
        finally:
            # Re-enable download button
            self.download_button.config(state=tk.NORMAL)
    
    def map_audio_format(self, format_name):
        """Map UI audio format names to yt-dlp format strings"""
        format_map = {
            'ogg': 'vorbis',  # OGG container uses Vorbis codec
            'alac': 'alac',
            'mp3': 'mp3',
            'aac': 'aac',
            'm4a': 'm4a',
            'opus': 'opus',
            'flac': 'flac',
            'wav': 'wav'
        }
        return format_map.get(format_name, format_name)
    
    def get_video_duration(self, url):
        """Fetch video duration in seconds"""
        try:
            ytdlp_cmd = self.find_ytdlp()
            
            self.update_console("Fetching video information to calculate compression...")
            
            # Get video duration
            result = subprocess.run(
                [ytdlp_cmd, "--print", "duration", url],
                capture_output=True,
                text=True,
                creationflags=subprocess_flags()
            )
            
            if result.returncode == 0 and result.stdout.strip():
                duration = float(result.stdout.strip())
                self.update_console(f"Video duration: {int(duration // 60)}m {int(duration % 60)}s")
                return duration
            else:
                self.update_console("Warning: Could not fetch duration, using 3 minute estimate")
                return 180  # Default to 3 minutes
        except Exception as e:
            self.update_console(f"Warning: Error fetching duration ({str(e)}), using 3 minute estimate")
            return 180
    
    def calculate_bitrates_for_target_size(self, target_size_mb, duration_seconds, audio_bitrate_kbps):
        """Calculate video bitrate needed to achieve target file size"""
        # Convert target size to kilobits
        target_size_kbits = target_size_mb * 8192  # 1 MB = 8192 kilobits
        
        # Calculate total bitrate needed
        total_bitrate_kbps = target_size_kbits / duration_seconds
        
        # Subtract audio bitrate to get video bitrate
        # Add small overhead for container (about 2%)
        overhead_factor = 0.98
        video_bitrate_kbps = (total_bitrate_kbps - audio_bitrate_kbps) * overhead_factor
        
        # Ensure minimum viable bitrate
        video_bitrate_kbps = max(100, int(video_bitrate_kbps))
        
        return video_bitrate_kbps
    
    def get_compression_settings(self, url=None, duration=None):
        """Calculate compression settings based on user selection"""
        if not self.compression_enabled.get():
            return None
        
        if self.compression_mode_var.get() == "simple":
            # Simple mode - use presets with calculated bitrates
            preset = self.preset_var.get()
            
            # Map presets to target sizes and audio bitrates
            preset_map = {
                'Discord 8MB (Video)': (8, 96),
                'Discord 25MB (Nitro Classic)': (25, 128),
                'Discord 50MB (Nitro)': (50, 128),
                'Discord 100MB (Nitro Boost)': (100, 192),
                'Twitter/X 512MB': (512, 192),
                'Instagram 100MB': (100, 192),
                'WhatsApp 16MB': (16, 96),
                'Telegram 2GB': (2048, 256)
            }
            
            target_size_mb, audio_bitrate = preset_map.get(preset, (8, 96))
            
            # If we have duration, calculate proper video bitrate
            if duration:
                video_bitrate = self.calculate_bitrates_for_target_size(
                    target_size_mb, duration, audio_bitrate
                )
            else:
                # Fallback to estimation for 3-minute video
                video_bitrate = self.calculate_bitrates_for_target_size(
                    target_size_mb, 180, audio_bitrate
                )
            
            return {
                'target_size': target_size_mb,
                'video_bitrate': video_bitrate,
                'audio_bitrate': audio_bitrate
            }
        else:
            # Advanced mode - use user input
            try:
                target_size = float(self.target_size_entry.get() or "8")
                video_bitrate_str = self.video_bitrate_entry.get().strip()
                audio_bitrate = int(self.audio_bitrate_entry.get() or "128")
                
                if video_bitrate_str:
                    # User specified video bitrate
                    video_bitrate = int(video_bitrate_str)
                else:
                    # Auto-calculate video bitrate from target size and duration
                    if duration:
                        video_bitrate = self.calculate_bitrates_for_target_size(
                            target_size, duration, audio_bitrate
                        )
                    else:
                        # Fallback to estimation for 3-minute video
                        video_bitrate = self.calculate_bitrates_for_target_size(
                            target_size, 180, audio_bitrate
                        )
                
                return {
                    'target_size': target_size,
                    'video_bitrate': video_bitrate,
                    'audio_bitrate': audio_bitrate
                }
            except ValueError:
                self.update_console("Warning: Invalid compression settings, using defaults")
                return {
                    'target_size': 8,
                    'video_bitrate': 500,
                    'audio_bitrate': 96
                }
    
    def find_ytdlp(self):
        """Locate the yt-dlp binary (cross-platform)"""
        if IS_WINDOWS:
            local_ytdlp = os.path.join(self.deps_path, "yt-dlp.exe")
        else:
            local_ytdlp = os.path.join(self.deps_path, "yt-dlp")
        
        if os.path.exists(local_ytdlp):
            return local_ytdlp
        return "yt-dlp"
    
    def build_command(self, url):
        """Build the yt-dlp command based on selected options"""
        ytdlp_cmd = self.find_ytdlp()
        cmd = [ytdlp_cmd, "--js-runtimes", "node"]
        
        # Add age limit if enabled
        if self.age_limit_enabled.get():
            age_limit = self.age_limit_entry.get().strip() or "18"
            cmd.extend(["--age-limit", age_limit])
            self.update_console(f"Setting age limit to {age_limit} years")
        
        # Get video duration if compression is enabled
        duration = None
        if self.compression_enabled.get() and self.format_var.get() == "video":
            duration = self.get_video_duration(url)
        
        # Get compression settings if enabled (now with duration)
        compression = self.get_compression_settings(url, duration)
        
        if self.format_var.get() == "video":
            # Video command - prioritize best quality
            video_format = self.video_format_var.get()
            
            if compression:
                # Compression enabled - re-encode with specified bitrates
                video_bitrate = compression['video_bitrate']
                audio_bitrate = compression['audio_bitrate']
                
                self.update_console("=" * 60)
                self.update_console("COMPRESSION ENABLED")
                self.update_console(f"Target File Size: ~{compression['target_size']}MB")
                self.update_console(f"Video Bitrate: {video_bitrate}kbps")
                self.update_console(f"Audio Bitrate: {audio_bitrate}kbps")
                self.update_console("Note: Compression requires re-encoding and will take longer.")
                self.update_console("This is normal - the video must be processed to reduce size.")
                self.update_console("=" * 60)
                
                # Build compression FFmpeg arguments
                if video_format == "mp4":
                    postproc_args = f"ffmpeg:-c:v libx264 -b:v {video_bitrate}k -maxrate {video_bitrate}k -bufsize {video_bitrate*2}k -preset medium -c:a aac -b:a {audio_bitrate}k -ar 48000"
                elif video_format == "mkv":
                    postproc_args = f"ffmpeg:-c:v libx264 -b:v {video_bitrate}k -maxrate {video_bitrate}k -bufsize {video_bitrate*2}k -preset medium -c:a aac -b:a {audio_bitrate}k -ar 48000"
                elif video_format == "webm":
                    postproc_args = f"ffmpeg:-c:v libvpx-vp9 -b:v {video_bitrate}k -maxrate {video_bitrate}k -bufsize {video_bitrate*2}k -c:a libopus -b:a {audio_bitrate}k -ar 48000"
                elif video_format == "mov":
                    postproc_args = f"ffmpeg:-c:v libx264 -b:v {video_bitrate}k -maxrate {video_bitrate}k -bufsize {video_bitrate*2}k -preset medium -c:a aac -b:a {audio_bitrate}k -ar 48000"
                elif video_format == "avi":
                    postproc_args = f"ffmpeg:-c:v libx264 -b:v {video_bitrate}k -maxrate {video_bitrate}k -bufsize {video_bitrate*2}k -preset medium -c:a mp3 -b:a {audio_bitrate}k -ar 48000"
                else:
                    postproc_args = f"ffmpeg:-c:v libx264 -b:v {video_bitrate}k -maxrate {video_bitrate}k -bufsize {video_bitrate*2}k -preset medium -c:a aac -b:a {audio_bitrate}k -ar 48000"
            else:
                # No compression - use high quality encoding for compatibility
                # MP4 always uses H.264 for maximum compatibility with editing software
                if video_format == "mp4":
                    postproc_args = "ffmpeg:-c:v libx264 -crf 18 -preset slow -c:a aac -b:a 320k -ar 48000"
                elif video_format == "mkv":
                    postproc_args = "ffmpeg:-c:v copy -c:a aac -b:a 320k -ar 48000"
                elif video_format == "webm":
                    postproc_args = "ffmpeg:-c:v copy -c:a libopus -b:a 320k -ar 48000"
                elif video_format == "mov":
                    postproc_args = "ffmpeg:-c:v libx264 -crf 18 -preset slow -c:a aac -b:a 320k -ar 48000"
                elif video_format == "avi":
                    postproc_args = "ffmpeg:-c:v copy -c:a mp3 -b:a 320k -ar 48000"
                else:
                    postproc_args = "ffmpeg:-c:v copy -c:a aac -b:a 320k -ar 48000"
            
            output_template = os.path.join(self.output_dir, "%(title)s.%(ext)s")
            cmd.extend([
                "-f", "bestvideo*+bestaudio/best",
                "--merge-output-format", video_format,
                "--ffmpeg-location", self.ffmpeg_location,
                "--postprocessor-args", postproc_args,
                "-o", output_template,
                url
            ])
        else:
            # Audio command - best quality
            audio_format = self.audio_format_var.get()
            # Map UI format to yt-dlp format (e.g., 'ogg' -> 'vorbis')
            ytdlp_audio_format = self.map_audio_format(audio_format)
            
            if compression:
                # Compression enabled for audio
                audio_bitrate = compression['audio_bitrate']
                self.update_console("=" * 60)
                self.update_console("COMPRESSION ENABLED (Audio)")
                self.update_console(f"Audio Bitrate: {audio_bitrate}kbps")
                self.update_console("Note: Lower bitrate reduces file size but may affect quality.")
                self.update_console("=" * 60)
                bitrate = f"{audio_bitrate}k"
                audio_quality = "0"
            else:
                # Set audio quality based on format
                if audio_format in ["mp3", "aac", "opus", "ogg"]:
                    # For lossy formats, use highest bitrate
                    audio_quality = "0"  # Best quality for VBR
                    bitrate = "320k"
                else:
                    # For lossless formats (flac, wav, alac, m4a)
                    audio_quality = "0"
                    bitrate = None
            
            cmd.extend([
                "-f", "bestaudio/best",
                "-x",  # Extract audio
                "--audio-format", ytdlp_audio_format,
                "--audio-quality", audio_quality,
                "--ffmpeg-location", self.ffmpeg_location,
            ])
            
            if bitrate:
                cmd.extend(["--postprocessor-args", f"audio:-b:a {bitrate} -ar 48000"])
            else:
                cmd.extend(["--postprocessor-args", "audio:-ar 48000"])
            
            output_template = os.path.join(self.output_dir, "%(title)s.%(ext)s")
            cmd.extend([
                "-o", output_template,
                url
            ])
            
        return cmd

if __name__ == "__main__":
    # Get base path
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    deps_path = os.path.join(base_path, "dependencies")
    ytdlp_binary = "yt-dlp.exe" if IS_WINDOWS else "yt-dlp"
    ffmpeg_binary = "ffmpeg.exe" if IS_WINDOWS else "ffmpeg"
    local_ytdlp = os.path.join(deps_path, ytdlp_binary)
    local_ffmpeg = os.path.join(deps_path, "ffmpeg", "bin", ffmpeg_binary)
    
    # Check if yt-dlp is available (either local or system-wide)
    ytdlp_found = False
    if os.path.exists(local_ytdlp):
        ytdlp_found = True
    else:
        try:
            subprocess.run(
                ["yt-dlp", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                creationflags=subprocess_flags()
            )
            ytdlp_found = True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
    
    if not ytdlp_found:
        if IS_WINDOWS:
            response = messagebox.askyesno(
                "Dependencies Missing",
                "yt-dlp is not installed.\n\nWould you like to run the setup wizard now?"
            )
            if response:
                setup_bat = os.path.join(base_path, "setup.bat")
                if os.path.exists(setup_bat):
                    subprocess.Popen([setup_bat], shell=True)
                else:
                    messagebox.showerror("Error", "Setup file not found. Please run setup.bat manually.")
        else:
            messagebox.showerror(
                "Dependencies Missing",
                "yt-dlp is not installed.\n\n"
                "Install it with your package manager:\n"
                "  Ubuntu/Debian: sudo apt install yt-dlp\n"
                "  Arch: sudo pacman -S yt-dlp\n"
                "  macOS: brew install yt-dlp\n"
                "  pip: pip install yt-dlp"
            )
        exit(1)
    
    # Check if ffmpeg is available (local, system path, or platform-specific fallback)
    ffmpeg_found = False
    if os.path.exists(local_ffmpeg):
        ffmpeg_found = True
    elif IS_WINDOWS and os.path.exists("C:\\ffmpeg\\bin\\ffmpeg.exe"):
        ffmpeg_found = True
    elif shutil.which("ffmpeg"):
        ffmpeg_found = True
    
    if not ffmpeg_found:
        if IS_WINDOWS:
            response = messagebox.askyesno(
                "Dependencies Missing",
                "FFmpeg is not installed.\n\nWould you like to run the setup wizard now?"
            )
            if response:
                setup_bat = os.path.join(base_path, "setup.bat")
                if os.path.exists(setup_bat):
                    subprocess.Popen([setup_bat], shell=True)
                else:
                    messagebox.showerror("Error", "Setup file not found. Please run setup.bat manually.")
        else:
            messagebox.showerror(
                "Dependencies Missing",
                "FFmpeg is not installed.\n\n"
                "Install it with your package manager:\n"
                "  Ubuntu/Debian: sudo apt install ffmpeg\n"
                "  Arch: sudo pacman -S ffmpeg\n"
                "  macOS: brew install ffmpeg"
            )
        exit(1)

    # Check if all required Python packages are installed
    required_packages = ["tkinter"]
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            messagebox.showerror("Error", f"Required Python package '{package}' is not installed.")
            exit(1)
    
    # Create and run the app
    root = tk.Tk()
    app = YtDlpGUI(root)
    root.mainloop()