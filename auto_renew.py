import os
import logging
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_KEY = os.environ.get("API_KEY")
BASE_URL = "https://tickhosting.com/api/client"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

def get_servers():
    logger.info("Fetching server list...")
    r = requests.get(f"{BASE_URL}", headers=headers)
    logger.info(f"Status: {r.status_code}")
    logger.info(f"Response: {r.text[:500]}")
    if r.status_code == 200:
        return r.json().get("data", [])
    return []

def renew_server(server_id):
    logger.info(f"Attempting to renew server: {server_id}")
    endpoints = [
        f"{BASE_URL}/servers/{server_id}/renew",
        f"https://tickhosting.com/api/client/servers/{server_id}/renew",
        f"https://tickhosting.com/freeservers/{server_id}/renew",
    ]
    for endpoint in endpoints:
        r = requests.post(endpoint, headers=headers)
        logger.info(f"Endpoint: {endpoint} | Status: {r.status_code} | Response: {r.text[:300]}")
        if r.status_code in [200, 204]:
            logger.info(f"Server {server_id} renewed successfully!")
            return True
    return False

def main():
    if not API_KEY:
        logger.error("API_KEY not set!")
        return

    servers = get_servers()
    if not servers:
        logger.warning("No servers found or could not fetch server list")
        return

    for server in servers:
        server_id = server.get("attributes", {}).get("identifier")
        name = server.get("attributes", {}).get("name")
        logger.info(f"Found server: {name} ({server_id})")
        renew_server(server_id)

if __name__ == "__main__":
    main()
