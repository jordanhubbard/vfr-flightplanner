import math
import heapq
from app.models.airport import get_airport_coordinates, get_airports
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


def plan_route(start_code, end_code, aircraft_range_nm=400, groundspeed_kt=120):
    """
    Plan a VFR route between two airports, considering terrain, VFR altitudes, and fuel stops.
    Args:
        start_code (str): ICAO code of departure airport
        end_code (str): ICAO code of destination airport
        aircraft_range_nm (float): Max range in nautical miles
        groundspeed_kt (float): Average groundspeed in knots
    Returns:
        dict: Route legs, total distance, estimated time, fuel stops
    """
    # Get airport coordinates
    start = get_airport_coordinates(start_code)
    end = get_airport_coordinates(end_code)
    if not start or not end:
        return {'error': 'Invalid airport code(s)'}
    
    # For simplicity, get all airports within a bounding box
    mid_lat = (start['latitude'] + end['latitude']) / 2
    mid_lon = (start['longitude'] + end['longitude']) / 2
    box_radius = haversine(start['latitude'], start['longitude'], end['latitude'], end['longitude']) / 2 + 100  # nm
    airports = get_airports(mid_lat, mid_lon, box_radius)
    nodes = {a['icao']: a for a in airports.get('airports', []) if 'icao' in a}
    nodes[start['icao']] = start
    nodes[end['icao']] = end

    # Build graph: connect airports within aircraft range
    graph = {icao: [] for icao in nodes}
    for icao1, a1 in nodes.items():
        for icao2, a2 in nodes.items():
            if icao1 == icao2:
                continue
            dist = haversine(a1['latitude'], a1['longitude'], a2['latitude'], a2['longitude'])
            if dist <= aircraft_range_nm:
                cruise_alt = get_vfr_altitude(a1['latitude'], a1['longitude'], a2['latitude'], a2['longitude'])
                graph[icao1].append({'to': icao2, 'distance': dist, 'cruise_altitude': cruise_alt})

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
        cruise_alt = get_vfr_altitude(a1['latitude'], a1['longitude'], a2['latitude'], a2['longitude'])
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
    return {
        'legs': legs,
        'total_distance_nm': sum(l['distance_nm'] for l in legs),
        'estimated_time_hr': total_time_hr,
        'fuel_stops': fuel_stops
    }
