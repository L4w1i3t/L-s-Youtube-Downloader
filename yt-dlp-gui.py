import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import threading
import re
import sys
import platform

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
        self.root.geometry("700x650")
        self.root.configure(bg="#f0f0f0")
        
        # Configuration
        # Check for local ffmpeg first, then fall back to C:\ffmpeg\bin
        local_ffmpeg = os.path.join(self.deps_path, "ffmpeg", "bin")
        if os.path.exists(local_ffmpeg):
            self.ffmpeg_location = local_ffmpeg
        else:
            self.ffmpeg_location = "C:\\ffmpeg\\bin"
        
        # Find user's desktop path
        self.output_dir = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        
        # Set up the main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="L's YouTube Downloader", font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 20))

        # User Output Directory (Default: Desktop, but can be changed by the user)
        output_dir_frame = ttk.Frame(main_frame)
        output_dir_frame.pack(fill=tk.X, pady=(0, 20))
        
        output_dir_label = ttk.Label(output_dir_frame, text="Output Directory:")
        output_dir_label.pack(anchor=tk.W)
        
        self.output_dir_entry = ttk.Entry(output_dir_frame, width=70)
        self.output_dir_entry.pack(fill=tk.X, pady=(5, 0))
        self.output_dir_entry.insert(0, self.output_dir)
        
        # URL Entry
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=(0, 20))
        
        url_label = ttk.Label(url_frame, text="Enter YouTube URL:")
        url_label.pack(anchor=tk.W)
        
        self.url_entry = ttk.Entry(url_frame, width=70)
        self.url_entry.pack(fill=tk.X, pady=(5, 0))
        # Format Selection
        format_frame = ttk.LabelFrame(main_frame, text="Download Format")
        format_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Video options with nested radio buttons
        self.format_var = tk.StringVar(value="video")
        video_frame = ttk.Frame(format_frame)
        video_frame.pack(fill=tk.X, padx=10, pady=5)
        
        video_radio = ttk.Radiobutton(video_frame, text="Video", variable=self.format_var, 
                                    value="video", command=self.update_format_selection)
        video_radio.grid(row=0, column=0, sticky=tk.W)
        
        # Video format options
        self.video_format_var = tk.StringVar(value="mp4")
        self.video_formats_frame = ttk.Frame(video_frame)
        self.video_formats_frame.grid(row=0, column=1, padx=(20, 0))
        
        mp4_radio = ttk.Radiobutton(self.video_formats_frame, text="MP4", variable=self.video_format_var, value="mp4")
        mp4_radio.pack(side=tk.LEFT, padx=10)
        
        mkv_radio = ttk.Radiobutton(self.video_formats_frame, text="MKV", variable=self.video_format_var, value="mkv")
        mkv_radio.pack(side=tk.LEFT, padx=10)
        
        webm_radio = ttk.Radiobutton(self.video_formats_frame, text="WEBM", variable=self.video_format_var, value="webm")
        webm_radio.pack(side=tk.LEFT, padx=10)
        
        avi_radio = ttk.Radiobutton(self.video_formats_frame, text="AVI", variable=self.video_format_var, value="avi")
        avi_radio.pack(side=tk.LEFT, padx=10)
        
        mov_radio = ttk.Radiobutton(self.video_formats_frame, text="MOV", variable=self.video_format_var, value="mov")
        mov_radio.pack(side=tk.LEFT, padx=10)
        
        # Audio options with nested radio buttons
        audio_frame = ttk.Frame(format_frame)
        audio_frame.pack(fill=tk.X, padx=10, pady=5)
        
        audio_radio = ttk.Radiobutton(audio_frame, text="Audio", variable=self.format_var, 
                                    value="audio", command=self.update_format_selection)
        audio_radio.grid(row=0, column=0, sticky=tk.W)
        
        # Audio format options
        self.audio_format_var = tk.StringVar(value="mp3")
        self.audio_formats_frame = ttk.Frame(audio_frame)
        self.audio_formats_frame.grid(row=0, column=1, padx=(20, 0))
        
        mp3_radio = ttk.Radiobutton(self.audio_formats_frame, text="MP3", variable=self.audio_format_var, value="mp3")
        mp3_radio.pack(side=tk.LEFT, padx=10)
        
        aac_radio = ttk.Radiobutton(self.audio_formats_frame, text="AAC", variable=self.audio_format_var, value="aac")
        aac_radio.pack(side=tk.LEFT, padx=10)
        
        m4a_radio = ttk.Radiobutton(self.audio_formats_frame, text="M4A", variable=self.audio_format_var, value="m4a")
        m4a_radio.pack(side=tk.LEFT, padx=10)
        
        opus_radio = ttk.Radiobutton(self.audio_formats_frame, text="OPUS", variable=self.audio_format_var, value="opus")
        opus_radio.pack(side=tk.LEFT, padx=10)
        
        flac_radio = ttk.Radiobutton(self.audio_formats_frame, text="FLAC", variable=self.audio_format_var, value="flac")
        flac_radio.pack(side=tk.LEFT, padx=10)
        
        wav_radio = ttk.Radiobutton(self.audio_formats_frame, text="WAV", variable=self.audio_format_var, value="wav")
        wav_radio.pack(side=tk.LEFT, padx=10)
        
        ogg_radio = ttk.Radiobutton(self.audio_formats_frame, text="OGG", variable=self.audio_format_var, value="ogg")
        ogg_radio.pack(side=tk.LEFT, padx=10)
        
        alac_radio = ttk.Radiobutton(self.audio_formats_frame, text="ALAC", variable=self.audio_format_var, value="alac")
        alac_radio.pack(side=tk.LEFT, padx=10)
        
        # Initialize the state of the format options based on initial selection
        self.update_format_selection()
        
        # Format Help Button
        help_button = ttk.Button(main_frame, text="Format Guide", command=self.show_format_guide)
        help_button.pack(pady=(10, 0))
        
        # Download Button
        self.download_button = ttk.Button(main_frame, text="Download", command=self.start_download)
        self.download_button.pack(pady=(0, 20))
        
        # Console Output
        console_frame = ttk.LabelFrame(main_frame, text="Console Output")
        console_frame.pack(fill=tk.BOTH, expand=True)
        
        self.console = tk.Text(console_frame, wrap=tk.WORD, bg="#000000", fg="#00FF00", height=10)
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar for console
        scrollbar = ttk.Scrollbar(self.console, command=self.console.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.console.config(yscrollcommand=scrollbar.set)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
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
        close_button = ttk.Button(frame, text="Close", command=guide_window.destroy)
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
            response = messagebox.askyesno("Continue?", "Do you want to continue anyway?")
            if not response:
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
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Stream the output
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
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
    
    def build_command(self, url):
        """Build the yt-dlp command based on selected options"""
        # Check for local yt-dlp.exe first
        local_ytdlp = os.path.join(self.deps_path, "yt-dlp.exe")
        if os.path.exists(local_ytdlp):
            ytdlp_cmd = local_ytdlp
        else:
            ytdlp_cmd = "yt-dlp"
        
        cmd = [ytdlp_cmd, "--js-runtimes", "node"]
        
        if self.format_var.get() == "video":
            # Video command - prioritize best quality
            video_format = self.video_format_var.get()
            
            # Build format-specific FFmpeg arguments - copy video for speed, re-encode audio for compatibility
            if video_format == "mp4":
                postproc_args = "ffmpeg:-c:v copy -c:a aac -b:a 320k -ar 48000"
            elif video_format == "mkv":
                postproc_args = "ffmpeg:-c:v copy -c:a aac -b:a 320k -ar 48000"
            elif video_format == "webm":
                postproc_args = "ffmpeg:-c:v copy -c:a libopus -b:a 320k -ar 48000"
            elif video_format == "mov":
                postproc_args = "ffmpeg:-c:v copy -c:a aac -b:a 320k -ar 48000"
            elif video_format == "avi":
                postproc_args = "ffmpeg:-c:v copy -c:a mp3 -b:a 320k -ar 48000"
            else:
                postproc_args = "ffmpeg:-c:v copy -c:a aac -b:a 320k -ar 48000"
            
            cmd.extend([
                "-f", "bestvideo*+bestaudio/best",
                "--merge-output-format", video_format,
                "--ffmpeg-location", self.ffmpeg_location,
                "--postprocessor-args", postproc_args,
                "-o", f"{self.output_dir}\\%(title)s.%(ext)s",
                url
            ])
        else:
            # Audio command - best quality
            audio_format = self.audio_format_var.get()
            
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
                "--audio-format", audio_format,
                "--audio-quality", audio_quality,
                "--ffmpeg-location", self.ffmpeg_location,
            ])
            
            if bitrate:
                cmd.extend(["--postprocessor-args", f"audio:-b:a {bitrate} -ar 48000"])
            else:
                cmd.extend(["--postprocessor-args", "audio:-ar 48000"])
            
            cmd.extend([
                "-o", f"{self.output_dir}\\%(title)s.%(ext)s",
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
    local_ytdlp = os.path.join(deps_path, "yt-dlp.exe")
    local_ffmpeg = os.path.join(deps_path, "ffmpeg", "bin", "ffmpeg.exe")
    
    # Check if yt-dlp is available (either local or system-wide)
    ytdlp_found = False
    if os.path.exists(local_ytdlp):
        ytdlp_found = True
    else:
        try:
            subprocess.run(["yt-dlp", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            ytdlp_found = True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
    
    if not ytdlp_found:
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
        exit(1)
    
    # Check if ffmpeg is available (either local or at C:\ffmpeg)
    ffmpeg_found = False
    if os.path.exists(local_ffmpeg):
        ffmpeg_found = True
    elif os.path.exists("C:\\ffmpeg\\bin\\ffmpeg.exe"):
        ffmpeg_found = True
    
    if not ffmpeg_found:
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