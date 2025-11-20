import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def wait_for_file_complete(directory, extension=".pdf", timeout=60):
    end_time = time.time() + timeout
    file_path = None
    last_size = -1
    stable_counter = 0
    while time.time() < end_time:
        files = [f for f in os.listdir(directory) if f.endswith(extension)]
        if files:
            latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(directory, f)))
            full_path = os.path.join(directory, latest_file)
            current_size = os.path.getsize(full_path)
            if current_size == last_size:
                stable_counter += 1
                if stable_counter >= 3:  # File size stable for 3 cycles (6 seconds)
                    return full_path
            else:
                stable_counter = 0
            last_size = current_size
        time.sleep(2)
    raise Exception("Timed out waiting for completed PDF file")

def run_eda_and_download_report(input_csv, dashboard_url, download_dir):
    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": download_dir}
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(dashboard_url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys(os.path.abspath(input_csv))

        # Wait for and click button to initiate analysis
        button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, 'download-pdf')))
        button.click()

        # Wait for analysis completion/download button enabled
        download_btn = WebDriverWait(driver, 40).until(EC.element_to_be_clickable((By.ID, 'download-analysis-btn')))
        download_btn.click()

        # Wait for the file to finish downloading
        pdf_file = wait_for_file_complete(download_dir, timeout=60)
        return pdf_file
    finally:
        driver.quit()
