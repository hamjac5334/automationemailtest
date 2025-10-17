import os
import time
import base64
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def download_report_pdf(username, password, report_url, report_number=1):
    print(f"Downloading report #{report_number} from {report_url}...")

    download_dir = os.path.abspath("AutomatedEmailData")
    os.makedirs(download_dir, exist_ok=True)

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Step 1: Login
        driver.get("https://dsdlink.com/Login")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "Username"))
        ).send_keys(username)
        driver.find_element(By.ID, "Password").send_keys(password)
        driver.find_element(By.ID, "loginBtn").click()
        WebDriverWait(driver, 30).until(EC.url_contains("Home"))
        print("Logged in successfully.")

        # Step 2: Navigate to report
        driver.get(report_url)
        print("Waiting for report iframe or content to load...")
        time.sleep(5)

        # Step 3: Get cookies to replicate session
        cookies = driver.get_cookies()
        session = requests.Session()
        for c in cookies:
            session.cookies.set(c['name'], c['value'])

        # Step 4: Intercept network requests to find PDF
        logs = driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd("Network.clearBrowserCache", {})

        pdf_url = None
        # Wait and check network requests for PDF
        for _ in range(10):
            events = driver.execute_cdp_cmd("Network.getResponseBody", {})
            # Actually, simpler: check page for links ending in PDF
            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href")
                if href and ".pdf" in href.lower():
                    pdf_url = href
                    break
            if pdf_url:
                break
            time.sleep(1)

        if not pdf_url:
            raise Exception("Could not find PDF link in report page.")

        # Step 5: Download PDF with requests
        response = session.get(pdf_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download PDF from {pdf_url}")

        pdf_path = os.path.join(download_dir, f"Report_{time.strftime('%Y-%m-%d')}_{report_number}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(response.content)

        print(f"PDF saved: {pdf_path}")
        return pdf_path

    except Exception as e:
        print(f"Failed to download PDF: {e}")
        return None

    finally:
        driver.quit()
