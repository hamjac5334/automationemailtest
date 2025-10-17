import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def download_report_pdf(username, password, report_url, report_number=1):
    print(f"Downloading report #{report_number} from {report_url}...")

    # Create output directory
    download_dir = os.path.abspath("AutomatedEmailData")
    os.makedirs(download_dir, exist_ok=True)
    pdf_path = os.path.join(download_dir, f"Report_{time.strftime('%Y-%m-%d')}_{report_number}.pdf")

    # Set up Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Step 1: Log in
        driver.get("https://dsdlink.com/Login")
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "Username"))).send_keys(username)
        driver.find_element(By.ID, "Password").send_keys(password)
        driver.find_element(By.ID, "loginBtn").click()
        WebDriverWait(driver, 30).until(EC.url_contains("Home"))
        print("Logged in successfully.")

        # Step 2: Navigate to report page
        driver.get(report_url)
        time.sleep(5)  # wait for the page to load

        # Step 3: Get cookies from Selenium session
        session_cookies = driver.get_cookies()
        cookies_dict = {cookie['name']: cookie['value'] for cookie in session_cookies}

        # Step 4: Find PDF URL (network request)
        # For DSDLink, the print button usually triggers a URL like:
        # https://dsdlink.com/Report/Print?ReportID=XXXXX&Format=PDF
        # We'll construct it from the ReportID in the URL
        import urllib.parse as urlparse
        parsed = urlparse.urlparse(report_url)
        params = urlparse.parse_qs(parsed.query)
        report_id = params.get("ReportID", [None])[0]
        if not report_id:
            raise Exception("Could not find ReportID in URL")

        pdf_url = f"https://dsdlink.com/Report/Print?ReportID={report_id}&Format=PDF"

        # Step 5: Download PDF using requests with cookies
        response = requests.get(pdf_url, cookies=cookies_dict, stream=True)
        if response.status_code != 200:
            raise Exception(f"Failed to download PDF, status code {response.status_code}")

        with open(pdf_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        print(f"PDF saved: {pdf_path}")
        return pdf_path

    except Exception as e:
        print(f"Failed to download PDF: {e}")
        return None

    finally:
        driver.quit()

