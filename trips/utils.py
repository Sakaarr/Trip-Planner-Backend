import requests

ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImJhMWE0OWI4Mjk1YzQyMzlhZmIzYjc5NGVmNDU1OTYxIiwiaCI6Im11cm11cjY0In0="
ORS_BASE_URL = "https://api.openrouteservice.org/v2/directions/driving-car"

def get_route_distance(start, end):
    """
    Uses OpenRouteService to calculate distance in miles between two locations
    """
    geocode_url = "https://api.openrouteservice.org/geocode/search"
    
    def geocode(place):
        response = requests.get(geocode_url, params={
            "api_key": ORS_API_KEY,
            "text": place,
            "size": 1
        })
        data = response.json()
        coords = data["features"][0]["geometry"]["coordinates"]
        return coords  # [lon, lat]
    
    try:
        start_coords = geocode(start)
        end_coords = geocode(end)

        response = requests.post(
            ORS_BASE_URL,
            headers={"Authorization": ORS_API_KEY, "Content-Type": "application/json"},
            json={"coordinates": [start_coords, end_coords]}
        )
        data = response.json()
        meters = data["routes"][0]["summary"]["distance"]
        return round(meters / 1609.34, 2)  # Convert to miles
    except Exception as e:
        return None
