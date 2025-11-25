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

def clean_download_dir(download_dir):
    for f in os.listdir(download_dir):
        if f.endswith('.pdf'):
            os.remove(os.path.join(download_dir, f))

def enable_chrome_headless_download(driver, download_dir):
    driver.execute_cdp_cmd(
        "Page.setDownloadBehavior",
        {"behavior": "allow", "downloadPath": os.path.abspath(download_dir)}
    )

def remove_overlays(driver):
    scripts = [
        "document.querySelectorAll('.modal-backdrop, .overlay, .spinner, .loader').forEach(e => e.remove())",
        "document.body.style.overflow = 'auto';"
    ]
    for script in scripts:
        driver.execute_script(script)
    print("[INFO] Removed possible blocking overlays.")

def click_button_wait_enabled_with_retry(driver, by_locator, max_attempts=8, wait_seconds=3):
    for attempt in range(max_attempts):
        try:
            wait = WebDriverWait(driver, 30)
            wait.until(EC.presence_of_element_located(by_locator))
            element = driver.find_element(*by_locator)
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

def wait_for_pdf_file(download_dir, known_files=None, timeout=120):
    print(f"[STEP] Waiting for a new PDF in {download_dir} (timeout={timeout}s)...")
    start_time = time.time()
    last_size = -1
    stable_since = None
    if known_files is None:
        known_files = set(os.listdir(download_dir))
    while True:
        downloading_files = [f for f in os.listdir(download_dir) if f.endswith('.crdownload')]
        pdf_files = [f for f in os.listdir(download_dir) if f.endswith('.pdf')]
        new_pdfs = set(pdf_files) - known_files
        if new_pdfs and len(downloading_files) == 0:
            for pf in new_pdfs:
                full_path = os.path.join(download_dir, pf)
                size = os.path.getsize(full_path)
                if size > 0:
                    if size == last_size:
                        if stable_since is None:
                            stable_since = time.time()
                        elif time.time() - stable_since > 2:
                            print(f"[OK] New PDF stable and ready: {full_path}")
                            return full_path
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

    clean_download_dir(download_dir)

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    prefs = {
        "download.default_directory": os.path.abspath(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "profile.default_content_setting_values.automatic_downloads": 1,
    }
    options.add_experimental_option("prefs", prefs)

    driver = None
    try:
        print(f"[STEP] Launching WebDriver for dashboard: {dashboard_url}")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        enable_chrome_headless_download(driver, download_dir)

        print("[STEP] Navigating to dashboard URL...")
        driver.get(dashboard_url)

        print(f"[DEBUG] Page source length after get: {len(driver.page_source)}")

        print("[STEP] Waiting for dashboard branding in HTML...")
        dashboard_ready = False
        for i in range(120):
            page_source = driver.page_source
            print(f"[DEBUG] Branding check loop {i} snippet: {page_source[:500]!r}")
            if "Bogmayer Analytics Dashboard" in page_source or "Upload Dataset" in page_source:
                dashboard_ready = True
                print(f"[OK] Dashboard branding found at {i} seconds.")
                break
            time.sleep(1)

        if not dashboard_ready:
            print("[ERROR] Dashboard branding not found after 120 seconds.")
            with open("dashboard_title_debug.html", "w") as f:
                f.write(driver.page_source[:20000])
            return None

        print("[STEP] Waiting for file input to be visible...")
        wait = WebDriverWait(driver, 90)
        file_input = wait.until(EC.visibility_of_element_located((By.ID, "fileInput")))
        print("[OK] File input visible, sending file path.")
        file_input.send_keys(os.path.abspath(input_csv))

        print("[STEP] Waiting for backend analysis (~15s)...")
        time.sleep(15)

        print("[STEP] Directory before download click:", os.listdir(download_dir))
        existing_files = set(os.listdir(download_dir))

        print("[STEP] Clicking dashboard PDF trigger button by ID...")
        download_pdf_locator = (By.ID, "download-pdf")
        if not click_button_wait_enabled_with_retry(driver, download_pdf_locator):
            with open("dashboard_pdf_click_fail.html", "w") as f:
                f.write(driver.page_source[:10000])
            return None

        print("[INFO] Clicked download button, waiting 10 seconds for download to start...")
        time.sleep(10)

        print("[STEP] Directory after download click:", os.listdir(download_dir))
        print("[STEP] Waiting for PDF file to be fully downloaded...")
        pdf_file = wait_for_pdf_file(download_dir, known_files=existing_files, timeout=120)
        if pdf_file:
            print(f"[SUCCESS] PDF downloaded and ready: {pdf_file}")
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

