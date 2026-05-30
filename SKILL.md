---
name: mediafire-downloader
description: Download files from one or more MediaFire or ouo.io/ouo.press URLs using a hybrid bypass (bypass_ouo package + Playwright) pipeline.
metadata: {"openclaw": {"emoji": "📥", "requires": {"bins": ["python"]}}}
---

# MediaFire & ouo.io Downloader Skill

This skill allows the OpenClaw agent to autonomously download files from one or more MediaFire links or bypass URL shorteners (like `ouo.io` and `ouo.press`) that redirect to MediaFire. It utilizes a hybrid bypass strategy combining the `bypass_ouo` API library and a stealth-enabled Playwright browser instance.

## When to Use
Use this skill when a user provides one or multiple MediaFire links or shortened URLs (such as `ouo.io` or `ouo.press`) and requests to download, fetch, retrieve, or grab the files.

## Setup Requirements
This skill requires the dependencies specified in the requirements file and Playwright's Chromium browser binaries:
1. Install Python packages (Playwright, bypass-ouo, and lxml):
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
* `urls` (positional): One or more MediaFire or `ouo.io` URLs.
* `-f`, `--file`: Path to a text file containing one URL per line.
* `-o`, `--output`: Target folder for downloaded files (defaults to `downloads`).
* `--headful`: Run in visible browser mode (essential when resolving `ouo.io` shorteners to manually solve Cloudflare Turnstile verification checkboxes).

### Execution Examples

**Direct URL(s):**
```bash
python {baseDir}/downloader.py "https://www.mediafire.com/file/example1/file.zip" -o downloads
```

**URL Shortener (e.g. ouo.io) Bypassing (Interactive):**
```bash
python {baseDir}/downloader.py "https://ouo.io/WU3GDY" --headful
```

**Multiple URLs:**
```bash
python {baseDir}/downloader.py "https://www.mediafire.com/file/ex1/file1.zip" "https://ouo.io/WU3GDY" --headful
```

**Using a File Input (Batch Download):**
```bash
python {baseDir}/downloader.py -f urls.txt --headful
```

**Piping URLs via stdin:**
```bash
cat urls.txt | python {baseDir}/downloader.py --headful
```
