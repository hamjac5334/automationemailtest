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

# Directory to store downloaded reports
DOWNLOAD_DIR = os.path.join(os.getcwd(), "AutomatedEmailData")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_report(username, password, url):
    """
    Logs into DSDLink, opens a specific report URL, downloads the CSV,
    and renames it using the report's ID and current date.
    """

    # Setup Chrome WebDriver in headless mode
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    user_data_dir = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={user_data_dir}")

    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 30)

    try:
        # Step 1 — Log in
        driver.get("https://dsdlink.com/Home?DashboardID=185125")
        username_elem = wait.until(EC.presence_of_element_located((By.ID, "ews-login-username")))
        password_elem = wait.until(EC.presence_of_element_located((By.ID, "ews-login-password")))
        username_elem.send_keys(username)
        password_elem.send_keys(password, Keys.RETURN)
        time.sleep(6)

        # Step 2 — Navigate to the specific report URL
        driver.get(url)
        time.sleep(6)

        # Step 3 — Export as CSV
        export_btn_host = wait.until(EC.presence_of_element_located((By.ID, "ActionButtonExport")))
        export_btn_root = driver.execute_script("return arguments[0].shadowRoot", export_btn_host)
        download_btn = export_btn_root.find_element(By.CSS_SELECTOR, "button.button")
        download_btn.click()

        csv_option = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.ews-menu-item[format="CSV"]')))
        csv_option.click()
        print(f"Downloading CSV from: {url}")

        # Wait for file to fully download
        time.sleep(20)

    finally:
        driver.quit()

    # Step 4 — Find the downloaded file
    original_filename = "Live_Inventory_Snapshot_automation_test.csv"
    original_filepath = os.path.join(DOWNLOAD_DIR, original_filename)

    timeout = 60
    start_time = time.time()
    while not os.path.exists(original_filepath):
        time.sleep(1)
        if time.time() - start_time > timeout:
            raise Exception(f"Download timeout for {url}")

    # Step 5 — Rename file using ReportID
    report_id = url.split("ReportID=")[-1]
    date_str = datetime.now().strftime("%Y-%m-%d")
    new_filename = f"Report_{report_id}_{date_str}.csv"
    new_filepath = os.path.join(DOWNLOAD_DIR, new_filename)
    os.rename(original_filepath, new_filepath)

    print(f"Downloaded and renamed to: {new_filename}")
    return new_filepath

