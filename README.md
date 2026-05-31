# 📥 OpenClaw Skill: MediaFire & ouo.io Downloader

A premium, autonomous OpenClaw skill written in Python that leverages a multi-tier hybrid bypass pipeline (`bypass_ouo` library + `DrissionPage` anti-bot evasion + Playwright browser automation) to automatically bypass URL shorteners (like `ouo.io` and `ouo.press`) and batch-download files from MediaFire.

---

## ✨ Features

- **MediaFire Downloader**: Locates and triggers downloads on MediaFire pages using a dynamic and robust set of fallback selectors, with built-in 15-second rendering auto-waiting.
- **Three-Tier Hybrid ouo.io Bypasser**: 
  - **Tier 1 (Fastest)**: Automatically attempts to resolve shortlinks using the **`bypass_ouo`** library via API requests.
  - **Tier 2 (Evasive)**: Employs **`DrissionPage`** to control Chrome natively via CDP, hiding automation signatures to clear Cloudflare Turnstile blocks passively and automatically without clicks.
  - **Tier 3 (Resilient Fallback)**: Automatically falls back to our custom **Playwright** browser solver with prominent user guidance if previous tiers are blocked.
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
Install requirements (including `playwright`, `bypass-ouo`, `lxml`, and `DrissionPage`) and download the Chromium browser binaries:

```bash
# Install Python packages
pip install -r mediafire-downloader/requirements.txt

# Install Playwright Chromium binaries
python -m playwright install chromium
```

---

## 💻 CLI Usage Guide

The downloader is extremely flexible and can be customized with various arguments.

### Positional Arguments
- `urls`: List of MediaFire or `ouo.io` URLs to download.

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

### 2. Download from an ouo.io Link (Headful / Interactive)
If a link contains an `ouo.io` or `ouo.press` shortener, you should run in `--headful` mode so you can interact with the Cloudflare checkbox if it falls back to Playwright:
```bash
python mediafire-downloader/downloader.py "https://ouo.io/WU3GDY" --headful
```

### 3. Batch Download from a Text File
Create a `urls.txt` file (one URL per line, lines starting with `#` are ignored) and run:
```bash
python mediafire-downloader/downloader.py -f urls.txt --headful
```

### 4. Custom Output Directory
Save downloads to a specific target folder:
```bash
python mediafire-downloader/downloader.py "https://www.mediafire.com/file/xxxxx/example.zip" -o "C:\MyDownloads"
```

---

## 🛠️ Troubleshooting

### 1. Cloudflare Turnstile Verification Paused?
> [!NOTE]
> When the `bypass_ouo` library gets blocked by Cloudflare (403 Forbidden), the script will automatically fallback to **DrissionPage**.
> If `DrissionPage` also fails, it will fallback to Playwright and open the browser on your screen.
> - **Solution**: Always append the `--headful` flag. When the browser pops up on your screen, click the "Verify you are human" checkbox. The script will wait up to **180 seconds** for you to do this, and will automatically continue immediately after you click it.

### 2. Immediate Redirect to Homepage?
> [!IMPORTANT]
> Ouo.io uses browser signature checks. If it detects a standard automated runner, it redirects back to `ouo.io/`.
> - **Solution**: The script contains built-in stealth scripts. Ensure you are running the latest version of `downloader.py` which dynamically hides `navigator.webdriver`.
