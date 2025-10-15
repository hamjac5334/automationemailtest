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

# Directory where all reports will be stored
DOWNLOAD_DIR = os.path.join(os.getcwd(), "AutomatedEmailData")

def download_report(username, password, report_name, report_url):
    options = webdriver.ChromeOptions()

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Create a temporary user data directory
    user_data_dir = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={user_data_dir}")

    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(180)
    wait = WebDriverWait(driver, 30)

    try:
        # Open DSDLink home (to load login page)
        print(f"Opening DSDLink for {report_name}...")
        driver.get("https://dsdlink.com/Home?DashboardID=185125")

        # Log in
        username_elem = wait.until(EC.presence_of_element_located((By.ID, "ews-login-username")))
        password_elem = wait.until(EC.presence_of_element_located((By.ID, "ews-login-password")))
        username_elem.send_keys(username)
        password_elem.send_keys(password, Keys.RETURN)
        time.sleep(5)

        # Open the report URL
        print(f"Navigating to report: {report_url}")
        driver.get(report_url)
        time.sleep(5)

        # Click export button
        export_btn_host = wait.until(EC.presence_of_element_located((By.ID, "ActionButtonExport")))
        export_btn_root = driver.execute_script("return arguments[0].shadowRoot", export_btn_host)
        download_btn = export_btn_root.find_element(By.CSS_SELECTOR, "button.button")
        download_btn.click()

        csv_option = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '.ews-menu-item[format="CSV"]'))
        )
        csv_option.click()

        print("CSV export initiated. Waiting for download to complete...")
        time.sleep(20)  # Wait for download

    finally:
        driver.quit()

    # The default filename DSDLink uses
    original_filename = "Live_Inventory_Snapshot_automation_test.csv"
    original_filepath = os.path.join(DOWNLOAD_DIR, original_filename)

    # Wait for file to appear
    timeout = 30
    start_time = time.time()
    while not os.path.exists(original_filepath):
        time.sleep(1)
        if time.time() - start_time > timeout:
            raise Exception(f"Download file not found for {report_name}.")

    # Rename the file to include report name and date
    date_str = datetime.now().strftime("%Y-%m-%d")
    new_filename = f"{report_name}_{date_str}.csv"
    new_filepath = os.path.join(DOWNLOAD_DIR, new_filename)
    os.rename(original_filepath, new_filepath)

    print(f"Report saved as: {new_filepath}")
    return new_filepath

