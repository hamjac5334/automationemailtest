import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def init_driver():
    """Initialize headless Chrome WebDriver for GitHub Actions."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    return driver


def ensure_dir(path):
    """Ensure directory exists."""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def download_report(username, password, url):
    print("Downloading Sales Summary...")
    driver = init_driver()
    wait = WebDriverWait(driver, 20)

    try:
        print("Opening login page...")
        driver.get("https://dsdlink.com/Login")
        time.sleep(3)

        # Detect login form
        if "Login" in driver.current_url or "login" in driver.page_source.lower():
            try:
                username_elem = wait.until(EC.presence_of_element_located((By.ID, "ews-login-username")))
                password_elem = wait.until(EC.presence_of_element_located((By.ID, "ews-login-password")))
                login_btn = wait.until(EC.element_to_be_clickable((By.ID, "ews-login-submit")))

                username_elem.send_keys(username)
                password_elem.send_keys(password)
                login_btn.click()
                print("Logging in...")
                time.sleep(5)
            except TimeoutException:
                print("Login form not found — might already be logged in or redirected.")
        else:
            print("Already logged in.")

        # Navigate to the report page
        print(f"Navigating to report URL: {url}")
        driver.get(url)
        time.sleep(5)

        print("Locating export button...")

        # Wait for the ecp-btn to appear
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ecp-btn#ActionButtonExport")))

        # Access the shadow root and find the button
        export_btn = driver.execute_script("""
          const host = document.querySelector('ecp-btn#ActionButtonExport');
          return host && host.shadowRoot ? host.shadowRoot.querySelector('button') : null;
        """)

        if not export_btn:
            # Save page for debugging
            debug_dir = os.path.join(os.getcwd(), "AutomatedEmailData")
            ensure_dir(debug_dir)
            debug_path = os.path.join(debug_dir, "debug_page.html")
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"Saved page source to {debug_path} for debugging.")
            raise Exception("Could not find export button inside shadow root")

        # Click the button
        export_btn.click()
        print("Clicked export button successfully!")

        # Wait a bit for download to complete
        time.sleep(10)

        # Locate the downloaded file
        download_dir = os.path.join(os.getcwd(), "AutomatedEmailData")
        ensure_dir(download_dir)

        # This assumes Chrome downloads to /tmp or similar
        downloaded_files = [f for f in os.listdir("/tmp") if f.endswith(".xlsx") or f.endswith(".csv")]
        if not downloaded_files:
            raise Exception("No downloaded file found in /tmp directory")

        latest_file = max([os.path.join("/tmp", f) for f in downloaded_files], key=os.path.getmtime)
        final_path = os.path.join(download_dir, os.path.basename(latest_file))
        os.rename(latest_file, final_path)

        print(f"Report downloaded successfully: {final_path}")
        return final_path

    except Exception as e:
        debug_dir = os.path.join(os.getcwd(), "AutomatedEmailData")
        ensure_dir(debug_dir)
        debug_path = os.path.join(debug_dir, "debug_page.html")
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"Saved page source to {debug_path} for debugging.")
        raise e

    finally:
        driver.quit()

