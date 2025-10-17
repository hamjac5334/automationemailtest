import os
import time
import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def download_report_pdf(username, password, report_url, report_number=1):
    print(f"Downloading report #{report_number} from {report_url}...")

    # Configure Chrome for saving PDFs
    download_dir = os.path.abspath("AutomatedEmailData")
    os.makedirs(download_dir, exist_ok=True)

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Enable saving PDFs automatically
    prefs = {
        "printing.print_preview_sticky_settings.appState": '{"recentDestinations": [{"id": "Save as PDF","origin": "local"}],"selectedDestinationId": "Save as PDF","version": 2}',
        "savefile.default_directory": download_dir
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--kiosk-printing")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Step 1: Login
        driver.get("https://dsdlink.com/Login")
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "Username"))).send_keys(username)
        driver.find_element(By.ID, "Password").send_keys(password)
        driver.find_element(By.ID, "loginBtn").click()
        WebDriverWait(driver, 30).until(EC.url_contains("Home"))
        print("✅ Logged in successfully.")

        # Step 2: Navigate to report
        driver.get(report_url)
        WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(5)  # Let dynamic content load

        # Step 3: Save the page as PDF
        pdf_path = os.path.join(download_dir, f"Report_{time.strftime('%Y-%m-%d')}_{report_number}.pdf")

        driver.execute_script("window.print();")
        time.sleep(3)  # Allow print-to-PDF to complete

        # Wait for file to appear
        timeout = 20
        for _ in range(timeout):
            files = [f for f in os.listdir(download_dir) if f.endswith(".pdf")]
            if files:
                latest_pdf = max([os.path.join(download_dir, f) for f in files], key=os.path.getctime)
                os.rename(latest_pdf, pdf_path)
                print(f"PDF saved as: {pdf_path}")
                return pdf_path
            time.sleep(1)

        raise Exception("Timed out waiting for PDF to be saved.")

    except Exception as e:
        print(f"Failed to download PDF: {e}")
        return None

    finally:
        driver.quit()
