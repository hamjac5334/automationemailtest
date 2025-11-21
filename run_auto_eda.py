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
    if not input_csv or not os.path.isfile(input_csv):
        print(f"Dashboard analysis skipped: {input_csv!r} is missing or not a valid file.")
        return None

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    user_data_dir = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={user_data_dir}")
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
    }
    options.add_experimental_option("prefs", prefs)

    driver = None
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )
        wait = WebDriverWait(driver, 60)
        print(f"Navigating to dashboard: {dashboard_url}")
        driver.get(dashboard_url)
        with open("page_debug.html", "w") as f:
            f.write(driver.page_source)

        # Locate the file input directly—do not click the upload button!
        try:
            file_input = wait.until(EC.visibility_of_element_located((By.ID, "fileInput")))
            # If the input is hidden, unhide it with JS:
            if not file_input.is_displayed():
                driver.execute_script("arguments[0].style.display = 'block';", file_input)
            file_input.send_keys(os.path.abspath(input_csv))
            print("CSV path sent to file input.")
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Could not find dashboard file input: {e!r}")
            return None

        # Continue as before: click download trigger button
        try:
            download_trigger = wait.until(EC.element_to_be_clickable((By.ID, "download-pdf")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_trigger)
            time.sleep(0.5)
            try:
                download_trigger.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", download_trigger)
            print("Triggered dashboard PDF analysis.")
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Could not click dashboard analysis trigger: {e!r}")
            return None

        # Click final PDF download button
        try:
            download_btn = wait.until(EC.element_to_be_clickable((By.ID, "download-analysis-btn")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_btn)
            time.sleep(0.5)
            try:
                download_btn.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", download_btn)
            print("Clicked dashboard PDF download button.")
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Could not click dashboard download button: {e!r}")
            return None

        # Wait for the new PDF file to appear
        pdf_file = wait_for_new_pdf(download_dir, timeout=60)
        if pdf_file:
            print(f"Downloaded dashboard PDF: {pdf_file}")
            return pdf_file
        else:
            print("PDF download did not complete or file missing.")
            return None

    except Exception as e:
        print("Unexpected error in analytics automation:", repr(e))
        traceback.print_exc()
        if driver is not None:
            with open("dashboard_error.html", "w") as f:
                f.write(driver.page_source)
        return None
    finally:
        if driver is not None:
            driver.quit()

def wait_for_new_pdf(download_dir, timeout=60):
    start = time.time()
    while True:
        pdfs = [f for f in os.listdir(download_dir) if f.endswith('.pdf')]
        if pdfs:
            full_path = os.path.join(download_dir, pdfs[0])
            if os.path.getsize(full_path) > 0:
                return full_path
        if time.time() - start > timeout:
            print("Timed out waiting for PDF download in:", download_dir)
            return None
        time.sleep(2)
