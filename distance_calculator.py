from geopy.distance import geodesic
from geopy.geocoders import Nominatim

def calculate_distance_and_time(user_lat, user_lon, station_lat, station_lon):
    user_coords = (user_lat, user_lon)
    station_coords = (station_lat, station_lon)
    distance = geodesic(user_coords, station_coords).kilometers

    # 假设平均速度为 50 km/h
    time_hours = distance / 50
    time_minutes = time_hours * 60

    return {
        'distance': round(distance, 2),
        'time_minutes': round(time_minutes, 2)
    }

def get_address(lat, lon):
    geolocator = Nominatim(user_agent="fuel_price_tracker")
    location = geolocator.reverse(f"{lat}, {lon}")
    return location.address if location else "Unknown"