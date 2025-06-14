import requests
import logging
import math
import os
from datetime import datetime

OPENAIP_API_KEY = os.getenv('OPENAIP_API_KEY')
OPENAIP_API_URL = 'https://api.openaip.net/api/v4/airports'

HEADERS = {
    'Authorization': f'Bearer {OPENAIP_API_KEY}',
    'Accept': 'application/json'
}

logger = logging.getLogger(__name__)

def get_airports(lat, lon, radius=50):
    """
    Get airports within a specified radius of a location using OpenAIP.
    Args:
        lat (float): Latitude
        lon (float): Longitude
        radius (int): Search radius in kilometers (OpenAIP expects km)
    Returns:
        dict: Airport data
    """
    try:
        logger.info(f"Starting OpenAIP airport data download for lat={lat}, lon={lon}, radius={radius}nm ({radius_km}km)")
        radius_km = max(16, min(160, int(radius * 1.60934)))  # Convert miles to km, clamp to reasonable values
        params = {
            'lat': lat,
            'lon': lon,
            'radius': radius_km
        }
        response = requests.get(OPENAIP_API_URL, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        airports = []
        # OpenAIP v4 returns airports in 'data' key, not 'items'
        for airport in data.get('data', []):
            airport_data = {
                'icao': airport.get('icao'),
                'iata': airport.get('iata'),
                'name': airport.get('name'),
                'city': airport.get('city'),
                'country': airport.get('country'),
                'latitude': airport.get('lat'),
                'longitude': airport.get('lon'),
                'elevation': airport.get('elevation'),
                'type': airport.get('type'),
                'distance': airport.get('distance', None),
            }
            # Optionally, get METAR data if needed
            icao = airport.get('icao')
            if icao:
                metar_data = get_metar_data([icao])
                if icao in metar_data:
                    airport_data['metar'] = metar_data[icao]
            airports.append(airport_data)
        airports.sort(key=lambda x: x.get('distance', float('inf')))
        logger.info(f"Completed OpenAIP airport data download: found {len(airports)} airports.")
        return {
            'count': len(airports),
            'airports': airports
        }
        
    except Exception as e:
        logger.error(f"Error fetching airport data: {str(e)}")
        return {'count': 0, 'airports': []}

import json
CACHE_PATH = os.path.join(os.path.dirname(__file__), 'airports_cache.json')

_airport_cache = None

def load_airport_cache():
    global _airport_cache
    if _airport_cache is None:
        try:
            with open(CACHE_PATH, 'r') as f:
                _airport_cache = json.load(f)
        except Exception as e:
            logger.error(f"Error loading airport cache: {e}")
            _airport_cache = []
    return _airport_cache

def get_airport_coordinates(code):
    """
    Get coordinates for an airport by ICAO or IATA code using local cache.
    Args:
        code (str): Airport code (ICAO or IATA)
    Returns:
        dict: Airport location data
    """
    code = code.upper()
    airports = load_airport_cache()
    for airport in airports:
        if airport.get('icao') == code or airport.get('iata') == code:
            airport_data = {
                'icao': airport.get('icao'),
                'iata': airport.get('iata'),
                'name': airport.get('name'),
                'city': airport.get('city'),
                'country': airport.get('country'),
                'latitude': airport.get('lat'),
                'longitude': airport.get('lon'),
                'elevation': airport.get('elevation'),
                'type': airport.get('type'),
            }
            icao = airport.get('icao')
            if icao:
                metar_data = get_metar_data([icao])
                if icao in metar_data:
                    airport_data['metar'] = metar_data[icao]
            return airport_data
    return None


def get_icao_from_iata(iata_code):
    """
    Convert IATA code to ICAO code.
    
    Args:
        iata_code (str): IATA airport code
        
    Returns:
        str: ICAO code or None if not found
    """
    try:
        # For US airports, try the K prefix
        if len(iata_code) == 3:
            icao_guess = 'K' + iata_code
            
            # Verify this is a valid ICAO code
            url = f"https://nfdc.faa.gov/nfdcApps/services/ajv5/airportSearch.jsp?icao={icao_guess}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                if root.find('.//Airport') is not None:
                    return icao_guess
        
        # For non-US airports, we would need a more comprehensive database
        # This is a simplified approach
        return None
        
    except Exception as e:
        logger.error(f"Error converting IATA to ICAO: {str(e)}")
        return None

def get_metar_data(icao_codes):
    """
    Fetch METAR data for a list of airports.
    
    Args:
        icao_codes (list): List of ICAO airport codes
        
    Returns:
        dict: METAR data keyed by ICAO code
    """
    if not icao_codes:
        return {}
        
    try:
        # Join ICAO codes for the API request
        codes_str = ','.join(icao_codes)
        
        # Call the ADDS API to get METAR data
        url = f"https://aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&stationString={codes_str}&hoursBeforeNow=2"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return {}
            
        # Parse the XML response
        root = ET.fromstring(response.content)
        metars = {}
        
        for metar in root.findall('.//METAR'):
            try:
                station_id = metar.find('station_id').text
                
                # Extract METAR data
                raw_text = metar.find('raw_text').text if metar.find('raw_text') is not None else None
                
                if not raw_text:
                    continue
                    
                # Parse observation time
                obs_time = None
                if metar.find('observation_time') is not None:
                    time_str = metar.find('observation_time').text
                    try:
                        obs_time = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M UTC")
                    except:
                        obs_time = time_str
                
                # Extract weather elements
                temp_c = float(metar.find('temp_c').text) if metar.find('temp_c') is not None else None
                dewpoint_c = float(metar.find('dewpoint_c').text) if metar.find('dewpoint_c') is not None else None
                wind_dir_degrees = int(metar.find('wind_dir_degrees').text) if metar.find('wind_dir_degrees') is not None else None
                wind_speed_kt = int(metar.find('wind_speed_kt').text) if metar.find('wind_speed_kt') is not None else None
                wind_gust_kt = int(metar.find('wind_gust_kt').text) if metar.find('wind_gust_kt') is not None else None
                visibility_statute_mi = float(metar.find('visibility_statute_mi').text) if metar.find('visibility_statute_mi') is not None else None
                altim_in_hg = float(metar.find('altim_in_hg').text) if metar.find('altim_in_hg') is not None else None
                
                # Extract cloud layers
                cloud_layers = []
                for sky_condition in metar.findall('.//sky_condition'):
                    cover = sky_condition.get('sky_cover')
                    base = sky_condition.get('cloud_base_ft_agl')
                    if cover and base:
                        cloud_layers.append({
                            'cover': cover,
                            'base': int(base)
                        })
                
                # Determine flight category
                flight_category = get_flight_category({
                    'visibility_statute_mi': visibility_statute_mi,
                    'cloud_layers': cloud_layers
                })
                
                # Build the METAR data structure
                metar_data = {
                    'raw_text': raw_text,
                    'observation_time': obs_time,
                    'temperature_c': temp_c,
                    'temperature_f': round(temp_c * 9/5 + 32, 1) if temp_c is not None else None,
                    'dewpoint_c': dewpoint_c,
                    'dewpoint_f': round(dewpoint_c * 9/5 + 32, 1) if dewpoint_c is not None else None,
                    'wind_dir_degrees': wind_dir_degrees,
                    'wind_speed_kt': wind_speed_kt,
                    'wind_speed_mph': round(wind_speed_kt * 1.15078, 1) if wind_speed_kt is not None else None,
                    'wind_gust_kt': wind_gust_kt,
                    'wind_gust_mph': round(wind_gust_kt * 1.15078, 1) if wind_gust_kt is not None else None,
                    'visibility_statute_mi': visibility_statute_mi,
                    'altim_in_hg': altim_in_hg,
                    'cloud_layers': cloud_layers,
                    'flight_category': flight_category
                }
                
                metars[station_id] = metar_data
                
            except Exception as e:
                logger.error(f"Error processing METAR for {station_id}: {str(e)}")
                continue
                
        return metars
        
    except Exception as e:
        logger.error(f"Error fetching METAR data: {str(e)}")
        return {}

def get_flight_category(metar_data):
    """
    Determine flight category from METAR data.
    
    Args:
        metar_data (dict): METAR data containing visibility and cloud layers
        
    Returns:
        str: Flight category (VFR, MVFR, IFR, LIFR) or None if unknown
    """
    try:
        visibility = metar_data.get('visibility_statute_mi')
        cloud_layers = metar_data.get('cloud_layers', [])
        
        if visibility is None:
            return None
            
        # Find the lowest ceiling
        ceiling = None
        for layer in cloud_layers:
            if layer.get('cover') in ['BKN', 'OVC']:
                base = layer.get('base')
                if base is not None and (ceiling is None or base < ceiling):
                    ceiling = base
        
        # Determine flight category based on visibility and ceiling
        if visibility < 1 or (ceiling is not None and ceiling < 500):
            return 'LIFR'  # Low IFR
        elif visibility < 3 or (ceiling is not None and ceiling < 1000):
            return 'IFR'   # IFR
        elif visibility < 5 or (ceiling is not None and ceiling < 3000):
            return 'MVFR'  # Marginal VFR
        else:
            return 'VFR'   # VFR
            
    except Exception as e:
        logger.error(f"Error determining flight category: {str(e)}")
        return None
