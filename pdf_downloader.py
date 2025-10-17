import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def download_report_pdf(username, password, report_url, report_number=1):
    print(f"Downloading report #{report_number} from {report_url}...")

    # Directory to save PDFs
    download_dir = os.path.abspath("AutomatedEmailData")
    os.makedirs(download_dir, exist_ok=True)

    # Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--kiosk-printing")  # Automatically selects Print to PDF
    # Optional: set a custom profile if needed
    # chrome_options.add_argument("--user-data-dir=/path/to/chrome/profile")

    # Start Chrome (non-headless)
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Step 1: Login
        driver.get("https://dsdlink.com/Login")
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "Username"))).send_keys(username)
        driver.find_element(By.ID, "Password").send_keys(password)
        driver.find_element(By.ID, "loginBtn").click()
        WebDriverWait(driver, 30).until(EC.url_contains("Home"))
        print("Logged in successfully.")

        # Step 2: Navigate to report
        driver.get(report_url)
        print("Waiting for report to load...")
        time.sleep(10)  # Wait for the iframe and content to fully render

        # Step 3: Trigger print dialog and save as PDF
        # Chrome headless cannot use printToPDF here, so we rely on kiosk-printing mode
        pdf_path = os.path.join(download_dir, f"Report_{time.strftime('%Y-%m-%d')}_{report_number}.pdf")
        driver.execute_script('window.print();')
        print(f"PDF should be saved automatically in Chrome default download folder: {pdf_path}")

        # NOTE: You might need to manually move it from default downloads folder
        # or configure Chrome profile to automatically save PDFs to `download_dir`

        return pdf_path

    except Exception as e:
        print(f"Failed to download PDF: {e}")
        return None

    finally:
        # Keep Chrome open for manual inspection if needed
        time.sleep(5)
        driver.quit()
