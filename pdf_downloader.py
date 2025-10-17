import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def download_report_pdf(username, password, report_url, report_number=1):
    print("Opening login page...")

    # Configure Chrome for PDF output
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Login
        driver.get("https://dsdlink.com/Login")
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "Username"))).send_keys(username)
        driver.find_element(By.ID, "Password").send_keys(password)
        driver.find_element(By.ID, "loginBtn").click()

        WebDriverWait(driver, 30).until(EC.url_contains("Home"))
        print("Logged in successfully.")

        # Navigate to report
        print(f"Navigating to report URL: {report_url}")
        driver.get(report_url)

        # Wait for export menu item
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Print (PDF)')]")))
        print("Page ready, generating PDF...")

        # Create output directory
        output_dir = "AutomatedEmailData"
        os.makedirs(output_dir, exist_ok=True)
        pdf_path = os.path.join(output_dir, f"Report_{time.strftime('%Y-%m-%d')}_{report_number}.pdf")

        # Use Chrome DevTools Protocol to save page as PDF
        result = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,
            "landscape": False
        })

        with open(pdf_path, "wb") as f:
            f.write(bytes(result['data'], encoding="base64"))

        print(f"PDF saved to: {pdf_path}")
        return pdf_path

    except Exception as e:
        print(f"Failed to download PDF: {e}")
        return None
    finally:
        driver.quit()
