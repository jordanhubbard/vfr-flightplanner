import os
import requests
import logging

URL = "https://ourairports.com/data/airports.csv"
DEST = os.environ.get("OURAIRPORTS_CSV", "/app/xctry-planner/backend/airports.csv")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fetch_ourairports_csv")

def fetch_csv(url=URL, dest=DEST):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    logger.info(f"Fetching OurAirports CSV from {url} ...")
    try:
        resp = requests.get(url, timeout=30)
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
