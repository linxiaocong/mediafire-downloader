#!/usr/bin/env python3
"""
MediaFire Downloader Script
Uses Playwright to navigate MediaFire links, locate download buttons,
handle potential redirects or popups, and securely download files.
"""

import os
import sys
import argparse
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

try:
    from bypass_ouo import bypass_ouo
except ImportError:
    bypass_ouo = None

def resolve_ouo_with_drission(url, headless=True):
    print(f"[*] Detected ouo.io shortener link: {url}")
    print("[*] Resolving using DrissionPage (Advanced anti-bot evasion)...")
    
    try:
        from DrissionPage import ChromiumPage, ChromiumOptions
    except ImportError:
        print("[-] DrissionPage is not installed in the environment. Skipping DrissionPage solver.")
        return None
        
    co = ChromiumOptions()
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    co.headless(headless)
    
    page = None
    try:
        page = ChromiumPage(addr_or_opts=co)
        page.get(url)
        
        # Step 1: Wait for 'I'm a human' button (Cloudflare Turnstile bypass)
        print("[*] Waiting for Cloudflare verification to clear...")
        button = None
        start_time = time.time()
        timeout_limit = 45 if headless else 180
        
        while time.time() - start_time < timeout_limit:
            # Check if we were redirected to MediaFire automatically
            if "mediafire.com" in page.url:
                print(f"[+] Automatically redirected to MediaFire: {page.url}")
                return page.url
                
            for txt in ["I'm a human", "I'M A HUMAN"]:
                try:
                    ele = page.ele(f"text:{txt}", timeout=2)
                    if ele and ele.is_displayed():
                        button = ele
                        break
                except Exception:
                    pass
            if button:
                break
            page.wait(2)
            
        if not button:
            print("[-] Timeout waiting for 'I'm a human' button to appear.")
            return None
            
        print(f"[*] Clicking '{button.text.strip()}' button...")
        button.click(by_js=True)
        
        # Step 2: Wait for countdown and 'Get Link' button
        print("[*] Waiting for countdown and 'Get Link' button...")
        get_link_btn = None
        start_time = time.time()
        
        while time.time() - start_time < timeout_limit:
            if "mediafire.com" in page.url:
                return page.url
                
            try:
                # Ouo.io button has id "btn-main"
                ele = page.ele("#btn-main", timeout=2)
                if ele and ele.is_enabled() and ele.is_displayed():
                    get_link_btn = ele
                    break
            except Exception:
                pass
            page.wait(2)
            
        if not get_link_btn:
            print("[-] Timeout waiting for 'Get Link' button.")
            return None
            
        print("[*] Clicking 'Get Link' button...")
        get_link_btn.click(by_js=True)
        page.wait(4)
        
        # Ouo.io might open popups, so check all open tabs
        final_url = None
        for tab in page.tabs:
            if "mediafire.com" in tab.url:
                final_url = tab.url
                break
                
        if not final_url:
            final_url = page.url
            
        if "mediafire.com" in final_url:
            return final_url
        else:
            print(f"[-] Bypassed but ended up at unexpected URL: {final_url}")
            return None
            
    except Exception as e:
        print(f"[-] DrissionPage resolution failed: {e}")
        return None
    finally:
        if page:
            try:
                page.quit()
            except Exception:
                pass

def resolve_ouo_url(page, url, headless=True):
    print(f"[*] Detected ouo.io shortener link: {url}")
    print("[*] Navigating to ouo.io...")
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    
    timeout_limit = 45 if headless else 180
    start_time = time.time()
    cloudflare_warned = False
    
    # Step 1: Wait for initial Cloudflare Turnstile to clear if present on page load
    print("[*] Checking for initial Cloudflare Turnstile challenge...")
    while time.time() - start_time < timeout_limit:
        title = page.title().lower()
        if "just a moment" in title or "security verification" in title:
            if not cloudflare_warned:
                print("\n" + "="*70)
                print("⚠️  CLOUDFLARE TURNSTILE CHALLENGE DETECTED ON LOAD!")
                if not headless:
                    print("👉 Please solve the verification checkbox in the open browser window.")
                    print(f"👉 The script will wait up to {timeout_limit} seconds for you to check the box.")
                else:
                    print("👉 The script is running headlessly. Try running with --headful to manually solve this challenge.")
                print("="*70 + "\n")
                cloudflare_warned = True
            else:
                print("[*] Waiting for initial Turnstile verification to clear...")
            page.wait_for_timeout(3000)
        else:
            break
            
    # Step 2: Now wait for the "I'm a human" button to become visible and enabled
    print("[*] Locating 'I'm a human' button...")
    button = None
    while time.time() - start_time < timeout_limit:
        # Check standard locators
        btn_loc = page.get_by_role("button", name="I'm a human", exact=False)
        if btn_loc.count() == 0:
            btn_loc = page.get_by_role("button", name="I'M A HUMAN", exact=False)
        if btn_loc.count() == 0:
            btn_loc = page.locator("button:has-text(\"I'm a human\")")
        if btn_loc.count() == 0:
            btn_loc = page.locator("button, input[type='submit']")
            
        if btn_loc.count() > 0 and btn_loc.first.is_visible() and btn_loc.first.is_enabled():
            button = btn_loc.first
            break
            
        page.wait_for_timeout(2000)
        
    if not button:
        print("[-] Could not find 'I'm a human' button. Page might have blocked the request or redirected unexpectedly.")
        return None
        
    try:
        print(f"[*] Clicking '{button.text_content().strip()}' button...")
        button.click()
        page.wait_for_timeout(3000)
    except Exception as e:
        print(f"[-] Click failed: {e}")
        return None
        
    # Step 3: Handle Cloudflare verification / countdown page
    print("[*] Waiting for verification page / countdown...")
    btn_selector = "button#btn-main, a#btn-main, button:has-text('Get Link'), a:has-text('Get Link'), button:has-text('GET LINK'), a:has-text('GET LINK')"
    
    get_link_btn = None
    cloudflare_warned = False
    
    while time.time() - start_time < timeout_limit:
        if "mediafire.com" in page.url:
            print(f"[+] Automatically redirected to MediaFire: {page.url}")
            return page.url
            
        try:
            locator = page.locator(btn_selector)
            if locator.count() > 0 and locator.first.is_visible():
                get_link_btn = locator.first
                break
        except Exception:
            pass
            
        title = page.title().lower()
        if "just a moment" in title or "security verification" in title:
            if not cloudflare_warned:
                print("\n" + "="*70)
                print("⚠️  CLOUDFLARE TURNSTILE CHALLENGE DETECTED ON COUNTDOWN!")
                if not headless:
                    print("👉 Please solve the verification checkbox in the open browser window.")
                    print(f"👉 The script will wait up to {timeout_limit} seconds for you to check the box.")
                else:
                    print("👉 The script is running headlessly. Try running with --headful to manually solve this challenge.")
                print("="*70 + "\n")
                cloudflare_warned = True
            else:
                print("[*] Waiting for Turnstile verification to clear...")
            
        page.wait_for_timeout(2000)
        
    if not get_link_btn:
        print(f"[-] Timeout waiting for 'Get Link' button to appear after {timeout_limit} seconds.")
        return None
        
    # Step 4: Click "Get Link"
    print("[*] Clicking 'Get Link' button...")
    
    # We expect either a new page (popup) or a direct redirect in page
    try:
        with page.context.expect_page(timeout=10000) as new_page_info:
            try:
                get_link_btn.click()
                page.wait_for_timeout(4000)
            except Exception as click_err:
                print(f"[-] Click error: {click_err}")
                
        try:
            popup = new_page_info.value
            print(f"[*] Closing ad popup: {popup.url}")
            popup.close()
        except Exception:
            pass
    except Exception:
        # If no page opened, just continue
        pass
        
    if "mediafire.com" in page.url:
        return page.url
        
    for open_page in page.context.pages:
        if "mediafire.com" in open_page.url:
            print(f"[+] Found MediaFire in open tabs: {open_page.url}")
            return open_page.url
            
    page.wait_for_timeout(3000)
    if "mediafire.com" in page.url:
        return page.url
        
    print(f"[-] Failed to resolve to MediaFire. Ended up at: {page.url}")
    return None

def download_file(url, output_dir, headless=True):
    print(f"\n[+] Processing URL: {url}")
    
    with sync_playwright() as p:
        # Launch Chromium. MediaFire can sometimes block standard headless user-agents,
        # so we will use a realistic user-agent to ensure reliability.
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-web-security", "--no-sandbox"]
        )
        
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        context = browser.new_context(
            accept_downloads=True,
            user_agent=user_agent,
            viewport={"width": 1280, "height": 800}
        )
        
        page = context.new_page()
        page.set_default_timeout(45000)  # 45 seconds timeout
        
        # Hide webdriver property to bypass bot detection on shorteners (like ouo.io)
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        try:
            # Check if this is an ouo.io link
            if "ouo.io" in url or "ouo.press" in url:
                resolved_url = None
                
                # 1. Attempt to bypass using bypass_ouo package (fast API requests)
                if bypass_ouo is not None:
                    print("[*] Attempting to bypass ouo.io using bypass_ouo package...")
                    try:
                        resolved_url = bypass_ouo(url)
                        if resolved_url:
                            print(f"[+] Successfully resolved URL via bypass_ouo package: {resolved_url}")
                    except Exception as e:
                        print(f"[-] bypass_ouo package failed: {e}")
                
                # 2. Secondary attempt using DrissionPage (Advanced anti-bot evasion)
                if not resolved_url:
                    print("[*] Attempting to bypass ouo.io using DrissionPage...")
                    try:
                        resolved_url = resolve_ouo_with_drission(url, headless=headless)
                        if resolved_url:
                            print(f"[+] Successfully resolved URL via DrissionPage: {resolved_url}")
                    except Exception as e:
                        print(f"[-] DrissionPage resolution failed: {e}")
                
                # 3. Tertiary fallback to custom Playwright bypass if previous options failed
                if not resolved_url:
                    print("[*] Falling back to custom Playwright bypass...")
                    resolved_url = resolve_ouo_url(page, url, headless=headless)
                    
                if not resolved_url:
                    print("[-] Error: Failed to resolve ouo.io shortener link.")
                    # Take screenshot for debugging
                    screenshot_path = os.path.join(output_dir, "error_screenshot.png")
                    page.screenshot(path=screenshot_path)
                    print(f"[*] Saved debug screenshot to: {screenshot_path}")
                    return False
                url = resolved_url
                print(f"[+] Successfully resolved shortener URL to: {url}")
            
            # Ensure the Playwright page is actually loaded on the target MediaFire URL
            if "mediafire.com" not in page.url or page.url != url:
                print(f"[*] Loading Playwright page onto resolved URL: {url}")
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
            
            title = page.title()
            print(f"[*] Page title: {title}")
            
            # Wait up to 15 seconds for the download button to render in the DOM
            print("[*] Waiting for download button to render on page...")
            try:
                page.wait_for_selector("a#downloadButton, a.download_link, .downloadButton, text=Download", state="visible", timeout=15000)
            except Exception:
                print("[*] Timeout waiting for specific download button. Proceeding with fallback checks...")
            
            # Robust selector strategies for the main MediaFire download button
            selectors = [
                "a#downloadButton",                     # Standard MediaFire button ID
                "a.download_link",                      # Alternative class name
                "a[href*='download']",                  # Fallback matching download in URL
                "text=Download",                        # Text matching
                "a:has-text('Download')",               # Case-insensitive text match
                ".downloadButton"                       # Alternate selector
            ]
            
            download_btn = None
            for selector in selectors:
                try:
                    locator = page.locator(selector)
                    if locator.count() > 0:
                        # Iterate to find the first visible/enabled match
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
                # If no specific button matches, list all anchor tags and look for 'download'
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
                # Save a screenshot to help debug
                screenshot_path = os.path.join(output_dir, "error_screenshot.png")
                page.screenshot(path=screenshot_path)
                print(f"[*] Saved debug screenshot to: {screenshot_path}")
                return False
            
            # Scroll the download button into view to ensure we can click it
            download_btn.scroll_into_view_if_needed()
            
            # Start waiting for download event while clicking the button
            print("[*] Triggering download click...")
            with page.expect_download(timeout=60000) as download_info:
                # Some ads trigger on click, so click and let expect_download handle it
                download_btn.click()
            
            download = download_info.value
            filename = download.suggested_filename
            filepath = os.path.join(output_dir, filename)
            
            print(f"[+] Download initiated: {filename}")
            print("[*] Downloading file... (this may take a moment depending on size)")
            
            # Save the downloaded file
            download.save_as(filepath)
            
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                print(f"[+] Success! Downloaded file saved to: {filepath} ({size_mb:.2f} MB)")
                return True
            else:
                print(f"[-] Error: File saved but appears to be empty or missing.")
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

def main():
    parser = argparse.ArgumentParser(description="MediaFire Downloader (Playwright-based)")
    parser.add_argument("urls", nargs="*", help="MediaFire URLs to download")
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
    
    print(f"[*] Starting download task for {len(urls)} URLs")
    print(f"[*] Output directory: {output_dir}")
    
    success_count = 0
    failures = []
    
    for idx, url in enumerate(urls, 1):
        print(f"\n--- URL {idx}/{len(urls)} ---")
        # Run in headless mode by default, or headful if requested
        success = download_file(url, output_dir, headless=not args.headful)
        if success:
            success_count += 1
        else:
            failures.append(url)
            
    print("\n==============================")
    print("       DOWNLOAD SUMMARY       ")
    print("==============================")
    print(f"Total processed: {len(urls)}")
    print(f"Successful:      {success_count}")
    print(f"Failed:          {len(failures)}")
    
    if failures:
        print("\nFailed URLs:")
        for fail in failures:
            print(f" - {fail}")
            
    if success_count == len(urls):
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
