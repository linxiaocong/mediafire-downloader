# 📥 MediaFire Downloader (OpenClaw Skill)

A premium OpenClaw skill that downloads files from MediaFire. It now includes:

- **Progress Indicators** – Real‑time `tqdm` progress bars.
- **Folder Support** – Accept MediaFire folder URLs and automatically enumerate and download all contained files (including nested folders).
- **Streamlined Dependencies** – Only `playwright`, `requests`, and `tqdm` are required.

---

## ✨ Features

- **MediaFire File Downloader** – Robust selector fallback to locate and click the download button.
- **Progress Bar** – Streams downloads via `requests` with a `tqdm` progress bar showing size, speed, and ETA.
- **Folder URL Handling** – Detect `mediafire.com/folder/...` links, use MediaFire's public API to list files recursively, and download each file.
- **Headful / Headless Modes** – Run invisibly (default) or with `--headful` for debugging or Cloudflare challenges.
- **Batch Processing** – Accept multiple URLs via command‑line arguments, a text file, or stdin.

---

## 📁 Directory Structure

```
mediafire-downloader/
├── SKILL.md            # This descriptor (you are reading it)
├── README.md           # User documentation
├── requirements.txt    # Dependencies (playwright, requests, tqdm)
└── downloader.py       # Core automation script
```

---

## 🚀 Setup & Installation

1. Create a virtual environment and activate it.
2. Install dependencies with `pip install -r requirements.txt`.
3. Install Playwright Chromium binaries via `python -m playwright install chromium`.

---

## 💻 Usage

```bash
python downloader.py <url1> <url2> ...            # Direct file URLs
python downloader.py "https://www.mediafire.com/folder/KEY"   # Folder URL
python downloader.py -f urls.txt -o my_downloads   # Batch from file
python downloader.py --headful "https://www.mediafire.com/file/..."  # Visible mode
```

---

## 🛠️ Troubleshooting

- **No progress bar** – Ensure `tqdm` is installed.
- **Folder enumeration fails** – Folder must be public; private folders are not supported.
- **Playwright errors** – Re‑run `python -m playwright install chromium`.

---

Enjoy fast, transparent MediaFire downloads with clear progress and folder support!
