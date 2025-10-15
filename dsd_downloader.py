# dsd_downloader.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

def download_reports(username, password, reports):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    wait = WebDriverWait(driver, 60)

    downloaded_files = []

    # Login once
    driver.get("https://dsdlink.com/Home")
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.ID, "loginButton").click()

    time.sleep(5)  # let page fully load

    # Loop through reports (limit to 2)
    for r in reports[:2]:
        print(f"Downloading {r['name']}...")
        driver.get(r['url'])  # navigate to report
        # Wait for download button to appear
        wait.until(EC.element_to_be_clickable((By.ID, "downloadButton"))).click()
        time.sleep(5)  # wait for download to finish
        downloaded_files.append(r['name'])

        # Navigate back to main dashboard
        driver.get("https://dsdlink.com/Home")
        time.sleep(3)

    driver.quit()
    return downloaded_files
