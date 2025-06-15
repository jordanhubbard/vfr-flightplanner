import os
import requests
import json
import time
import logging

OPENAIP_API_KEY = os.getenv('OPENAIP_API_KEY')
OPENAIP_API_URL = 'https://api.core.openaip.net/api/airports'
CACHE_FILE = os.path.join(os.path.dirname(__file__), '../app/models/airports_cache.json')

HEADERS = {
    'x-openaip-api-key': OPENAIP_API_KEY,
    'Accept': 'application/json'
}

PAGE_SIZE = 1000

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("update_airport_cache")

def download_all_airports():
    all_items = []
    page = 1
    while True:
        params = {'page': page, 'limit': PAGE_SIZE}
        
        # Add API key as query parameter as fallback
        if OPENAIP_API_KEY:
            params['apiKey'] = OPENAIP_API_KEY
            
        logger.info(f"Requesting airports page {page}...")
        try:
            resp = requests.get(OPENAIP_API_URL, headers=HEADERS, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            items = data.get('items', [])
            logger.info(f"Received {len(items)} airports on page {page}.")
            if not items:
                break
            all_items.extend(items)
            if len(items) < PAGE_SIZE:
                break
            page += 1
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Failed to download airports on page {page}: {e}")
            break
    return all_items

def main():
    import sys
    
    # Check if we should force refresh
    force_refresh = '--force' in sys.argv
    
    # Check if cache already exists and is not empty
    if not force_refresh and os.path.exists(CACHE_FILE) and os.path.getsize(CACHE_FILE) > 100:
        logger.info(f"Airport cache already exists at {CACHE_FILE}. Use --force to refresh.")
        return
    
    if not OPENAIP_API_KEY:
        logger.error("OPENAIP_API_KEY not set. Exiting.")
        return
        
    logger.info("Downloading airport data from OpenAIP...")
    try:
        airports = download_all_airports()
        if airports:
            logger.info(f"Downloaded {len(airports)} airports.")
            with open(CACHE_FILE, 'w') as f:
                json.dump(airports, f)
            logger.info(f"Saved to {CACHE_FILE}")
        else:
            logger.warning("No airports downloaded. Keeping existing cache.")
    except Exception as e:
        logger.error(f"Airport data download failed: {e}. Keeping existing cache.")

if __name__ == "__main__":
    main()
