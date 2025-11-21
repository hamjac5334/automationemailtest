import os
import time
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager

def run_eda_and_download_report(input_csv, dashboard_url, download_dir):
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

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 60)

    try:
        driver.get(dashboard_url)

        with open("page_debug.html", "w") as f:
            f.write(driver.page_source)

        # Wait for and upload the CSV file
        file_input = wait.until(EC.visibility_of_element_located((By.ID, "fileInput")))
        file_input.send_keys(os.path.abspath(input_csv))

        # Wait for trigger button, scroll to it, and try clicking
        download_trigger = wait.until(EC.element_to_be_clickable((By.ID, "download-pdf")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_trigger)
        time.sleep(0.5)  # Give CSS transitions time if any
        try:
            download_trigger.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", download_trigger)

        # Wait for final download-analysis-btn, scroll and click
        download_btn = wait.until(EC.element_to_be_clickable((By.ID, "download-analysis-btn")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_btn)
        time.sleep(0.5)
        try:
            download_btn.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", download_btn)

        # Wait for the new PDF file to appear in download_dir (reuse your wait logic)
        pdf_file = wait_for_new_pdf(download_dir, timeout=60)
        return pdf_file

    finally:
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
            raise Exception("Timed out waiting for PDF download")
        time.sleep(2)
