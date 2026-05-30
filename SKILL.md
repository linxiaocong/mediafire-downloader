---
name: mediafire-downloader
description: Download files from one or more MediaFire URLs using a Playwright browser automation script.
metadata: {"openclaw": {"emoji": "📥", "requires": {"bins": ["python"]}}}
---

# MediaFire Downloader Skill

This skill allows the OpenClaw agent to autonomously download files from one or more MediaFire links. It handles browser interactions, page rendering, selectors, and downloads via Playwright.

## When to Use
Use this skill when a user provides one or multiple MediaFire URLs and requests to download, fetch, retrieve, or grab the files.

## Setup Requirements
This skill requires the `playwright` Python library and Chromium browser binaries:
1. Install Python packages:
   ```bash
   pip install -r {baseDir}/requirements.txt
   ```
2. Install Chromium binaries:
   ```bash
   python -m playwright install chromium
   ```

## Usage
The skill can be executed directly as a Python script:

### Command Line Arguments
* `urls` (positional): One or more MediaFire URLs.
* `-f`, `--file`: Path to a text file containing one URL per line.
* `-o`, `--output`: Target folder for downloaded files (defaults to `downloads`).
* `--headful`: Run in visible browser mode (helps bypass anti-bot challenges if any).

### Execution Examples

**Direct URL(s):**
```bash
python {baseDir}/downloader.py "https://www.mediafire.com/file/example1/file.zip" -o downloads
```

**Multiple URLs:**
```bash
python {baseDir}/downloader.py "https://www.mediafire.com/file/ex1/file1.zip" "https://www.mediafire.com/file/ex2/file2.zip"
```

**Using a File Input:**
```bash
python {baseDir}/downloader.py -f urls.txt
```

**Piping URLs via stdin:**
```bash
cat urls.txt | python {baseDir}/downloader.py
```
