#!/usr/bin/env python3
"""
MediaFire Downloader Script
Downloads individual files and entire folders from MediaFire.
Uses Playwright to extract direct download links and requests+tqdm for
streaming downloads with progress indicators.
"""

import os
import sys
import re
import argparse
import requests
from urllib.parse import unquote
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from tqdm import tqdm


# ---------------------------------------------------------------------------
# Folder URL helpers
# ---------------------------------------------------------------------------

def is_folder_url(url):
    """Check if a URL is a MediaFire folder link."""
    return bool(re.search(r"mediafire\.com/folder/", url))


def is_file_url(url):
    """Check if a URL is a MediaFire single-file link."""
    return bool(re.search(r"mediafire\.com/file/", url))


def extract_folder_key(url):
    """
    Extract the folder key from a MediaFire folder URL.
    E.g. https://www.mediafire.com/folder/6n49l4tgmirt5/SomeName -> 6n49l4tgmirt5
    """
    match = re.search(r"mediafire\.com/folder/([a-zA-Z0-9]+)", url)
    return match.group(1) if match else None


def get_folder_file_links(folder_key, folder_name="root"):
    """
    Use MediaFire's public API to list all files inside a folder (including
    nested sub-folders, recursively).

    Returns a list of file page URLs:
        https://www.mediafire.com/file/<quickkey>/<filename>/file
    """
    api_base = "https://www.mediafire.com/api/1.5/folder/get_content.php"
    file_urls = []

    # --- Collect files ---
    chunk = 1
    while True:
        params = {
            "folder_key": folder_key,
            "content_type": "files",
            "response_format": "json",
            "chunk": chunk,
        }
        try:
            resp = requests.get(api_base, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[-] API request failed for folder {folder_key} (chunk {chunk}): {e}")
            break

        result = data.get("response", {}).get("result", "")
        if result != "Success":
            error_msg = data.get("response", {}).get("message", "Unknown error")
            print(f"[-] API error for folder '{folder_name}': {error_msg}")
            break

        folder_content = data["response"].get("folder_content", {})
        files = folder_content.get("files", [])

        if not files:
            break

        for f in files:
            quickkey = f.get("quickkey", "")
            filename = f.get("filename", "unknown")
            if quickkey:
                file_url = f"https://www.mediafire.com/file/{quickkey}/{filename}/file"
                file_urls.append(file_url)

        # Check if there are more chunks
        more_chunks = folder_content.get("more_chunks", "no")
        if more_chunks == "yes":
            chunk += 1
        else:
            break

    # --- Recursively collect files from sub-folders ---
    chunk = 1
    while True:
        params = {
            "folder_key": folder_key,
            "content_type": "folders",
            "response_format": "json",
            "chunk": chunk,
        }
        try:
            resp = requests.get(api_base, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[-] API request failed for subfolders of {folder_key} (chunk {chunk}): {e}")
            break

        result = data.get("response", {}).get("result", "")
        if result != "Success":
            break

        folder_content = data["response"].get("folder_content", {})
        folders = folder_content.get("folders", [])

        if not folders:
            break

        for sub in folders:
            sub_key = sub.get("folderkey", "")
            sub_name = sub.get("name", "subfolder")
            if sub_key:
                print(f"[*]   Scanning sub-folder: {sub_name}")
                sub_files = get_folder_file_links(sub_key, folder_name=sub_name)
                file_urls.extend(sub_files)

        more_chunks = folder_content.get("more_chunks", "no")
        if more_chunks == "yes":
            chunk += 1
        else:
            break

    return file_urls


def expand_folder_urls(urls):
    """
    Given a list of URLs, expand any folder URLs into individual file URLs
    using the MediaFire API.  Non-folder URLs are kept as-is.
    """
    expanded = []
    for url in urls:
        if is_folder_url(url):
            folder_key = extract_folder_key(url)
            if not folder_key:
                print(f"[-] Could not extract folder key from: {url}")
                expanded.append(url)  # keep it so it shows as failed later
                continue

            # Extract human-readable folder name from URL for display
            parts = url.rstrip("/").split("/")
            folder_label = unquote(parts[-1]) if len(parts) > 4 else folder_key

            print(f"\n[*] Enumerating folder: {folder_label}")
            file_links = get_folder_file_links(folder_key, folder_name=folder_label)
            if file_links:
                print(f"[+] Found {len(file_links)} file(s) in folder '{folder_label}'")
                expanded.extend(file_links)
            else:
                print(f"[-] No files found in folder '{folder_label}'")
        else:
            expanded.append(url)
    return expanded


# ---------------------------------------------------------------------------
# Download with progress
# ---------------------------------------------------------------------------

def download_with_progress(direct_url, filepath):
    """
    Stream-download a file from *direct_url* to *filepath* while displaying
    a tqdm progress bar showing size, speed, and ETA.

    Returns True on success, False on failure.
    """
    try:
        resp = requests.get(direct_url, stream=True, timeout=60, allow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        print(f"[-] Failed to start download stream: {e}")
        return False

    total_size = int(resp.headers.get("content-length", 0))
    filename = os.path.basename(filepath)

    # Use tqdm for a nice progress bar
    with open(filepath, "wb") as f, tqdm(
        desc=filename,
        total=total_size if total_size > 0 else None,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        ncols=80,
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}, {elapsed}<{remaining}]",
    ) as progress:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                progress.update(len(chunk))

    return True


# ---------------------------------------------------------------------------
# Core download logic (single file)
# ---------------------------------------------------------------------------

def download_file(url, output_dir, headless=True):
    """
    Download a single MediaFire file.
    1. Use Playwright to navigate to the MediaFire page and locate the
       download button / extract the direct download link.
    2. Stream-download the file using requests + tqdm for a progress bar.
    """
    print(f"\n[+] Processing URL: {url}")

    if not is_file_url(url) and not is_folder_url(url):
        print(f"[-] URL does not appear to be a valid MediaFire file link: {url}")
        return False

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-web-security", "--no-sandbox"],
        )

        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        context = browser.new_context(
            accept_downloads=True,
            user_agent=user_agent,
            viewport={"width": 1280, "height": 800},
        )

        page = context.new_page()
        page.set_default_timeout(45000)

        try:
            print(f"[*] Loading MediaFire page: {url}")
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            title = page.title()
            print(f"[*] Page title: {title}")

            # Wait for the download button to appear
            print("[*] Waiting for download button to render on page...")
            try:
                page.wait_for_selector(
                    "a#downloadButton, a.download_link, .downloadButton",
                    state="visible",
                    timeout=15000,
                )
            except Exception:
                print("[*] Timeout waiting for specific download button. Trying fallback...")

            # Robust selector strategies for the main MediaFire download button
            selectors = [
                "a#downloadButton",
                "a.download_link",
                "a[href*='download']",
                "a:has-text('Download')",
                ".downloadButton",
            ]

            download_btn = None
            for selector in selectors:
                try:
                    locator = page.locator(selector)
                    if locator.count() > 0:
                        for i in range(locator.count()):
                            item = locator.nth(i)
                            if item.is_visible() and item.is_enabled():
                                download_btn = item
                                print(f"[+] Found download element with selector: '{selector}'")
                                break
                    if download_btn:
                        break
                except Exception:
                    continue

            if not download_btn:
                # Last-resort: scan all <a> tags for anything with "download"
                print("[-] Specific download button not found. Searching all links...")
                links = page.locator("a")
                for i in range(links.count()):
                    link = links.nth(i)
                    href = link.get_attribute("href") or ""
                    text = link.text_content() or ""
                    if "download" in href.lower() or "download" in text.lower():
                        if link.is_visible():
                            download_btn = link
                            print(f"[+] Found fallback link: text='{text.strip()}', href='{href}'")
                            break

            if not download_btn:
                print("[-] Error: Could not locate the download button on the page.")
                screenshot_path = os.path.join(output_dir, "error_screenshot.png")
                page.screenshot(path=screenshot_path)
                print(f"[*] Saved debug screenshot to: {screenshot_path}")
                return False

            download_btn.scroll_into_view_if_needed()

            # ---------------------------------------------------------------
            # Strategy: Click the button and intercept the Playwright download
            # to get the direct URL, then download via requests for progress.
            # ---------------------------------------------------------------
            print("[*] Triggering download click...")
            with page.expect_download(timeout=60000) as download_info:
                download_btn.click()

            download = download_info.value
            direct_url = download.url
            filename = download.suggested_filename
            filepath = os.path.join(output_dir, filename)

            # Cancel Playwright's own download – we'll use requests instead
            download.cancel()

            print(f"[+] Captured direct download URL for: {filename}")
            print(f"[*] Downloading with progress bar...")

            success = download_with_progress(direct_url, filepath)

            if success and os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                print(f"[+] Success! Saved to: {filepath} ({size_mb:.2f} MB)")
                return True
            else:
                print("[-] Error: Download failed or file is empty.")
                # Clean up empty/partial file
                if os.path.exists(filepath):
                    os.remove(filepath)
                return False

        except PlaywrightTimeoutError:
            print("[-] Timeout occurred while waiting for the page or download.")
            return False
        except Exception as e:
            print(f"[-] An unexpected error occurred: {e}")
            return False
        finally:
            context.close()
            browser.close()


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="MediaFire Downloader (supports files & folders)")
    parser.add_argument("urls", nargs="*", help="MediaFire file or folder URLs to download")
    parser.add_argument("-f", "--file", help="File containing list of URLs (one per line)")
    parser.add_argument("-o", "--output", default="downloads", help="Output directory (default: 'downloads')")
    parser.add_argument("--headful", action="store_true", help="Run browser in headful (visible) mode")

    args = parser.parse_args()

    # Collate URLs
    urls = []
    if args.urls:
        urls.extend(args.urls)

    if args.file:
        if os.path.exists(args.file):
            with open(args.file, "r", encoding="utf-8") as f:
                for line in f:
                    line_clean = line.strip()
                    if line_clean and not line_clean.startswith("#"):
                        urls.append(line_clean)
        else:
            print(f"[-] Error: Specified file not found: {args.file}")
            sys.exit(1)

    # If no URLs provided, check standard input
    if not urls and not sys.stdin.isatty():
        print("[*] Reading URLs from standard input...")
        for line in sys.stdin:
            line_clean = line.strip()
            if line_clean and not line_clean.startswith("#"):
                urls.append(line_clean)

    if not urls:
        print("[-] Error: No URLs provided.")
        parser.print_help()
        sys.exit(1)

    # Standardize output directory
    output_dir = os.path.abspath(args.output)
    os.makedirs(output_dir, exist_ok=True)

    # Expand folder URLs into individual file URLs
    print(f"[*] Resolving {len(urls)} input URL(s)...")
    expanded_urls = expand_folder_urls(urls)

    if not expanded_urls:
        print("[-] Error: No downloadable file URLs found.")
        sys.exit(1)

    print(f"\n[*] Starting download task for {len(expanded_urls)} file(s)")
    print(f"[*] Output directory: {output_dir}")

    success_count = 0
    failures = []

    for idx, file_url in enumerate(expanded_urls, 1):
        print(f"\n{'='*50}")
        print(f"  File {idx}/{len(expanded_urls)}")
        print(f"{'='*50}")
        success = download_file(file_url, output_dir, headless=not args.headful)
        if success:
            success_count += 1
        else:
            failures.append(file_url)

    print("\n==============================")
    print("       DOWNLOAD SUMMARY       ")
    print("==============================")
    print(f"Total processed: {len(expanded_urls)}")
    print(f"Successful:      {success_count}")
    print(f"Failed:          {len(failures)}")

    if failures:
        print("\nFailed URLs:")
        for fail in failures:
            print(f" - {fail}")

    if success_count == len(expanded_urls):
        print("\n[+] All downloads completed successfully!")
        sys.exit(0)
    elif success_count > 0:
        print("\n[!] Task completed with some failures.")
        sys.exit(2)
    else:
        print("\n[-] All downloads failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
