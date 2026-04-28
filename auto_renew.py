import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EMAIL = os.environ.get("EMAIL")
PASSWORD = os.environ.get("PASSWORD")
LOGIN_URL = "https://tickhosting.com/auth/login"
SERVERS_URL = "https://tickhosting.com/freeservers"

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def login(driver):
    logger.info("Navigating to login page...")
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 20)

    # Wait for page to fully load
    time.sleep(3)

    # Try to find email field by various selectors
    email_selectors = [
        (By.NAME, "email"),
        (By.ID, "email"),
        (By.CSS_SELECTOR, "input[type='email']"),
        (By.CSS_SELECTOR, "input[placeholder*='email' i]"),
        (By.CSS_SELECTOR, "input[placeholder*='Email' i]"),
    ]

    email_field = None
    for by, selector in email_selectors:
        try:
            email_field = wait.until(EC.presence_of_element_located((by, selector)))
            logger.info(f"Found email field with selector: {selector}")
            break
        except TimeoutException:
            continue

    if not email_field:
        logger.error("Could not find email input field")
        logger.info(f"Page source snippet: {driver.page_source[:2000]}")
        return False

    # Find password field
    password_selectors = [
        (By.NAME, "password"),
        (By.ID, "password"),
        (By.CSS_SELECTOR, "input[type='password']"),
    ]

    password_field = None
    for by, selector in password_selectors:
        try:
            password_field = driver.find_element(by, selector)
            logger.info(f"Found password field with selector: {selector}")
            break
        except NoSuchElementException:
            continue

    if not password_field:
        logger.error("Could not find password input field")
        return False

    # Fill in credentials
    email_field.clear()
    email_field.send_keys(EMAIL)
    time.sleep(0.5)
    password_field.clear()
    password_field.send_keys(PASSWORD)
    time.sleep(0.5)

    # Find and click submit button
    submit_selectors = [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.XPATH, "//button[contains(text(), 'Login')]"),
        (By.XPATH, "//button[contains(text(), 'Sign in')]"),
        (By.XPATH, "//input[@type='submit']"),
    ]

    submitted = False
    for by, selector in submit_selectors:
        try:
            btn = driver.find_element(by, selector)
            btn.click()
            submitted = True
            logger.info(f"Clicked submit with selector: {selector}")
            break
        except NoSuchElementException:
            continue

    if not submitted:
        logger.error("Could not find submit button")
        return False

    # Wait for redirect after login
    time.sleep(5)
    current_url = driver.current_url
    logger.info(f"After login, URL is: {current_url}")

    if "login" in current_url:
        logger.error("Still on login page - credentials may be wrong")
        return False

    logger.info("Login successful!")
    return True

def renew_servers(driver):
    logger.info("Navigating to free servers page...")
    driver.get(SERVERS_URL)
    time.sleep(4)

    renewed = 0
    failed = 0

    # Look for renew buttons
    renew_selectors = [
        (By.XPATH, "//button[contains(text(), 'Renew')]"),
        (By.XPATH, "//a[contains(text(), 'Renew')]"),
        (By.CSS_SELECTOR, "button.renew-btn"),
        (By.CSS_SELECTOR, "[data-action='renew']"),
        (By.XPATH, "//button[contains(@class, 'renew')]"),
    ]

    renew_buttons = []
    for by, selector in renew_selectors:
        try:
            buttons = driver.find_elements(by, selector)
            if buttons:
                renew_buttons = buttons
                logger.info(f"Found {len(buttons)} renew button(s) with selector: {selector}")
                break
        except Exception:
            continue

    if not renew_buttons:
        logger.warning("No renew buttons found - server may not need renewal yet or selectors changed")
        logger.info(f"Page title: {driver.title}")
        logger.info(f"Current URL: {driver.current_url}")
        # Log a snippet of the page to help debug
        logger.info(f"Page source snippet: {driver.page_source[:3000]}")
        return 0, 0

    for i, btn in enumerate(renew_buttons):
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            time.sleep(0.5)
            btn.click()
            logger.info(f"Clicked renew button {i+1}")
            time.sleep(2)

            # Check for confirmation dialog
            try:
                confirm = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Confirm') or contains(text(), 'Yes') or contains(text(), 'OK')]"))
                )
                confirm.click()
                logger.info("Confirmed renewal dialog")
                time.sleep(2)
            except TimeoutException:
                pass  # No confirmation dialog needed

            renewed += 1
            logger.info(f"Server {i+1} renewed successfully!")

        except Exception as e:
            logger.error(f"Failed to renew server {i+1}: {e}")
            failed += 1

    return renewed, failed

def main():
    if not EMAIL or not PASSWORD:
        logger.error("EMAIL or PASSWORD environment variables not set!")
        return

    driver = get_driver()
    try:
        if not login(driver):
            logger.error("Login failed, exiting.")
            return

        renewed, failed = renew_servers(driver)
        logger.info(f"Done! Renewed: {renewed}, Failed: {failed}")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
