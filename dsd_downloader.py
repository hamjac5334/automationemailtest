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

def download_report(username, password, url, max_wait_seconds=90):
    """
    Logs into DSDLink, opens a specific report URL, triggers CSV export,
    discovers the newly downloaded CSV file, renames it to Report_<ReportID>_<YYYY-MM-DD>.csv,
    and returns the new filepath.

    Parameters:
      - username (str): DSD username
      - password (str): DSD password
      - url (str): Full DSD report URL (contains ReportID=...)
      - max_wait_seconds (int): maximum time to wait for CSV to appear

    Returns:
      - new_filepath (str)
    """
    # Selenium/Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # headless for CI
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Create a temporary user data dir (helps in CI)
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
    wait = WebDriverWait(driver, 45)

    try:
        # Enable downloads in headless mode via Chrome DevTools Protocol
        # This must be done after driver is created
        driver.command_executor._commands["send_command"] = ("POST", "/session/$sessionId/chromium/send_command")
        params = {
            "cmd": "Page.setDownloadBehavior",
            "params": {"behavior": "allow", "downloadPath": DOWNLOAD_DIR},
        }
        driver.execute("send_command", params)

        # Step 1 — Log in
        print("Opening login page...")
        driver.get("https://dsdlink.com/Home?DashboardID=185125")
        username_elem = wait.until(EC.presence_of_element_located((By.ID, "ews-login-username")))
        password_elem = wait.until(EC.presence_of_element_located((By.ID, "ews-login-password")))
        username_elem.send_keys(username)
        password_elem.send_keys(password, Keys.RETURN)
        time.sleep(5)  # allow login to complete

        # Step 2 — Navigate to the report URL
        print(f"Navigating to report URL: {url}")
        driver.get(url)
        time.sleep(5)  # let the page render

        # Step 3 — Prepare to detect new file(s)
        before_files = set(os.listdir(DOWNLOAD_DIR))

        # Step 4 — Trigger export to CSV via the export button and shadow DOM
        print("Locating export button...")
        export_btn_host = wait.until(EC.presence_of_element_located((By.ID, "ActionButtonExport")))
        export_btn_root = driver.execute_script("return arguments[0].shadowRoot", export_btn_host)
        download_btn = export_btn_root.find_element(By.CSS_SELECTOR, "button.button")
        download_btn.click()

        print("Selecting CSV export option...")
        csv_option = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.ews-menu-item[format="CSV"]')))
        csv_option.click()

        print("CSV export initiated — waiting for new file to appear...")

        # Step 5 — Wait for a new .csv file to appear
        start_time = time.time()
        downloaded_filepath = None

        while time.time() - start_time < max_wait_seconds:
            time.sleep(1.5)
            all_files = set(os.listdir(DOWNLOAD_DIR))
            new_files = all_files - before_files
            # filter for csvs in new_files
            new_csvs = [f for f in new_files if f.lower().endswith(".csv")]
            if new_csvs:
                # pick the most recently modified among these new csvs
                new_csv_paths = [os.path.join(DOWNLOAD_DIR, f) for f in new_csvs]
                downloaded_filepath = max(new_csv_paths, key=os.path.getmtime)
                break

        if not downloaded_filepath:
            # As a fallback, check for any csv created/modified in the time window
            csv_candidates = [os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR) if f.lower().endswith(".csv")]
            if csv_candidates:
                downloaded_filepath = max(csv_candidates, key=os.path.getmtime)

        if not downloaded_filepath:
            raise Exception(f"Download timeout for {url} — no new CSV detected after {max_wait_seconds} seconds.")

    except Exception as e:
        # Try to capture a small HTML snapshot for debugging (if possible)
        try:
            debug_html = os.path.join(DOWNLOAD_DIR, "debug_page.html")
            with open(debug_html, "w", encoding="utf-8") as fh:
                fh.write(driver.page_source)
            print(f"Saved page source to {debug_html} for debugging.")
        except Exception:
            pass
        driver.quit()
        raise

    finally:
        # ensure driver quits (if not already)
        try:
            driver.quit()
        except Exception:
            pass

    # Step 6 — Rename the downloaded file to a consistent name using ReportID and date
    report_id = url.split("ReportID=")[-1].split("&")[0]
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_new_filename = f"Report_{report_id}_{date_str}.csv"
    new_filepath = os.path.join(DOWNLOAD_DIR, safe_new_filename)

    # If a file with the target name already exists, add a timestamp suffix
    if os.path.exists(new_filepath):
        ts = datetime.now().strftime("%H%M%S")
        new_filepath = os.path.join(DOWNLOAD_DIR, f"Report_{report_id}_{date_str}_{ts}.csv")

    os.rename(downloaded_filepath, new_filepath)
    print(f"Downloaded and renamed to: {new_filepath}")
    return new_filepath
