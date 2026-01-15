# YouTube Downloader Setup Script
# This script will download and install all required dependencies

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  YouTube Downloader - Setup Wizard" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get the script's directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$depsDir = Join-Path $scriptDir "dependencies"

# Create dependencies directory if it doesn't exist
if (-not (Test-Path $depsDir)) {
    New-Item -ItemType Directory -Path $depsDir | Out-Null
}

# Function to download files with progress
function Download-File {
    param (
        [string]$Url,
        [string]$OutputPath
    )
    
    try {
        Write-Host "Downloading from: $Url" -ForegroundColor Yellow
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($Url, $OutputPath)
        Write-Host "Downloaded successfully!" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "Error downloading file: $_" -ForegroundColor Red
        return $false
    }
}

# Function to extract zip files
function Extract-ZipFile {
    param (
        [string]$ZipPath,
        [string]$DestinationPath
    )
    
    try {
        Write-Host "Extracting archive..." -ForegroundColor Yellow
        Expand-Archive -Path $ZipPath -DestinationPath $DestinationPath -Force
        Write-Host "Extracted successfully!" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "Error extracting file: $_" -ForegroundColor Red
        return $false
    }
}

# Check and install yt-dlp
Write-Host "[1/2] Checking yt-dlp..." -ForegroundColor Cyan
$ytdlpPath = Join-Path $depsDir "yt-dlp.exe"

if (Test-Path $ytdlpPath) {
    Write-Host "yt-dlp is already installed." -ForegroundColor Green
} else {
    Write-Host "yt-dlp not found. Downloading..." -ForegroundColor Yellow
    $ytdlpUrl = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
    
    if (Download-File -Url $ytdlpUrl -OutputPath $ytdlpPath) {
        Write-Host "yt-dlp installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Failed to download yt-dlp. Please check your internet connection." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Check and install ffmpeg
Write-Host ""
Write-Host "[2/2] Checking ffmpeg..." -ForegroundColor Cyan
$ffmpegDir = Join-Path $depsDir "ffmpeg"
$ffmpegBinDir = Join-Path $ffmpegDir "bin"
$ffmpegExe = Join-Path $ffmpegBinDir "ffmpeg.exe"

if (Test-Path $ffmpegExe) {
    Write-Host "ffmpeg is already installed." -ForegroundColor Green
} else {
    Write-Host "ffmpeg not found. Downloading..." -ForegroundColor Yellow
    Write-Host "This may take a few minutes (file is ~100MB)..." -ForegroundColor Yellow
    
    # Download ffmpeg
    $ffmpegZip = Join-Path $depsDir "ffmpeg.zip"
    $ffmpegUrl = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    
    if (Download-File -Url $ffmpegUrl -OutputPath $ffmpegZip) {
        # Extract ffmpeg
        $extractDir = Join-Path $depsDir "ffmpeg_temp"
        if (Extract-ZipFile -ZipPath $ffmpegZip -DestinationPath $extractDir) {
            # Find the extracted folder (it will have a timestamp in the name)
            $extractedFolder = Get-ChildItem -Path $extractDir -Directory | Select-Object -First 1
            
            if ($extractedFolder) {
                # Move the bin folder to our dependencies directory
                $sourceBinDir = Join-Path $extractedFolder.FullName "bin"
                
                if (Test-Path $sourceBinDir) {
                    # Create ffmpeg directory structure
                    if (-not (Test-Path $ffmpegDir)) {
                        New-Item -ItemType Directory -Path $ffmpegDir | Out-Null
                    }
                    
                    # Copy bin directory
                    Copy-Item -Path $sourceBinDir -Destination $ffmpegDir -Recurse -Force
                    Write-Host "ffmpeg installed successfully!" -ForegroundColor Green
                } else {
                    Write-Host "Error: Could not find ffmpeg bin directory in extracted files." -ForegroundColor Red
                }
            }
            
            # Cleanup
            Remove-Item -Path $extractDir -Recurse -Force -ErrorAction SilentlyContinue
            Remove-Item -Path $ffmpegZip -Force -ErrorAction SilentlyContinue
        } else {
            Write-Host "Failed to extract ffmpeg." -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
    } else {
        Write-Host "Failed to download ffmpeg. Please check your internet connection." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Final verification
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verify installations
$allGood = $true

if (Test-Path $ytdlpPath) {
    Write-Host "[OK] yt-dlp: $ytdlpPath" -ForegroundColor Green
} else {
    Write-Host "[ERROR] yt-dlp not found!" -ForegroundColor Red
    $allGood = $false
}

if (Test-Path $ffmpegExe) {
    Write-Host "[OK] ffmpeg: $ffmpegExe" -ForegroundColor Green
} else {
    Write-Host "[ERROR] ffmpeg not found!" -ForegroundColor Red
    $allGood = $false
}

Write-Host ""
if ($allGood) {
    Write-Host "All dependencies are installed correctly!" -ForegroundColor Green
    Write-Host "You can now run the YouTube Downloader application." -ForegroundColor Cyan
} else {
    Write-Host "Some dependencies are missing. Please run setup again." -ForegroundColor Red
}

Write-Host ""