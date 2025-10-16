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

def download_report(username, password, url):
    """
    Logs into DSDLink, downloads a specific report, and renames it.
    """

    # Setup Selenium
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

    try:
        # Step 1 — Go to login page
        print("Opening login page...")
        driver.get("https://dsdlink.com/Login")

        # Wait for either login inputs or dashboard (if already logged in)
        time.sleep(3)
        if "Login" in driver.current_url:
            try:
                username_elem = wait.until(EC.presence_of_element_located((By.ID, "ews-login-username")))
                password_elem = driver.find_element(By.ID, "ews-login-password")
                username_elem.send_keys(username)
                password_elem.send_keys(password)
                password_elem.send_keys(Keys.RETURN)
                print("Login submitted.")
                time.sleep(7)
            except Exception:
                print("Login form not found. Maybe already logged in.")
        else:
            print("Already logged in.")

        # Verify login worked
        if "Login" in driver.current_url:
            raise Exception("Login failed — still on login page.")

        # Step 2 — Navigate to the specific report
        print(f"Navigating to report URL: {url}")
        driver.get(url)
        time.sleep(7)

        # Verify page actually loaded the report
        if "Login" in driver.current_url:
            raise Exception("Session expired — redirected back to login page.")

        # Step 3 — Export the report
        print("Locating export button...")
        export_btn_host = wait.until(EC.presence_of_element_located((By.ID, "ActionButtonExport")))
        export_btn_root = driver.execute_script("return arguments[0].shadowRoot", export_btn_host)
        download_btn = export_btn_root.find_element(By.CSS_SELECTOR, "button.button")
        download_btn.click()

        # Step 4 — Click CSV option
        csv_option = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.ews-menu-item[format="CSV"]')))
        csv_option.click()
        print("CSV export clicked.")
        time.sleep(15)

        # Step 5 — Rename the most recent CSV file
        csv_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".csv")]
        if not csv_files:
            raise Exception(f"No CSV downloaded for {url}")

        latest_file = max(
            [os.path.join(DOWNLOAD_DIR, f) for f in csv_files],
            key=os.path.getctime
        )

        date_str = datetime.now().strftime("%Y-%m-%d")
        report_id = url.split("ReportID=")[-1]
        new_filename = f"Report_{report_id}_{date_str}.csv"
        new_filepath = os.path.join(DOWNLOAD_DIR, new_filename)
        os.rename(latest_file, new_filepath)
        print(f"Saved as {new_filename}")

        return new_filepath

    except Exception as e:
        debug_path = os.path.join(DOWNLOAD_DIR, "debug_page.html")
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"Saved page source to {debug_path} for debugging.")
        raise e

    finally:
        driver.quit()
