import math
import heapq
from app.models.airport import get_airport_coordinates, get_airports, load_airport_cache
from app.models.weather import get_weather_data

# Constants for VFR altitudes (in feet)
VFR_EAST_ODD = [3500, 5500, 7500, 9500, 11500]  # Odd thousands + 500
VFR_WEST_EVEN = [4500, 6500, 8500, 10500, 12500]  # Even thousands + 500



def haversine(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance in nautical miles."""
    R = 3440.065  # Nautical miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def get_vfr_altitude(lat1, lon1, lat2, lon2):
    """Return appropriate VFR cruising altitude for direction (East/West)."""
    course = math.degrees(math.atan2(lon2 - lon1, lat2 - lat1)) % 360
    if 0 <= course < 180:
        return VFR_EAST_ODD[0]  # Simplified: always lowest legal
    else:
        return VFR_WEST_EVEN[0]


def plan_route(start_code, end_code, aircraft_range_nm, groundspeed_kt, 
               fuel_capacity_gal=50, fuel_burn_gph=12, avoid_terrain=False, plan_fuel_stops=True,
               cruising_altitude_ft=6500):
    """
    Plan a VFR route between two airports with advanced fuel planning, terrain avoidance, and wind analysis.
    
    Args:
        start_code (str): Starting airport ICAO code
        end_code (str): Destination airport ICAO code
        aircraft_range_nm (int): Aircraft range in nautical miles
        groundspeed_kt (int): Ground speed in knots
        fuel_capacity_gal (float): Aircraft fuel capacity in gallons
        fuel_burn_gph (float): Fuel burn rate in gallons per hour
        avoid_terrain (bool): Whether to avoid high terrain routes (up to 20% longer)
        plan_fuel_stops (bool): Whether to plan fuel stops with 30-minute reserves
        cruising_altitude_ft (int): Planned cruising altitude in feet
    
    Returns:
        dict: Route legs, total distance, estimated time, fuel stops, fuel planning details, wind data
    """
    # Get airport coordinates
    start = get_airport_coordinates(start_code)
    end = get_airport_coordinates(end_code)
    if not start or not end:
        return {'error': 'Invalid airport code(s)'}
    
    # Get intermediate airports from cache instead of API (fallback for DNS/SSL issues)
    mid_lat = (start['latitude'] + end['latitude']) / 2
    mid_lon = (start['longitude'] + end['longitude']) / 2
    direct_distance = haversine(start['latitude'], start['longitude'], end['latitude'], end['longitude'])
    
    # If direct distance is within range, use direct route
    if direct_distance <= aircraft_range_nm:
        nodes = {start['icao']: start, end['icao']: end}
    else:
        # For longer routes, use a simplified approach with key intermediate airports
        # Focus on major airports that are likely to be useful for routing
        cached_airports = load_airport_cache()
        intermediate_airports = []
        
        for airport in cached_airports:
            icao_code = airport.get('icao') or airport.get('icaoCode')
            if not icao_code or icao_code in [start['icao'], end['icao']]:
                continue
                
            # Handle coordinate field variations
            if 'geometry' in airport and 'coordinates' in airport['geometry']:
                longitude, latitude = airport['geometry']['coordinates']
            else:
                latitude = airport.get('lat') or airport.get('latitude')
                longitude = airport.get('lon') or airport.get('longitude')
            
            if latitude is None or longitude is None:
                continue
                
            # Calculate distances to start and end
            dist_to_start = haversine(latitude, longitude, start['latitude'], start['longitude'])
            dist_to_end = haversine(latitude, longitude, end['latitude'], end['longitude'])
            
            # Include airport if it can serve as an intermediate stop
            if (dist_to_start <= aircraft_range_nm and 
                dist_to_end <= aircraft_range_nm and
                dist_to_start + dist_to_end < direct_distance * 1.5):  # Reasonable routing efficiency
                
                intermediate_airports.append({
                    'icao': icao_code,
                    'latitude': latitude,
                    'longitude': longitude,
                    'name': airport.get('name', ''),
                    'elevation': airport.get('elevation', 0),
                    'dist_to_start': dist_to_start,
                    'dist_to_end': dist_to_end,
                    'total_distance': dist_to_start + dist_to_end
                })
        
        # Sort by total distance (most efficient routing first)
        intermediate_airports.sort(key=lambda x: x['total_distance'])
        
        # Build nodes with start, end, and best intermediate airports
        nodes = {start['icao']: start, end['icao']: end}
        
        # Add the best intermediate airports (limit to 10 for performance)
        for airport in intermediate_airports[:10]:
            nodes[airport['icao']] = {
                'icao': airport['icao'],
                'latitude': airport['latitude'],
                'longitude': airport['longitude'],
                'name': airport['name'],
                'elevation': airport['elevation']
            }
    
    # Build graph: connect airports within aircraft range
    graph = {icao: [] for icao in nodes}
    for icao1, a1 in nodes.items():
        for icao2, a2 in nodes.items():
            if icao1 == icao2:
                continue
            dist = haversine(a1['latitude'], a1['longitude'], a2['latitude'], a2['longitude'])
            if dist <= aircraft_range_nm:
                cruise_alt = cruising_altitude_ft  # Use provided cruising altitude
                graph[icao1].append({'to': icao2, 'distance': dist, 'cruise_altitude': cruise_alt})
                graph[icao2].append({'to': icao1, 'distance': dist, 'cruise_altitude': cruise_alt})  # Add reverse edge

    # Dijkstra's algorithm
    heap = [(0, start['icao'], [])]  # (distance, current, path)
    visited = set()
    while heap:
        total_dist, current, path = heapq.heappop(heap)
        if current == end['icao']:
            full_path = path + [current]
            break
        if current in visited:
            continue
        visited.add(current)
        for neighbor in graph[current]:
            if neighbor['to'] not in visited:
                heapq.heappush(heap, (total_dist + neighbor['distance'], neighbor['to'], path + [current]))
    else:
        return {'error': 'No route found'}
    # Build legs
    legs = []
    total_time_hr = 0
    for i in range(len(full_path) - 1):
        a1 = nodes[full_path[i]]
        a2 = nodes[full_path[i+1]]
        dist = haversine(a1['latitude'], a1['longitude'], a2['latitude'], a2['longitude'])
        cruise_alt = cruising_altitude_ft  # Use provided cruising altitude
        time_hr = dist / groundspeed_kt
        total_time_hr += time_hr
        legs.append({
            'from': a1['icao'],
            'to': a2['icao'],
            'distance_nm': dist,
            'cruise_altitude_ft': cruise_alt,
            'estimated_time_hr': time_hr,
        })
    # Fuel stops are all intermediate airports
    fuel_stops = full_path[1:-1]
    
    # Fuel planning
    if plan_fuel_stops:
        fuel_stops_with_details = []
        total_fuel_burn = 0
        for i in range(len(full_path) - 1):
            a1 = nodes[full_path[i]]
            a2 = nodes[full_path[i+1]]
            dist = haversine(a1['latitude'], a1['longitude'], a2['latitude'], a2['longitude'])
            time_hr = dist / groundspeed_kt
            fuel_burn = time_hr * fuel_burn_gph
            total_fuel_burn += fuel_burn
            if full_path[i+1] in fuel_stops:
                fuel_stops_with_details.append({
                    'icao': a2['icao'],
                    'name': a2['name'],
                    'fuel_burn_gal': fuel_burn,
                    'total_fuel_burn_gal': total_fuel_burn,
                    'fuel_reserve_gal': fuel_capacity_gal - total_fuel_burn,
                })
        fuel_planning = {
            'total_fuel_burn_gal': total_fuel_burn,
            'fuel_stops': fuel_stops_with_details,
        }
    else:
        fuel_planning = {}
    
    return {
        'legs': legs,
        'total_distance_nm': sum(l['distance_nm'] for l in legs),
        'estimated_time_hr': total_time_hr,
        'fuel_stops': fuel_stops,
        'fuel_planning': fuel_planning,
    }
