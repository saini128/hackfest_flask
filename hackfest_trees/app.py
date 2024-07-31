from flask import Flask, request, jsonify
from flask_cors import CORS

import cv2
import numpy as np

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def calculate_green_percentage(image_path):
    # Load the image
    image = cv2.imread(image_path)

    if image is None:
        print("Failed to load image.")
        return 0.0

    # Convert the image to the HSV color space
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define masks for dark green and light green colors
    lower_dark_green = np.array([40, 40, 40])
    upper_dark_green = np.array([70, 255, 255])
    dark_green_mask = cv2.inRange(hsv, lower_dark_green, upper_dark_green)

    lower_light_green = np.array([35, 40, 40])
    upper_light_green = np.array([85, 255, 255])
    light_green_mask = cv2.inRange(hsv, lower_light_green, upper_light_green)

    # Morphological operations to clean up the masks
    kernel = np.ones((5, 5), np.uint8)
    dark_green_mask = cv2.morphologyEx(dark_green_mask, cv2.MORPH_CLOSE, kernel)
    light_green_mask = cv2.morphologyEx(light_green_mask, cv2.MORPH_CLOSE, kernel)

    # Calculate the number of dark green and light green pixels
    dark_green_pixels = cv2.countNonZero(dark_green_mask)
    light_green_pixels = cv2.countNonZero(light_green_mask)

    # Calculate the total number of pixels
    total_pixels = image.shape[0] * image.shape[1]

    # Calculate the percentage of dark green and light green pixels
    dark_green_percentage = (dark_green_pixels / total_pixels) * 100
    light_green_percentage = (light_green_pixels / total_pixels) * 100

    # Calculate the total greenery percentage
    total_green_percentage = dark_green_percentage + light_green_percentage

    return {
        'dark_green_percentage': dark_green_percentage,
        'light_green_percentage': light_green_percentage,
        'total_green_percentage': total_green_percentage
    }
@app.route('/', methods=['Get'])
def index():
    resp={
        "message":"Count trees from image file"
    }
    return jsonify(resp)
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    file_path = './uploaded_image.jpg'
    file.save(file_path)

    green_percentages = calculate_green_percentage(file_path)

    return jsonify(green_percentages)

if __name__ == '__main__':
    app.run(debug=True)
