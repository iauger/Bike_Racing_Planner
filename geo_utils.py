import pgeocode
import math
import pandas as pd

def get_lat_lon(zip_code, country='US'):
    nomi = pgeocode.Nominatim(country)
    location = nomi.query_postal_code(zip_code)
    
    if pd.isna(location.latitude.item()) or pd.isna(location.longitude.item()):
        raise ValueError(f"Could not find coordinates for ZIP code {zip_code}")

    return float(location.latitude.item()), float(location.longitude.item())

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of the Earth in kilometers
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def calculate_distance_to_event(events_df, user_zip):
    user_lat, user_lon = get_lat_lon(user_zip)
    distances = []
    for _, row in events_df.iterrows():
        if pd.notna(row['latitude']) and pd.notna(row['longitude']):
            dist = haversine_distance(user_lat, user_lon, row['latitude'], row['longitude'])
        else:
            dist = float('inf')  # Assign infinity if coordinates are missing
        distances.append(dist)
    events_df['distance_to_event'] = distances
    return events_df
    