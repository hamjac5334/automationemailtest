import os
import time
import tempfile
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

def click_button_with_retry(driver, by_locator, max_attempts=5, wait_seconds=2):
    for attempt in range(max_attempts):
        try:
            wait = WebDriverWait(driver, 30)
            wait.until(EC.presence_of_element_located(by_locator))
            element = wait.until(EC.element_to_be_clickable(by_locator))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            try:
                element.click()
                print(f"[OK] Clicked button {by_locator} on attempt {attempt+1}")
                return True
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", element)
                print(f"[WARN] JS click fallback for {by_locator} on attempt {attempt+1}")
                return True
        except Exception as e:
            print(f"[WARN] Click attempt {attempt+1} for {by_locator} failed: {e}")
            time.sleep(wait_seconds)
    print(f"[ERROR] Failed to click button {by_locator} after {max_attempts} attempts")
    return False

def wait_for_pdf_file(download_dir, timeout=90):
    start_time = time.time()
    last_size = -1
    stable_since = None
    while True:
        pdf_files = [f for f in os.listdir(download_dir) if f.endswith('.pdf')]
        if pdf_files:
            pdf_path = os.path.join(download_dir, pdf_files[0])
            size = os.path.getsize(pdf_path)
            if size > 0:
                if size == last_size:
                    if stable_since is None:
                        stable_since = time.time()
                    elif time.time() - stable_since > 2:  # filesize stable > 2s
                        print(f"[OK] PDF file stable and ready: {pdf_path}")
                        return pdf_path
                else:
                    stable_since = None
                    last_size = size
        if time.time() - start_time > timeout:
            print(f"[ERROR] Timed out waiting for PDF download in {download_dir}")
            return None
        time.sleep(1)

def run_eda_and_download_report(input_csv, dashboard_url, download_dir):
    print("[STEP] Starting EDA automation script.")
    if not input_csv or not os.path.isfile(input_csv):
        print(f"[ERROR] Dashboard analysis skipped: {input_csv!r} missing or invalid.")
        return None

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Uncomment and adjust prefs if your runner supports it
    # prefs = {
    #     "download.default_directory": download_dir,
    #     "download.prompt_for_download": False,
    #     "download.directory_upgrade": True,
    # }
    # options.add_experimental_option("prefs", prefs)

    driver = None
    try:
        print(f"[STEP] Launching WebDriver for dashboard: {dashboard_url}")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        print("[STEP] Waiting for dashboard branding in HTML...")
        driver.get(dashboard_url)
        dashboard_ready = False
        for i in range(120):
            if "Bogmayer Analytics Dashboard" in driver.page_source or "Upload Dataset" in driver.page_source:
                dashboard_ready = True
                print(f"[OK] Dashboard branding found at {i} seconds.")
                break
            time.sleep(1)
        if not dashboard_ready:
            print("[ERROR] Dashboard branding not found after 120 seconds.")
            with open("dashboard_title_debug.html", "w") as f:
                f.write(driver.page_source[:20000])
            return None

        print("[STEP] Waiting for file input visible...")
        wait = WebDriverWait(driver, 90)
        file_input = wait.until(EC.visibility_of_element_located((By.ID, "fileInput")))
        print("[OK] File input visible, sending file path.")
        file_input.send_keys(os.path.abspath(input_csv))

        print("[STEP] Waiting 15s for backend analysis...")
        time.sleep(15)

        print("[STEP] Clicking PDF report trigger button...")
        download_pdf_locator = (By.ID, "download-pdf")
        if not click_button_with_retry(driver, download_pdf_locator):
            with open("dashboard_analysis_trigger_debug.html", "w") as f:
                f.write(driver.page_source[:10000])
            return None

        print("[STEP] Clicking final PDF download button...")
        download_analysis_locator = (By.ID, "download-analysis-btn")
        if not click_button_with_retry(driver, download_analysis_locator, max_attempts=6, wait_seconds=5):
            with open("dashboard_final_debug.html", "w") as f:
                f.write(driver.page_source[:10000])
            return None

        print("[STEP] Waiting for PDF file to download...")
        pdf_file = wait_for_pdf_file(download_dir, timeout=120)
        if pdf_file:
            print(f"[SUCCESS] PDF downloaded: {pdf_file}")
            return pdf_file
        else:
            print("[ERROR] PDF download failed or timed out.")
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
