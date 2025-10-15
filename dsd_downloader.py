# dsd_downloader.py
import os
import time
import tempfile
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

DOWNLOAD_DIR = os.path.join(os.getcwd(), "AutomatedEmailData")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_reports(username, password, reports):
    """
    Download multiple reports in a single browser session.
    Returns a list of downloaded file paths.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Temporary user data dir
    user_data_dir = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={user_data_dir}")

    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 60)
    downloaded_files = []

    try:
        # Login once
        print("Opening DSDLink login page...")
        driver.get("https://dsdlink.com/Home?DashboardID=185125")

        username_elem = wait.until(EC.presence_of_element_located((By.ID, "ews-login-username")))
        password_elem = wait.until(EC.presence_of_element_located((By.ID, "ews-login-password")))
        username_elem.send_keys(username)
        password_elem.send_keys(password, Keys.RETURN)

        # Give page time to load after login
        time.sleep(5)

        for r in reports:
            print(f"Downloading {r['name']}...")

            # Navigate to the report
            driver.get(r["url"])
            time.sleep(5)  # wait for page to load

            # Click export button via shadow DOM
            export_btn_host = wait.until(EC.presence_of_element_located((By.ID, "ActionButtonExport")))
            export_btn_root = driver.execute_script("return arguments[0].shadowRoot", export_btn_host)
            download_btn = export_btn_root.find_element(By.CSS_SELECTOR, "button.button")
            download_btn.click()

            csv_option = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.ews-menu-item[format="CSV"]'))
            )
            csv_option.click()

            print("CSV export initiated, waiting for download...")

            # Wait for the file to appear
            original_filename = "Live_Inventory_Snapshot_automation_test.csv"
            original_filepath = os.path.join(DOWNLOAD_DIR, original_filename)

            timeout = 60
            start_time = time.time()
            while not os.path.exists(original_filepath):
                time.sleep(1)
                if time.time() - start_time > timeout:
                    raise Exception(f"Download file not found for {r['name']}.")

            # Rename file
            date_str = datetime.now().strftime("%Y-%m-%d")
            new_filename = f"{r['name']}_{date_str}.csv"
            new_filepath = os.path.join(DOWNLOAD_DIR, new_filename)
            os.rename(original_filepath, new_filepath)
            downloaded_files.append(new_filepath)
            print(f"Report saved as: {new_filepath}")

    finally:
        driver.quit()

    return downloaded_files
