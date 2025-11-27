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

def wait_for_pdf_ready_indicator(driver, timeout=120):
    """Wait for the PDF ready indicator to appear"""
    print("[STEP] Waiting for PDF ready indicator...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # Check if the status div contains "PDF generation ready"
            status_text = driver.execute_script("""
                const statusDiv = document.getElementById('pdf-status');
                if (statusDiv && !statusDiv.classList.contains('d-none')) {
                    return statusDiv.textContent;
                }
                return null;
            """)
            
            if status_text and "ready" in status_text.lower():
                print(f"[OK] PDF ready indicator found: '{status_text}'")
                return True
            
            elapsed = int(time.time() - start_time)
            if elapsed % 10 == 0 and elapsed > 0:
                print(f"[INFO] Still waiting for PDF ready indicator... ({elapsed}s)")
            
            time.sleep(2)
        except Exception as e:
            print(f"[WARN] Error checking PDF ready status: {e}")
            time.sleep(2)
    
    print(f"[WARN] PDF ready indicator timeout after {timeout}s, proceeding anyway")
    return False

def wait_for_pdf_file(download_dir, timeout=240):
    """Wait for a new PDF file to appear and stabilize"""
    print(f"[STEP] Waiting for new PDF in {download_dir} (timeout={timeout}s)...")
    start_time = time.time()
    
    # Get initial PDFs to exclude
    initial_pdfs = set(f for f in os.listdir(download_dir) if f.endswith('.pdf'))
    print(f"[DEBUG] Initial PDFs in directory: {initial_pdfs}")
    
    last_size = {}
    stable_threshold = 3  # seconds for file size to remain stable
    
    while time.time() - start_time < timeout:
        current_pdfs = set(f for f in os.listdir(download_dir) if f.endswith('.pdf'))
        new_pdfs = current_pdfs - initial_pdfs
        
        if new_pdfs:
            for pdf_name in new_pdfs:
                full_path = os.path.join(download_dir, pdf_name)
                try:
                    size = os.path.getsize(full_path)
                    if size > 0:
                        # Check if size is stable
                        if pdf_name in last_size:
                            if last_size[pdf_name]['size'] == size:
                                if time.time() - last_size[pdf_name]['time'] > stable_threshold:
                                    print(f"[OK] PDF file stable and ready: {full_path} ({size} bytes)")
                                    return full_path
                        else:
                            last_size[pdf_name] = {'size': size, 'time': time.time()}
                            print(f"[DEBUG] New PDF detected: {pdf_name} ({size} bytes)")
                    else:
                        last_size[pdf_name] = {'size': size, 'time': time.time()}
                except OSError:
                    continue
        
        # Log progress every 15 seconds
        elapsed = int(time.time() - start_time)
        if elapsed % 15 == 0 and elapsed > 0:
            print(f"[INFO] Still waiting for PDF download... ({elapsed}s elapsed)")
        
        time.sleep(1)
    
    print(f"[ERROR] Timed out waiting for PDF download in {download_dir}")
    print(f"[DEBUG] Final directory contents: {os.listdir(download_dir)}")
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
    
    os.makedirs(download_dir, exist_ok=True)
    abs_download_dir = os.path.abspath(download_dir)
    
    prefs = {
        "download.default_directory": abs_download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "profile.default_content_settings.popups": 0,
        "safebrowsing.enabled": False,
    }
    options.add_experimental_option("prefs", prefs)
    
    driver = None
    try:
        print(f"[STEP] Launching WebDriver for dashboard: {dashboard_url}")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        enable_chrome_headless_download(driver, abs_download_dir)

        print("[STEP] Waiting for dashboard to load (may take 1-2 min on Render free tier)...")
        driver.get(dashboard_url)
        
        # Wait for dashboard to load
        dashboard_ready = False
        for i in range(240):
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

        # CRITICAL: Wait for backend analysis AND PDF generation to be ready
        print("[STEP] Waiting for backend to complete analysis and visualization generation...")
        print("[INFO] This includes: data processing, creating charts, and preparing PDF endpoint")
        
        # Wait for the PDF ready indicator
        wait_for_pdf_ready_indicator(driver, timeout=120)
        
        # Additional small buffer to ensure everything is truly ready
        print("[STEP] Adding 5-second buffer for final stabilization...")
        time.sleep(5)

        print("[STEP] Checking download button state...")
        try:
            button_state = driver.execute_script("""
                const btn = document.getElementById('download-pdf');
                if (btn) {
                    return {
                        exists: true,
                        disabled: btn.disabled || btn.classList.contains('btn-loading'),
                        visible: btn.offsetParent !== null,
                        text: btn.textContent.trim()
                    };
                }
                return {exists: false};
            """)
            print(f"[DEBUG] Button state: {button_state}")
        except Exception as e:
            print(f"[WARN] Could not check button state: {e}")

        print("[STEP] Clicking PDF download button...")
        download_button = driver.find_element(By.ID, "download-pdf")
        
        # Scroll button into view and click
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_button)
        time.sleep(1)
        
        try:
            download_button.click()
            print("[OK] Download button clicked successfully")
        except ElementClickInterceptedException:
            print("[WARN] Click intercepted, using JavaScript click...")
            remove_overlays(driver)
            driver.execute_script("arguments[0].click();", download_button)
            print("[OK] JavaScript click successful")

        print("[STEP] Waiting for PDF file to download...")
        print("[INFO] PDF generation may take 30-90 seconds depending on data complexity")
        
        # Wait for PDF with extended timeout (PDF generation happens on button click)
        pdf_file = wait_for_pdf_file(download_dir, timeout=180)
        
        if pdf_file:
            print(f"[SUCCESS] EDA PDF downloaded: {pdf_file}")
            return pdf_file
        else:
            print("[ERROR] PDF download failed or timed out.")
            
            # Check if there was an error message on the page
            try:
                error_msg = driver.execute_script("""
                    const statusDiv = document.getElementById('pdf-status');
                    if (statusDiv && statusDiv.textContent.includes('failed')) {
                        return statusDiv.textContent;
                    }
                    return null;
                """)
                if error_msg:
                    print(f"[ERROR] Page error message: {error_msg}")
            except:
                pass
            
            # Save page source for debugging
            with open("dashboard_error_detailed.html", "w") as f:
                f.write(driver.page_source)
            print("[DEBUG] Saved page source to dashboard_error_detailed.html")
            return None

    except Exception as e:
        print(f"[FATAL ERROR] Automation error: {repr(e)}")
        traceback.print_exc()
        if driver is not None:
            try:
                with open("dashboard_exception.html", "w") as f:
                    f.write(driver.page_source)
            except:
                pass
        return None
    finally:
        print("[STEP] Quitting WebDriver.")
        if driver is not None:
            driver.quit()
