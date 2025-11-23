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

def run_eda_and_download_report(input_csv, dashboard_url, download_dir):
    print("[STEP] Starting EDA automation script.")
    if not input_csv or not os.path.isfile(input_csv):
        print(f"[ERROR] Dashboard analysis skipped: {input_csv!r} is missing or not a valid file.")
        return None

    options = webdriver.ChromeOptions()
    # Always use headless in CI or container
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Remove user-agent/string flags, window size, user-data-dir for reliability

    # Optionally, use default download directory in CI
    # If download_dir is valid and writable, you can keep this block:
    # Otherwise, remove for maximum reliability in hosted runners
    # prefs = {
    #     "download.default_directory": download_dir,
    #     "download.prompt_for_download": False,
    #     "download.directory_upgrade": True,
    # }
    # options.add_experimental_option("prefs", prefs)

    driver = None
    try:
        print(f"[STEP] Launching WebDriver and navigating to dashboard: {dashboard_url}")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )

        print("[STEP] Waiting for HTML to contain dashboard branding...")
        driver.get(dashboard_url)
        dashboard_ready = False
        for i in range(120):
            page_source = driver.page_source
            if "Bogmayer Analytics Dashboard" in page_source or "Upload Dataset" in page_source:
                dashboard_ready = True
                print("[OK] Found dashboard branding in HTML at", i, "seconds.")
                break
            time.sleep(1)
        if not dashboard_ready:
            print("[ERROR] Dashboard page HTML does NOT contain dashboard branding after 120s, saving debug output.")
            with open("dashboard_title_debug.html", "w") as f:
                f.write(driver.page_source[:20000])
            return None

        print("[STEP] Waiting for file input element to be visible...")
        wait = WebDriverWait(driver, 90)
        try:
            file_input = wait.until(EC.visibility_of_element_located((By.ID, "fileInput")))
            print("[OK] File input element found and visible.")
        except (TimeoutException, NoSuchElementException) as e:
            print(f"[ERROR] Could not find dashboard file input: {e!r}")
            with open("dashboard_fileinput_debug.html", "w") as f:
                f.write(driver.page_source[:10000])
            return None

        print(f"[STEP] Sending file path to dashboard file input: {input_csv}")
        file_input.send_keys(os.path.abspath(input_csv))
        print("[OK] File path sent. Dashboard should process/upload the file.")

        print("[STEP] Waiting for backend analysis (~15s) to finish...")
        time.sleep(15)
        print("[OK] Backend analysis sleep complete; proceeding to report download triggers.")

        print("[STEP] Waiting for dashboard PDF trigger button to be clickable...")
        try:
            download_trigger = WebDriverWait(driver, 90).until(
                EC.element_to_be_clickable((By.ID, "download-pdf")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_trigger)
            time.sleep(0.5)
            try:
                download_trigger.click()
                print("[OK] Dashboard PDF analysis trigger button clicked.")
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", download_trigger)
                print("[WARN] Intercepted click, used JavaScript to click PDF trigger.")
        except (TimeoutException, NoSuchElementException) as e:
            print(f"[ERROR] Could not click dashboard analysis trigger: {e!r}")
            with open("dashboard_analysis_trigger_debug.html", "w") as f:
                f.write(driver.page_source[:10000])
            return None

        print("[STEP] Waiting for final PDF download button to appear and become clickable...")
        try:
            wait_download = WebDriverWait(driver, 120)
            wait_download.until(EC.presence_of_element_located((By.ID, "download-analysis-btn")))
            download_btn = wait_download.until(EC.element_to_be_clickable((By.ID, "download-analysis-btn")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_btn)
            time.sleep(0.5)
            try:
                download_btn.click()
                print("[OK] Final dashboard PDF download button clicked.")
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", download_btn)
                print("[WARN] Intercepted click, used JavaScript to click final PDF button.")
        except (TimeoutException, NoSuchElementException) as e:
            print(f"[ERROR] Could not click dashboard download button: {e!r}")
            with open("dashboard_final_debug.html", "w") as f:
                f.write(driver.page_source[:10000])
            return None

        print("[STEP] Waiting for new PDF to appear at:", download_dir)
        pdf_file = wait_for_new_pdf(download_dir, timeout=90)
        if pdf_file:
            print(f"[SUCCESS] Downloaded dashboard PDF: {pdf_file}")
            return pdf_file
        else:
            print("[ERROR] PDF download did not complete or file missing.")
            return None

    except Exception as e:
        print("[FATAL ERROR] Unexpected error in analytics automation:", repr(e))
        traceback.print_exc()
        if driver is not None:
            with open("dashboard_error.html", "w") as f:
                f.write(driver.page_source[:10000])
        return None
    finally:
        print("[STEP] Cleaning up: Quitting WebDriver.")
        if driver is not None:
            driver.quit()

def wait_for_new_pdf(download_dir, timeout=90):
    print(f"[STEP] Waiting for new PDF in {download_dir} (timeout={timeout}s)...")
    start = time.time()
    while True:
        pdfs = [f for f in os.listdir(download_dir) if f.endswith('.pdf')]
        if pdfs:
            full_path = os.path.join(download_dir, pdfs[0])
            if os.path.getsize(full_path) > 0:
                print(f"[STEP] Found non-empty PDF: {full_path}")
                return full_path
        if time.time() - start > timeout:
            print("[ERROR] Timed out waiting for PDF download in:", download_dir)
            return None
        time.sleep(2)


