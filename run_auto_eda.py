import os
import time
import shutil
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
    NoSuchElementException,
)
from webdriver_manager.chrome import ChromeDriverManager

def enable_chrome_headless_download(driver, download_dir):
    """Enable downloads in headless Chrome"""
    driver.execute_cdp_cmd(
        "Page.setDownloadBehavior",
        {"behavior": "allow", "downloadPath": os.path.abspath(download_dir)}
    )

def remove_overlays(driver):
    """Remove any blocking overlays or modals"""
    scripts = [
        "document.querySelectorAll('.modal-backdrop, .overlay, .spinner, .loader').forEach(e => e.remove())",
        "document.body.style.overflow = 'auto';"
    ]
    for script in scripts:
        driver.execute_script(script)
    print("[INFO] Removed possible blocking overlays.")

def click_button_wait_enabled_with_retry(driver, by_locator, max_attempts=8, wait_seconds=3):
    """Click a button with retry logic"""
    for attempt in range(max_attempts):
        try:
            wait = WebDriverWait(driver, 30)
            wait.until(EC.presence_of_element_located(by_locator))
            element = driver.find_element(*by_locator)
            
            # Wait for button to be enabled
            for enabled_wait in range(40):
                if element.is_enabled():
                    break
                print(f"[INFO] Button {by_locator} is disabled, waiting...")
                time.sleep(1)
                element = driver.find_element(*by_locator)
            
            if not element.is_enabled():
                print(f"[WARN] Button {by_locator} still disabled after 40s, retrying...")
                continue
            
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(1)
            
            try:
                element.click()
                print(f"[OK] Clicked button {by_locator} on attempt {attempt+1}")
                return True
            except ElementClickInterceptedException as e:
                print(f"[WARN] Intercepted, JS click fallback: {e}")
                remove_overlays(driver)
                driver.execute_script("arguments[0].click();", element)
                print(f"[OK] JS click fallback succeeded for button {by_locator} attempt {attempt+1}")
                return True
        except Exception as e:
            print(f"[WARN] Click attempt {attempt+1} for {by_locator} failed: {e}")
            time.sleep(wait_seconds)
    
    print(f"[ERROR] Failed to click button {by_locator} after {max_attempts} attempts")
    return False

def wait_for_pdf_file(download_dir, timeout=300):
    """Wait for a new PDF file to appear and stabilize - increased timeout to 300s"""
    print(f"[STEP] Waiting for new PDF in {download_dir} (timeout={timeout}s)...")
    start_time = time.time()
    
    # Get initial PDFs to exclude (only exclude temp files, keep dated reports)
    initial_files = set(os.listdir(download_dir))
    print(f"[DEBUG] Initial files in directory: {len(initial_files)} files")
    print(f"[DEBUG] Initial files: {sorted(initial_files)}")
    
    last_size = {}
    stable_threshold = 3  # seconds
    
    while time.time() - start_time < timeout:
        elapsed = int(time.time() - start_time)
        current_files = set(os.listdir(download_dir))
        new_files = current_files - initial_files
        
        # Print progress every 10 seconds
        if elapsed % 10 == 0 and elapsed > 0:
            print(f"[DEBUG] Still waiting... {elapsed}s elapsed. New files: {len(new_files)}")
        
        # Look for new PDF files
        new_pdfs = [f for f in new_files if f.endswith('.pdf')]
        
        if new_pdfs:
            print(f"[DEBUG] Found new PDF files: {new_pdfs}")
            for pdf_name in new_pdfs:
                full_path = os.path.join(download_dir, pdf_name)
                try:
                    size = os.path.getsize(full_path)
                    print(f"[DEBUG] PDF {pdf_name} current size: {size} bytes")
                    if size > 0:
                        # Check if size is stable
                        if pdf_name in last_size:
                            if last_size[pdf_name]['size'] == size:
                                if time.time() - last_size[pdf_name]['time'] > stable_threshold:
                                    print(f"[OK] PDF file stable and ready: {full_path}")
                                    return full_path
                            else:
                                print(f"[DEBUG] PDF size changed from {last_size[pdf_name]['size']} to {size}")
                                last_size[pdf_name] = {'size': size, 'time': time.time()}
                        else:
                            print(f"[DEBUG] First size check for {pdf_name}: {size} bytes")
                            last_size[pdf_name] = {'size': size, 'time': time.time()}
                    else:
                        last_size[pdf_name] = {'size': size, 'time': time.time()}
                except OSError as e:
                    print(f"[DEBUG] OSError reading {pdf_name}: {e}")
                    continue
        
        time.sleep(1)
    
    print(f"[ERROR] Timed out waiting for PDF download in {download_dir}")
    print(f"[DEBUG] Final directory contents: {sorted(os.listdir(download_dir))}")
    return None

def run_eda_and_download_report(input_csv, dashboard_url, download_dir):
    """Run EDA analysis and download the generated PDF report"""
    print("[STEP] Starting EDA automation script.")
    if not input_csv or not os.path.isfile(input_csv):
        print(f"[ERROR] Dashboard analysis skipped: {input_csv!r} missing or invalid.")
        return None

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    prefs = {
        "download.default_directory": os.path.abspath(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "profile.default_content_settings.popups": 0,
    }
    options.add_experimental_option("prefs", prefs)

    # NOTE: Removed clean_download_dir() to preserve existing PDFs
    
    driver = None
    try:
        print(f"[STEP] Launching WebDriver for dashboard: {dashboard_url}")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        enable_chrome_headless_download(driver, download_dir)

        print("[STEP] Waiting for dashboard to load (may take 1-2 min on Render free tier)...")
        driver.get(dashboard_url)
        
        # Wait for dashboard branding with extended timeout
        dashboard_ready = False
        for i in range(240):  # 4 minutes timeout
            page_source = driver.page_source
            if "Bogmayer Analytics Dashboard" in page_source or "Upload Dataset" in page_source:
                dashboard_ready = True
                print(f"[OK] Dashboard loaded at {i} seconds.")
                break
            time.sleep(1)
        
        if not dashboard_ready:
            print("[ERROR] Dashboard did not load after 240 seconds.")
            with open("dashboard_load_fail.html", "w") as f:
                f.write(driver.page_source[:20000])
            return None

        print("[STEP] Waiting for file input to be visible...")
        wait = WebDriverWait(driver, 90)
        file_input = wait.until(EC.visibility_of_element_located((By.ID, "fileInput")))
        print("[OK] File input visible, uploading CSV.")
        file_input.send_keys(os.path.abspath(input_csv))

        print("[STEP] Waiting for backend analysis to complete (~30-40s)...")
        time.sleep(35)  # Increased wait time for analysis

        print("[STEP] Directory before download click:", sorted(os.listdir(download_dir)))
        print("[STEP] Attempting to click PDF download button...")
        download_pdf_locator = (By.ID, "download-pdf")
        
        if not click_button_wait_enabled_with_retry(driver, download_pdf_locator):
            print("[ERROR] Failed to click download button")
            with open("dashboard_pdf_click_fail.html", "w") as f:
                f.write(driver.page_source[:10000])
            return None

        print("[STEP] Download button clicked, waiting for file...")
        
        # Debug: Check browser download status
        print("[DEBUG] Checking for download in progress...")
        time.sleep(5)
        
        try:
            user_agent = driver.execute_script("return window.navigator.userAgent")
            print(f"[DEBUG] User agent: {user_agent}")
        except Exception as e:
            print(f"[DEBUG] Could not check user agent: {e}")
        
        print("[STEP] Directory after download click:", sorted(os.listdir(download_dir)))
        
        # Wait for PDF with increased timeout (300 seconds = 5 minutes)
        pdf_file = wait_for_pdf_file(download_dir, timeout=300)
        
        if pdf_file:
            print(f"[SUCCESS] EDA PDF downloaded: {pdf_file}")
            return pdf_file
        else:
            print("[ERROR] PDF download failed or timed out.")
            # Try to get any error messages from the page
            try:
                body_text = driver.find_element(By.TAG_NAME, "body").text
                print(f"[DEBUG] Page content snippet: {body_text[:500]}")
            except:
                pass
            return None

    except Exception as e:
        print(f"[FATAL ERROR] Automation error: {repr(e)}")
        traceback.print_exc()
        if driver is not None:
            with open("dashboard_error.html", "w") as f:
                f.write(driver.page_source[:10000])
        return None
    finally:
        print("[STEP] Quitting WebDriver.")
        if driver is not None:
            driver.quit()
