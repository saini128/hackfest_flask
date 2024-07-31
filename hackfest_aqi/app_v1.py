from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import geopy
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Define AQI category labels
aqi_labels = {
    0: 'good',
    1: 'moderate',
    2: 'unhealthy_sensitive',
    3: 'unhealthy',
    4: 'very_unhealthy',
    5: 'hazardous'
}

# Function to get latitude and longitude from location name
def get_coordinates(location):
    geolocator = geopy.geocoders.Nominatim(user_agent="air_quality_app")
    location = geolocator.geocode(location)
    if location is None:
        raise ValueError("Location not found")
    return location.latitude, location.longitude

# Function to get AQI value from OpenWeatherMap API
def get_aqi(latitude, longitude):
    api_key = "c240a459dab670c0510091263e5a81ca"  # Directly including the API key here
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={latitude}&lon={longitude}&appid={api_key}"
    response = requests.get(url)
    data = response.json()

    if 'list' in data and len(data['list']) > 0:
        return data
    else:
        raise ValueError("AQI data not found in API response")

@app.route('/')
def home():
    return jsonify(message="Dev Message, Reyan AQI API")
@app.route('/get_aqi', methods=['GET'])
def get_aqi_info():
    location = request.args.get('location')
    latitude = request.args.get('lat')
    longitude = request.args.get('lon')
    try:
        if not location and (not latitude or not longitude):
            return jsonify({"error": "Please provide either a location name or latitude and longitude."}), 400

        if location:
            latitude, longitude = get_coordinates(location)

        aqi_data = get_aqi(latitude, longitude)

        result = {
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude
            },
            "aqi": aqi_data['list'][0]['main']['aqi'],
            "components": aqi_data['list'][0]['components'],
            "category": aqi_labels.get(aqi_data['list'][0]['main']['aqi'], 'unknown')
        }

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
