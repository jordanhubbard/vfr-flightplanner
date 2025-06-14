import csv
import json
import os

# Paths
OURAIRPORTS_CSV = '/app/xctry-planner/backend/airports.csv'
print(f"[merge_airport_datasets.py] Using OurAirports CSV at: {OURAIRPORTS_CSV}")


OPENAIP_JSON = os.path.join(os.path.dirname(__file__), '../app/models/airports_cache.json')
MERGED_JSON = os.path.join(os.path.dirname(__file__), '../app/models/airports_cache.json')

# Load OpenAIP airports (already in JSON)
def load_openaip():
    with open(OPENAIP_JSON, 'r') as f:
        return json.load(f)

# Load OurAirports CSV (https://ourairports.com/data/airports.csv)
def find_ourairports_csv():
    # Allow override via environment variable
    path = os.environ.get('OURAIRPORTS_CSV', '/app/xctry-planner/backend/airports.csv')
    if not os.path.exists(path):
        print(f"[merge_airport_datasets.py] OurAirports CSV not found at {path}.")
    return path

def load_ourairports():
    airports = []
    csv_path = find_ourairports_csv()
    if not os.path.exists(csv_path):
        print(f"[merge_airport_datasets.py] ERROR: OurAirports CSV does not exist at {csv_path}.")
        return airports
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Only include airports with ICAO or IATA code
            if not row['ident']:
                continue
            airport = {
                'icao': row['ident'] if len(row['ident']) == 4 else None,
                'iata': row['iata_code'] or None,
                'name': row['name'],
                'city': row['municipality'] or '',
                'country': row['iso_country'] or '',
                'latitude': float(row['latitude_deg']) if row['latitude_deg'] else None,
                'longitude': float(row['longitude_deg']) if row['longitude_deg'] else None,
                'elevation': float(row['elevation_ft']) if row['elevation_ft'] else None,
                'type': row['type'] or '',
            }
            airports.append(airport)
    return airports

def merge_airports(openaip, ourairports):
    # Index OpenAIP by ICAO and IATA
    index = {}
    for ap in openaip:
        if ap.get('icao'):
            index[ap['icao']] = ap
        if ap.get('iata'):
            index[ap['iata']] = ap
    # Add OurAirports entries not already present
    added = 0
    for ap in ourairports:
        if ap['icao'] and ap['icao'] in index:
            continue
        if ap['iata'] and ap['iata'] in index:
            continue
        openaip.append(ap)
        added += 1
    print(f"Added {added} airports from OurAirports.")
    return openaip

def main():
    openaip = load_openaip()
    ourairports = load_ourairports()
    merged = merge_airports(openaip, ourairports)
    with open(MERGED_JSON, 'w', encoding='utf-8') as f:
        json.dump(merged, f)
    print(f"Merged airport cache written to {MERGED_JSON}")

if __name__ == "__main__":
    main()
