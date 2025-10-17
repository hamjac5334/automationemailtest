import os
import time
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
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
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--remote-allow-origins=*")

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
        print("Waiting for report page to fully load...")

        # Wait for body to be present
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Extra wait to allow charts, iframes, and JS-rendered content
        time.sleep(10)

        # Step 3: Generate PDF
        pdf_data = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,
            "landscape": False,
            "paperWidth": 8.27,   # A4 size width in inches
            "paperHeight": 11.69  # A4 size height in inches
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
