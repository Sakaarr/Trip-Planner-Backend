import requests
import polyline

ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImJhMWE0OWI4Mjk1YzQyMzlhZmIzYjc5NGVmNDU1OTYxIiwiaCI6Im11cm11cjY0In0="
ORS_BASE_URL = "https://api.openrouteservice.org/v2/directions/driving-car"

# utils.py

def geocode_place(place):
    """
    Returns coordinates [lon, lat] for a given place.
    """
    response = requests.get("https://api.openrouteservice.org/geocode/search", params={
        "api_key": ORS_API_KEY,
        "text": place,
        "size": 1
    })
    response.raise_for_status()
    data = response.json()
    coords = data["features"][0]["geometry"]["coordinates"]
    return coords  # [lon, lat]

def get_route_distance(start, end):
    try:
        start_coords = geocode_place(start)
        end_coords = geocode_place(end)

        response = requests.post(
            ORS_BASE_URL,
            headers={"Authorization": ORS_API_KEY, "Content-Type": "application/json"},
            json={"coordinates": [start_coords, end_coords]}
        )
        response.raise_for_status()
        data = response.json()

        meters = data["routes"][0]["summary"]["distance"]
        encoded_geometry = data["routes"][0]["geometry"]

        # Decode polyline into [lat, lon] list
        decoded_coords = polyline.decode(encoded_geometry)  # [(lat, lon), ...]

        return round(meters / 1609.34, 2), {
            "start": start_coords[::-1],
            "end": end_coords[::-1],
            "geometry_encoded": encoded_geometry,
            "geometry_decoded": decoded_coords
        }

    except Exception as e:
        return None, {}