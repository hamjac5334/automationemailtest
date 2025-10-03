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

# Where downloaded reports will be stored
DOWNLOAD_DIR = os.path.join(os.getcwd(), "AutomatedEmailData")

def download_reports(username, password, report_links):
    """
    Downloads multiple reports from DSDLink given full URLs.
    :param username: DSD username
    :param password: DSD password
    :param report_links: List of tuples [(url, filename_prefix), ...]
    :return: List of downloaded file paths
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    user_data_dir = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={user_data_dir}")

    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 30)
    downloaded_files = []

    try:
        # Login once
        driver.get("https://dsdlink.com/Home?DashboardID=185125")
        username_elem = wait.until(EC.presence_of_element_located((By.ID, "ews-login-username")))
        password_elem = wait.until(EC.presence_of_element_located((By.ID, "ews-login-password")))
        username_elem.send_keys(username)
        password_elem.send_keys(password, Keys.RETURN)
        time.sleep(5)

        # Loop over all report links
        for url, prefix in report_links:
            driver.get(url)
            time.sleep(5)

            # Click export to CSV
            export_btn_host = wait.until(EC.presence_of_element_located((By.ID, "ActionButtonExport")))
            export_btn_root = driver.execute_script("return arguments[0].shadowRoot", export_btn_host)
            download_btn = export_btn_root.find_element(By.CSS_SELECTOR, "button.button")
            download_btn.click()

            csv_option = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.ews-menu-item[format="CSV"]'))
            )
            csv_option.click()

            # Wait for download
            time.sleep(15)

            # Rename file
            original_filename = "Live_Inventory_Snapshot_automation_test.csv"  # adjust if export filename differs
            original_filepath = os.path.join(DOWNLOAD_DIR, original_filename)

            timeout = 30
            start_time = time.time()
            while not os.path.exists(original_filepath):
                time.sleep(1)
                if time.time() - start_time > timeout:
                    raise Exception(f"Download for {prefix} not found.")

            date_str = datetime.now().strftime("%Y-%m-%d")
            new_filename = f"{prefix}_{date_str}.csv"
            new_filepath = os.path.join(DOWNLOAD_DIR, new_filename)

            os.rename(original_filepath, new_filepath)
            downloaded_files.append(new_filepath)

    finally:
        driver.quit()

    return downloaded_files


