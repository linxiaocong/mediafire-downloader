# 📥 OpenClaw Skill: MediaFire Downloader

A premium, autonomous OpenClaw skill written in Python that batch-downloads files from MediaFire.

---

## ✨ Features

- **MediaFire Downloader**: Locates and triggers downloads on MediaFire pages using a dynamic and robust set of fallback selectors, with built-in 15-second rendering auto-waiting.
- **Advanced Stealth**: Emulates real user behaviors and strips away automation traces (like `navigator.webdriver`).
- **Batch Processing**: Supports downloading multiple links passed as command line arguments or importing them in bulk from a `.txt` file.
- **Smart Retries & Timeouts**: Generous interactive timeouts (up to 3 minutes in headful mode) and full debugging screenshot generation on error.

---

## 📁 Directory Structure

```
mediafire-downloader/
├── SKILL.md            # OpenClaw skill descriptor & gateway runbook
├── README.md           # User documentation (this file)
├── requirements.txt    # Skill dependencies (Playwright, bypass-ouo, DrissionPage, lxml)
└── downloader.py       # Core automation script
```

---

## 🚀 Setup & Installation

### 1. Set Up Environment
Create and activate a virtual environment in the parent folder:

```bash
# Create a virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\Activate.ps1

# Activate (macOS/Linux)
source .venv/bin/activate
```

### 2. Install Dependencies
Install requirements and download the Chromium browser binaries:

```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright Chromium binaries
python -m playwright install chromium
```

---

## 💻 CLI Usage Guide

The downloader is extremely flexible and can be customized with various arguments.

### Positional Arguments
- `urls`: List of MediaFire URLs to download.

### Optional Flags
- `-f`, `--file`: Path to a text file containing one URL per line.
- `-o`, `--output`: Target folder for downloaded files (defaults to `downloads`).
- `--headful`: Run in visible browser mode (essential when running in interactive sessions to allow Cloudflare passive checks or manual clicks to clear).

---

## 📖 Command Examples

### 1. Download a single direct MediaFire URL (Headless)
```bash
python mediafire-downloader/downloader.py "https://www.mediafire.com/file/xxxxx/example.zip"
```

### 2. Batch Download from a Text File
Create a `urls.txt` file (one URL per line, lines starting with `#` are ignored) and run:
```bash
python mediafire-downloader/downloader.py -f urls.txt --headful
```

### 3. Custom Output Directory
Save downloads to a specific target folder:
```bash
python mediafire-downloader/downloader.py "https://www.mediafire.com/file/xxxxx/example.zip" -o "C:\MyDownloads"
```
