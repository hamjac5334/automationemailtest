import os
import time
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def download_report_pdf(username, password, report_url, report_number=1):
    """
    Downloads a DSD report as a PDF using headless Chrome and Chrome DevTools Protocol.

    Returns the path to the saved PDF, or None on failure.
    """
    print(f"Downloading report #{report_number} from {report_url}...")

    download_dir = os.path.abspath("AutomatedEmailData")
    os.makedirs(download_dir, exist_ok=True)

    # Setup headless Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--user-data-dir={os.path.join(download_dir, f'user_data_{report_number}')}")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-infobars")

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
        print("Waiting for report iframe to load...")
        time.sleep(5)  # Let page and scripts load

        # Wait for iframe and switch into it
        iframe = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
        driver.switch_to.frame(iframe)

        # Wait for report content to appear
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
        time.sleep(5)
        print("Report content loaded. Generating PDF...")

        # Step 3: Use Chrome DevTools Protocol to generate PDF
        pdf_data = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,
            "landscape": False
        })

        pdf_bytes = base64.b64decode(pdf_data['data'])
        pdf_path = os.path.join(download_dir, f"Report_{time.strftime('%Y-%m-%d')}_{report_number}.pdf")

        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

        print(f"PDF saved: {pdf_path}")
        return pdf_path

    except Exception as e:
        print(f"Failed to download PDF: {e}")
        return None

    finally:
        driver.quit()
