from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import geopy
import json

app = Flask(__name__)
CORS(app)
# Define AQI category labels
aqi_labels = {
    0: 'good',
    1: 'moderate',
    2: 'unhealthy_sensitive',
    3: 'unhealthy',
    4: 'very_unhealthy',
    5: 'hazardous'
}

def get_lanlat(lan, lat):
    return lan, lat

def get_coordinates(location):
    geolocator = geopy.geocoders.Nominatim(user_agent="air_quality_app")
    location = geolocator.geocode(location)
    if location is None:
        raise ValueError("Location not found")
    return location.latitude, location.longitude

def get_aqi(latitude, longitude):
    api_key = "c240a459dab670c0510091263e5a81ca"
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={latitude}&lon={longitude}&appid={api_key}"
    response = requests.get(url)
    data = response.json()

    if 'list' in data and len(data['list']) > 0:
        return data
    else:
        raise ValueError("AQI data not found in API response")

def calculate_credit_cost(aqi, co, no, no2, o3, so2, pm2_5, pm10, nh3,
                          market_supply, market_demand, adjustment_factor,
                          cost_per_unit, area_cost):
    # Normalization constants
    AQI_max = 5
    CO_max = 1000  # mg/m3
    NO_max = 20    # ppb
    NO2_max = 20   # ppb
    O3_max = 200   # ppb
    SO2_max = 20   # ppb
    PM2_5_max = 50 # µg/m3
    PM10_max = 50  # µg/m3
    NH3_max = 20   # ppb

    # Normalized pollutant values
    aqi_norm = aqi / AQI_max
    co_norm = co / CO_max
    no_norm = no / NO_max
    no2_norm = no2 / NO2_max
    o3_norm = o3 / O3_max
    so2_norm = so2 / SO2_max
    pm2_5_norm = pm2_5 / PM2_5_max
    pm10_norm = pm10 / PM10_max
    nh3_norm = nh3 / NH3_max

    # Static weights for each pollutant
    weights_1 = {
        'aqi': 3,
        'co': 567.44,
        'no': 0.84,
        'no2': 7.37,
        'o3': 110.15,
        'so2': 13.95,
        'pm2_5': 34.41,
        'pm10': 40.07,
        'nh3': 6.9
    }

    # Dynamically set weights_2 based on pollutant levels
    weights_2 = {
        'aqi': aqi,
        'co': co,
        'no': no,
        'no2': no2,
        'o3': o3,
        'so2': so2,
        'pm2_5': pm2_5,
        'pm10': pm10,
        'nh3': nh3
    }

    # Normalize weights_2 to be within a reasonable range
    max_weight = max(weights_2.values())
    weights_2 = {key: (value / max_weight) for key, value in weights_2.items()}

    # Calculate weight differences
    weights = {
        'aqi': weights_1['aqi'] - weights_2['aqi'],
        'co': weights_1['co'] - weights_2['co'],
        'no': weights_1['no'] - weights_2['no'],
        'no2': weights_1['no2'] - weights_2['no2'],
        'o3': weights_1['o3'] - weights_2['o3'],
        'so2': weights_1['so2'] - weights_2['so2'],
        'pm2_5': weights_1['pm2_5'] - weights_2['pm2_5'],
        'pm10': weights_1['pm10'] - weights_2['pm10'],
        'nh3': weights_1['nh3'] - weights_2['nh3']
    }

    # Weighted Pollution Index (WPI)
    wpi = (weights['aqi'] * aqi_norm + weights['co'] * co_norm + weights['no'] * no_norm +
           weights['no2'] * no2_norm + weights['o3'] * o3_norm + weights['so2'] * so2_norm +
           weights['pm2_5'] * pm2_5_norm + weights['pm10'] * pm10_norm + weights['nh3'] * nh3_norm)

    # Total cost for each pollutant
    total_cost = (co * cost_per_unit['co'] +
                  no * cost_per_unit['no'] +
                  no2 * cost_per_unit['no2'] +
                  o3 * cost_per_unit['o3'] +
                  so2 * cost_per_unit['so2'] +
                  pm2_5 * cost_per_unit['pm2_5'] +
                  pm10 * cost_per_unit['pm10'] +
                  nh3 * cost_per_unit['nh3'])

    # Market influence
    market_influence = (market_demand / market_supply) * adjustment_factor

    # Final credit cost using WPI
    credit_cost = wpi * total_cost * market_influence

    # Adjust area cost using provided logic
    factor = credit_cost / 1000000
    adjusted_area_cost = area_cost + ((area_cost * factor) / 100)

    return credit_cost, adjusted_area_cost

@app.route('/')
def home():
    return jsonify(message="Dev Message, Reyan AQI API v2")
@app.route('/calculate_cost', methods=['POST'])
def calculate_cost():
    data = request.json

    location = data.get("location", "")
    latitude, longitude = 0, 0
    if location:
        latitude, longitude = get_coordinates(location)
    else:
        latitude = data.get("latitude")
        longitude = data.get("longitude")

    # Fetch AQI and pollutant data
    aqi_data = get_aqi(latitude, longitude)
    lon = aqi_data['coord']['lon']
    lat = aqi_data['coord']['lat']
    aqi = aqi_data['list'][0]['main']['aqi']
    co = aqi_data['list'][0]['components']['co']
    no = aqi_data['list'][0]['components']['no']
    no2 = aqi_data['list'][0]['components']['no2']
    o3 = aqi_data['list'][0]['components']['o3']
    so2 = aqi_data['list'][0]['components']['so2']
    pm2_5 = aqi_data['list'][0]['components']['pm2_5']
    pm10 = aqi_data['list'][0]['components']['pm10']
    nh3 = aqi_data['list'][0]['components']['nh3']

    area = data.get("area_size", 1.0) # default area size is 1 acre
    credit_cost_og = area * 100

    # Example parameters
    market_supply = 1000
    market_demand = 800
    adjustment_factor = 1.05

    cost_per_unit = {
        'co': 100,
        'no': 150,
        'no2': 200,
        'o3': 80,
        'so2': 90,
        'pm2_5': 120,
        'pm10': 110,
        'nh3': 70
    }

    # Calculate credit cost and adjusted area cost
    credit_cost, adjusted_area_cost = calculate_credit_cost(
        aqi, co, no, no2, o3, so2, pm2_5, pm10, nh3,
        market_supply, market_demand, adjustment_factor,
        cost_per_unit, credit_cost_og
    )

    return jsonify({
        "original_credit_cost": credit_cost_og,
        "adjusted_area_cost": adjusted_area_cost,
        "pollutants": {
            "aqi": aqi,
            "co": co,
            "no": no,
            "no2": no2,
            "o3": o3,
            "so2": so2,
            "pm2_5": pm2_5,
            "pm10": pm10,
            "nh3": nh3
        }
    })

if __name__ == "__main__":
    app.run(debug=True)
