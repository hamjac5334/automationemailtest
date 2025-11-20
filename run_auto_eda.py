from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os

def run_eda_and_download_report(input_csv, dashboard_url, download_dir):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    prefs = {"download.default_directory": download_dir}
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(dashboard_url)
        # Wait for dashboard page to load
        time.sleep(3)  # or use selenium waits

        # 1. Upload the CSV
        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys(os.path.abspath(input_csv))

        # 2. Trigger analysis if needed
        button = driver.find_element(By.ID, 'download-pdf')
        button.click()

        # 3. Wait for analysis to finish and download to become available
        # Wait for download button to be enabled/appear, or poll download_dir
        time.sleep(20)  # or use better explicit waits

        # 4. Click download button
        download_btn = driver.find_element(By.ID, 'download-analysis-btn')
        download_btn.click()

        # 5. Wait for the pdf to appear in download_dir
        pdf_file = wait_for_new_pdf(download_dir, timeout=60)
        return pdf_file
    finally:
        driver.quit()

def wait_for_new_pdf(download_dir, timeout=60):
    start = time.time()
    while True:
        pdfs = [f for f in os.listdir(download_dir) if f.endswith('.pdf')]
        if pdfs:
            return os.path.join(download_dir, pdfs[0])  # Optionally grab newest
        if time.time() - start > timeout:
            raise Exception("Timed out waiting for PDF download")
        time.sleep(2)

