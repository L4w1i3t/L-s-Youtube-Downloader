# L's YouTube Downloader

A simple, user-friendly GUI application for downloading YouTube videos and audio using yt-dlp.

## Features

- 🎥 Download videos in multiple formats (MP4, MKV, WEBM, AVI, MOV)
- 🎵 Extract audio in various formats (MP3, AAC, M4A, OPUS, FLAC, WAV, OGG, ALAC)
- 📊 Real-time download progress in console output
- 🎨 Clean and intuitive interface
- 📁 Customizable output directory (defaults to Desktop)
- 📖 Built-in format guide to help choose the right format

## For End Users (Non-Technical)

### Quick Start Guide

1. **Download the Application**
   - Download the `yt-dlp-gui.exe` and `setup.bat` files
   - Place them in a folder of your choice

2. **Run Setup (First Time Only)**
   - Double-click `setup.bat`
   - The setup wizard will automatically download and install:
     - yt-dlp (the download engine)
     - ffmpeg (for video/audio processing)
   - This may take a few minutes depending on your internet speed
   - You only need to do this once

3. **Launch the Application**
   - Double-click `yt-dlp-gui.exe`
   - The application is now ready to use!

### How to Use

1. Paste a YouTube URL into the URL field
2. Choose your preferred format:
   - **Video**: Select video format (MP4, MKV, WEBM, AVI, or MOV)
   - **Audio Only**: Select audio format (MP3, AAC, M4A, OPUS, FLAC, WAV, OGG, or ALAC)
3. (Optional) Change the output directory if you don't want files saved to your Desktop
4. Click **Download**
5. Monitor progress in the console output
6. Your file will be saved to the specified directory when complete

### Troubleshooting

**"Dependencies Missing" Error**
- Run `setup.bat` to install required components

**Download Fails**
- Check your internet connection
- Verify the YouTube URL is correct
- Some videos may be restricted or unavailable

**Format Guide**
- Click the "Format Guide" button in the application for detailed information about each format

## For Developers

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Installation

1. **Clone or download this repository**

2. **Install Python dependencies**
   ```bash
   pip install tkinter
   ```

3. **Run the setup script**
   ```bash
   setup.bat
   ```
   Or manually install:
   - yt-dlp: `pip install yt-dlp` or download from [yt-dlp releases](https://github.com/yt-dlp/yt-dlp/releases)
   - ffmpeg: Download from [FFmpeg Builds](https://github.com/BtbN/FFmpeg-Builds/releases)

4. **Run the application**
   ```bash
   python yt-dlp-gui.py
   ```

### Building the Executable

To create a standalone .exe file:

1. **Install PyInstaller**
   ```bash
   pip install pyinstaller
   ```

2. **Build the executable**
   ```bash
   pyinstaller --onefile --windowed --icon=assets/logo.ico --add-data "assets;assets" yt-dlp-gui.py
   ```

3. **The executable will be in the `dist` folder**

4. **Copy the following files to distribute:**
   - `dist/yt-dlp-gui.exe`
   - `setup.bat`
   - `setup.ps1`

### Project Structure

```
yt-dlp-gui/
├── yt-dlp-gui.py          # Main application
├── setup.bat              # Setup launcher for Windows
├── setup.ps1              # PowerShell setup script
├── assets/
│   └── logo.png           # Application icon
└── dependencies/          # Created by setup script
    ├── yt-dlp.exe
    └── ffmpeg/
        └── bin/
            ├── ffmpeg.exe
            ├── ffplay.exe
            └── ffprobe.exe
```

### How It Works

1. **Dependency Detection**: The application checks for dependencies in this order:
   - Local `dependencies` folder (created by setup script)
   - System PATH

2. **Setup Script**: 
   - Downloads yt-dlp.exe from official GitHub releases
   - Downloads ffmpeg from BtbN's FFmpeg-Builds
   - Extracts and organizes files in the `dependencies` folder

3. **Application Launch**:
   - Checks for dependencies
   - Offers to run setup if dependencies are missing
   - Launches GUI when all dependencies are present

## Technical Details

### Supported Video Formats

- **MP4**: Best compatibility, works everywhere
- **MKV**: High quality with advanced features
- **WEBM**: Web-optimized format
- **AVI**: Legacy format for older systems
- **MOV**: Apple QuickTime format

### Supported Audio Formats

- **MP3**: Universal compatibility (lossy)
- **AAC**: Modern, efficient (lossy)
- **M4A**: Apple ecosystem (lossy)
- **OPUS**: Best quality-to-size ratio (lossy)
- **FLAC**: Lossless compression
- **WAV**: Uncompressed audio
- **OGG**: Open-source alternative (lossy)
- **ALAC**: Apple Lossless Audio Codec

## License

This project is a GUI wrapper for yt-dlp and ffmpeg. Please respect the licenses of the underlying tools:
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Unlicense
- [ffmpeg](https://ffmpeg.org/) - LGPL/GPL

## Credits

- Built with Python and Tkinter
- Powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- Video/audio processing by [ffmpeg](https://ffmpeg.org/)

## Support

For issues or questions:
1. Check the Format Guide in the application
2. Verify all dependencies are installed via setup.bat
3. Ensure you have a stable internet connection
4. Check if the video is available and not restricted

---

**Note**: This application is for personal use only. Please respect copyright laws and YouTube's Terms of Service when downloading content.
