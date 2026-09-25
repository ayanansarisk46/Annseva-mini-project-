"""
================================================================================
AnnSeva - Geocoding Resolver (services/geocoding.py)
================================================================================
College Viva Note:
Users do not know or enter GPS numbers (latitude & longitude) when donating food.
They enter natural locality and city names (e.g. 'Andheri West, Mumbai').
This helper resolves location text into coordinates for the interactive map.
================================================================================
"""

import hashlib

# Known locality coordinate centroids
LOCALITY_COORDINATES = {
    'andheri west': (19.1363, 72.8277),
    'andheri east': (19.1158, 72.8562),
    'andheri': (19.1197, 72.8464),
    'bandra kurla complex': (19.0657, 72.8687),
    'bkc': (19.0657, 72.8687),
    'bandra west': (19.0596, 72.8295),
    'bandra': (19.0596, 72.8295),
    'kurla west': (19.0726, 72.8845),
    'kurla east': (19.0650, 72.8900),
    'kurla': (19.0726, 72.8845),
    'dadar': (19.0178, 72.8478),
    'powai': (19.1176, 72.9060),
    'thane': (19.2183, 72.9781),
    'borivali': (19.2307, 72.8567),
    'malad': (19.1860, 72.8485),
    'ghatkopar': (19.0860, 72.9090),
    'chembur': (19.0622, 72.8997),
    'vashi': (19.0771, 72.9986),
    'navi mumbai': (19.0330, 73.0297),
    'colaba': (18.9067, 72.8147),
    'mumbai': (19.0760, 72.8777),
    'pune': (18.5204, 73.8567),
    'delhi': (28.6139, 77.2090),
    'bangalore': (12.9716, 77.5946),
    'bengaluru': (12.9716, 77.5946),
    'hyderabad': (17.3850, 78.4867),
    'chennai': (13.0827, 80.2707),
    'kolkata': (22.5726, 88.3639)
}

def resolve_location_coordinates(location_str, item_id=None):
    """
    Resolves human-readable location string to (lat, lng) tuple.
    Adds slight deterministic offset based on item_id to avoid overlapping pins.
    """
    if not location_str:
        return (19.0760, 72.8777) # Default to Mumbai center

    normalized = location_str.lower().replace(',', ' ')
    
    # Check for direct or partial match
    matched_coord = None
    for loc_key, coords in LOCALITY_COORDINATES.items():
        if loc_key in normalized:
            matched_coord = coords
            break

    # If no key found, default to general Mumbai
    if not matched_coord:
        matched_coord = (19.0760, 72.8777)

    lat, lng = matched_coord

    # Add slight pseudo-random jitter based on item_id or string hash so pins don't stack
    seed = item_id if item_id is not None else int(hashlib.md5(location_str.encode()).hexdigest(), 16) % 1000
    jitter_lat = ((seed % 17) - 8) * 0.0035
    jitter_lng = (((seed // 17) % 17) - 8) * 0.0035

    return (round(lat + jitter_lat, 4), round(lng + jitter_lng, 4))
