import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import base64

DOWNLOAD_DIR = os.path.join(os.getcwd(), "AutomatedEmailData")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_report_pdf(username, password, report_url, filename="Report.pdf"):
    """
    Logs into DSDLink, navigates to the given report URL,
    generates a PDF using Chrome DevTools, and saves it locally.
    """

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Enable printing to PDF in headless mode
    chrome_options.add_argument("--kiosk-printing")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        print("Opening login page...")
        driver.get("https://dsdlink.com/Home?DashboardID=185125")
        time.sleep(3)

        try:
            # Try to log in (if not already logged in)
            username_elem = wait.until(EC.presence_of_element_located((By.ID, "ews-login-username")))
            password_elem = wait.until(EC.presence_of_element_located((By.ID, "ews-login-password")))
            username_elem.send_keys(username)
            password_elem.send_keys(password, Keys.RETURN)
            print("Logged in successfully.")
            time.sleep(5)
        except:
            print("Already logged in or login not required.")

        # Navigate to the specific report
        print(f"Navigating to report URL: {report_url}")
        driver.get(report_url)
        time.sleep(5)

        # Wait for the export button to confirm page loaded
        wait.until(EC.presence_of_element_located((By.ID, "ActionButtonExport")))
        print("Page ready. Generating PDF...")

        # Use Chrome DevTools Protocol to generate PDF
        pdf_data = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,
            "landscape": False
        })

        # Decode Base64 and save the PDF file
        pdf_bytes = base64.b64decode(pdf_data['data'])
        pdf_path = os.path.join(DOWNLOAD_DIR, filename)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

        print(f"PDF saved to: {pdf_path}")
        return pdf_path

    except Exception as e:
        print(f"Failed to download PDF: {e}")
        return None

    finally:
        driver.quit()
