import os
import requests
import logging
import urllib3

# Suppress SSL warnings when using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = "https://ourairports.com/data/airports.csv"
DEST = os.environ.get("OURAIRPORTS_CSV", "/app/xctry-planner/backend/airports.csv")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fetch_ourairports_csv")

def fetch_csv(url=URL, dest=DEST):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    logger.info(f"Fetching OurAirports CSV from {url} ...")
    try:
        # Add SSL verification bypass and user agent to avoid SSL certificate issues
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        resp = requests.get(url, timeout=30, verify=False, headers=headers)
        resp.raise_for_status()
        with open(dest, "wb") as f:
            f.write(resp.content)
        logger.info(f"Saved OurAirports CSV to {dest}")
    except Exception as e:
        logger.error(f"Failed to fetch OurAirports CSV: {e}")
        return False
    return True

if __name__ == "__main__":
    fetch_csv()
