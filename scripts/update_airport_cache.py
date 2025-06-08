import os
import requests
import json
import time

OPENAIP_API_KEY = os.getenv('OPENAIP_API_KEY')
OPENAIP_API_URL = 'https://api.core.openaip.net/api/airports'
CACHE_FILE = os.path.join(os.path.dirname(__file__), '../app/models/airports_cache.json')

HEADERS = {
    'x-openaip-api-key': OPENAIP_API_KEY,
    'Accept': 'application/json'
}

PAGE_SIZE = 1000


def download_all_airports():
    all_items = []
    page = 1
    while True:
        params = {'page': page, 'limit': PAGE_SIZE}
        resp = requests.get(OPENAIP_API_URL, headers=HEADERS, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items = data.get('items', [])
        if not items:
            break
        all_items.extend(items)
        if len(items) < PAGE_SIZE:
            break
        page += 1
        time.sleep(0.5)
    return all_items


def main():
    if not OPENAIP_API_KEY:
        print("OPENAIP_API_KEY not set. Exiting.")
        return
    print("Downloading airport data from OpenAIP...")
    airports = download_all_airports()
    print(f"Downloaded {len(airports)} airports.")
    with open(CACHE_FILE, 'w') as f:
        json.dump(airports, f)
    print(f"Saved to {CACHE_FILE}")

if __name__ == "__main__":
    main()
