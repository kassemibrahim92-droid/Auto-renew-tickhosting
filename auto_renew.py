import os
import time
import logging
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EMAIL = os.environ.get("EMAIL")
PASSWORD = os.environ.get("PASSWORD")
BASE_URL = "https://tickhosting.com"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://tickhosting.com/auth/login",
    "Origin": "https://tickhosting.com",
})

def get_csrf_token():
    logger.info("Fetching CSRF token...")
    r = session.get(f"{BASE_URL}/auth/login")
    logger.info(f"Login page status: {r.status_code}")
    
    # Try to find CSRF token in cookies
    for cookie in session.cookies:
        logger.info(f"Cookie: {cookie.name} = {cookie.value[:20]}...")
        if 'csrf' in cookie.name.lower() or 'xsrf' in cookie.name.lower():
            return cookie.value
    
    # Try to find in response headers
    for key, val in r.headers.items():
        if 'csrf' in key.lower():
            logger.info(f"CSRF header: {key} = {val}")
            return val
    
    return None

def login():
    logger.info("Attempting login...")
    
    csrf = get_csrf_token()
    if csrf:
        logger.info(f"Got CSRF token: {csrf[:20]}...")
    
    payload = {
        "email": EMAIL,
        "password": PASSWORD,
    }
    
    if csrf:
        payload["_token"] = csrf
    
    headers = {
        "Content-Type": "application/json",
        "X-CSRF-TOKEN": csrf or "",
        "X-Requested-With": "XMLHttpRequest",
    }
    
    # Try JSON login
    r = session.post(f"{BASE_URL}/auth/login", json=payload, headers=headers)
    logger.info(f"Login response status: {r.status_code}")
    logger.info(f"Login response: {r.text[:500]}")
    
    if r.status_code == 200 or r.status_code == 302:
        # Check if we're logged in
        check = session.get(f"{BASE_URL}/freeservers")
        logger.info(f"Free servers page status: {check.status_code}")
        logger.info(f"Free servers URL: {check.url}")
        if "login" not in check.url:
            logger.info("Login successful!")
            return True
    
    # Try form login
    logger.info("Trying form-encoded login...")
    r = session.post(f"{BASE_URL}/auth/login", data=payload)
    logger.info(f"Form login response status: {r.status_code}")
    logger.info(f"Form login URL after redirect: {r.url}")
    
    check = session.get(f"{BASE_URL}/freeservers")
    if "login" not in check.url:
        logger.info("Login successful!")
        return True
    
    logger.error("Login failed")
    logger.info(f"Response snippet: {r.text[:1000]}")
    return False

def renew_servers():
    logger.info("Fetching free servers page...")
    r = session.get(f"{BASE_URL}/freeservers")
    logger.info(f"Page status: {r.status_code}")
    
    # Try the renew API endpoint directly
    renew_endpoints = [
        f"{BASE_URL}/api/renew",
        f"{BASE_URL}/freeservers/renew",
        f"{BASE_URL}/server/renew",
    ]
    
    for endpoint in renew_endpoints:
        logger.info(f"Trying renew endpoint: {endpoint}")
        r = session.post(endpoint)
        logger.info(f"Response: {r.status_code} - {r.text[:200]}")
        if r.status_code == 200:
            logger.info("Renewal successful!")
            return True
    
    logger.warning("Could not find working renew endpoint")
    return False

def main():
    if not EMAIL or not PASSWORD:
        logger.error("EMAIL or PASSWORD not set!")
        return
    
    if not login():
        logger.error("Login failed, exiting.")
        return
    
    renew_servers()

if __name__ == "__main__":
    main()
