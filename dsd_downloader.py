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

def download_report(username, password):
    options = webdriver.ChromeOptions()
    
    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True
    }
    options.add_experimental_option("prefs", prefs)

    # Headless new
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    temp_user_data_dir = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={temp_user_data_dir}")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    wait = WebDriverWait(driver, 30)

    try:
        # Login page
        driver.get("https://dsdlink.com/Home?DashboardID=185125")
        username_elem = wait.until(EC.presence_of_element_located((By.ID, "ews-login-username")))
        password_elem = wait.until(EC.presence_of_element_located((By.ID, "ews-login-password")))
        username_elem.send_keys(username)
        password_elem.send_keys(password, Keys.RETURN)
        time.sleep(5)

        # Navigate to report page
        driver.get("https://dsdlink.com/Home?DashboardID=100120&ReportID=22656753")
        time.sleep(5)

        # Click export button inside shadow DOM
        export_btn_host = wait.until(EC.presence_of_element_located((By.ID, "ActionButtonExport")))
        export_btn_root = driver.execute_script("return arguments[0].shadowRoot", export_btn_host)
        download_btn = export_btn_root.find_element(By.CSS_SELECTOR, "button.button")
        download_btn.click()

        # Click CSV 
        csv_option = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '.ews-menu-item[format="CSV"]'))
        )
        csv_option.click()
        time.sleep(15)

    finally:
        driver.quit()

    # Rename downloaded file
    original_filename = "Sales_By_Brand_&_124_Month-_pipeline_experiment.csv"
    original_filepath = os.path.join(DOWNLOAD_DIR, original_filename)

    timeout = 30
    start_time = time.time()
    while not os.path.exists(original_filepath):
        time.sleep(1)
        if time.time() - start_time > timeout:
            raise Exception("Download file not found.")

    date_str = datetime.now().strftime("%Y-%m-%d")
    new_filename = f"Report_{date_str}.csv"
    new_filepath = os.path.join(DOWNLOAD_DIR, new_filename)

    os.rename(original_filepath, new_filepath)
    return new_filepath

