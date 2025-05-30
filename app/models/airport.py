import requests
import logging
import math
import xml.etree.ElementTree as ET
from datetime import datetime

logger = logging.getLogger(__name__)

def get_airports(lat, lon, radius=50):
    """
    Get airports within a specified radius of a location.
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
        radius (int): Search radius in miles (default: 50)
        
    Returns:
        dict: Airport data
    """
    try:
        # Ensure radius is within reasonable limits
        radius = max(10, min(100, radius))
        
        # Call the FAA API to get airports
        url = f"https://nfdc.faa.gov/nfdcApps/services/ajv5/airportSearch.jsp?lat={lat}&lon={lon}&radius={radius}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse the XML response
        root = ET.fromstring(response.content)
        airports = []
        
        for airport in root.findall('.//Airport'):
            try:
                icao = airport.find('ICAO').text if airport.find('ICAO') is not None else None
                
                # Skip entries without ICAO code
                if not icao:
                    continue
                    
                # Extract airport data
                airport_data = {
                    'icao': icao,
                    'name': airport.find('Name').text if airport.find('Name') is not None else 'Unknown',
                    'city': airport.find('City').text if airport.find('City') is not None else '',
                    'state': airport.find('State').text if airport.find('State') is not None else '',
                    'latitude': float(airport.find('Lat').text) if airport.find('Lat') is not None else None,
                    'longitude': float(airport.find('Lon').text) if airport.find('Lon') is not None else None,
                    'elevation': int(float(airport.find('Elev').text)) if airport.find('Elev') is not None else None,
                    'type': airport.find('Type').text if airport.find('Type') is not None else 'Unknown',
                    'distance': float(airport.find('Distance').text) if airport.find('Distance') is not None else None
                }
                
                # Get METAR data for this airport
                metar_data = get_metar_data([icao])
                if icao in metar_data:
                    airport_data['metar'] = metar_data[icao]
                    
                airports.append(airport_data)
            except Exception as e:
                logger.error(f"Error processing airport data: {str(e)}")
                continue
                
        # Sort airports by distance
        airports.sort(key=lambda x: x.get('distance', float('inf')))
        
        return {
            'count': len(airports),
            'airports': airports
        }
        
    except Exception as e:
        logger.error(f"Error fetching airport data: {str(e)}")
        return {'count': 0, 'airports': []}

def get_airport_coordinates(code):
    """
    Get coordinates for an airport by ICAO or IATA code.
    
    Args:
        code (str): Airport code (ICAO or IATA)
        
    Returns:
        dict: Airport location data
    """
    try:
        # Handle IATA codes (convert to ICAO if possible)
        if len(code) == 3:
            # Common prefix mapping for US airports
            if code[0] in 'KLMNPQRSTUVWXYZ':
                icao_code = 'K' + code
            else:
                # Try to look up the ICAO code from a service
                icao_code = get_icao_from_iata(code)
                if not icao_code:
                    return None
        else:
            icao_code = code
            
        # Query the FAA API for airport data
        url = f"https://nfdc.faa.gov/nfdcApps/services/ajv5/airportSearch.jsp?icao={icao_code}"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return None
            
        # Parse the XML response
        root = ET.fromstring(response.content)
        airport = root.find('.//Airport')
        
        if airport is None:
            return None
            
        # Extract airport data
        airport_data = {
            'icao': icao_code,
            'name': airport.find('Name').text if airport.find('Name') is not None else 'Unknown',
            'city': airport.find('City').text if airport.find('City') is not None else '',
            'state': airport.find('State').text if airport.find('State') is not None else '',
            'latitude': float(airport.find('Lat').text) if airport.find('Lat') is not None else None,
            'longitude': float(airport.find('Lon').text) if airport.find('Lon') is not None else None,
            'elevation': int(float(airport.find('Elev').text)) if airport.find('Elev') is not None else None
        }
        
        # Get METAR data
        metar_data = get_metar_data([icao_code])
        if icao_code in metar_data:
            airport_data['metar'] = metar_data[icao_code]
            
        return airport_data
        
    except Exception as e:
        logger.error(f"Error getting airport coordinates: {str(e)}")
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
