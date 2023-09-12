import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Dictionary to store request counts per IP address
request_counts = {}

# Get the rate limit and window from environment variables
REQUEST_LIMIT = int(os.getenv("REQUEST_LIMIT"))
REQUEST_WINDOW = int(os.getenv("REQUEST_WINDOW"))

def get_remote_address():
    # Custom function to get the client's IP address
    return request.remote_addr

def rate_limit_exceeded(ip_address):
    # Check if the rate limit has been exceeded for the given IP address
    current_time = time.time()
    if ip_address in request_counts:
        count, timestamp = request_counts[ip_address]
        if current_time - timestamp < REQUEST_WINDOW:
            if count >= REQUEST_LIMIT:
                return True, REQUEST_LIMIT  # Include REQUEST_LIMIT in the response
        else:
            # Reset the count if the window has passed
            request_counts[ip_address] = (1, current_time)
    else:
        request_counts[ip_address] = (1, current_time)
    return False, None  # Include None if rate limit is not exceeded


def get_elevation(lat, lon):
    # URL of the webpage
    url = "https://geographiclib.sourceforge.io/cgi-bin/GeoidEval"

    # Define the parameters in the URL
    params = {
        "input": f"{lat} {lon}",
        "option": "Submit"
    }

    # Send the GET request with the parameters
    response = requests.get(url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the geoid heights section
        geoid_heights_section = soup.find("font", size="4")

        if geoid_heights_section:
            # Extract the text content from the section
            section_text = geoid_heights_section.get_text()

            # Extract data using regular expressions
            import re
            pattern_egm2008 = r"EGM2008\s*=\s*([\d.]+)"
            pattern_egm96 = r"EGM96\s*=\s*([\d.]+)"
            pattern_egm84 = r"EGM84\s*=\s*([\d.]+)"

            match_egm2008 = re.search(pattern_egm2008, section_text)
            match_egm96 = re.search(pattern_egm96, section_text)
            match_egm84 = re.search(pattern_egm84, section_text)

            # Check if all data is available
            if match_egm2008 and match_egm96 and match_egm84:
                egm2008 = match_egm2008.group(1)
                egm96 = match_egm96.group(1)
                egm84 = match_egm84.group(1)

                # Return the extracted data as a dictionary
                elevation_data = {
                    'EGM2008': float(egm2008),
                    'EGM96': float(egm96),
                    'EGM84': float(egm84),
                }

                return elevation_data
            else:
                return None
        else:
            return None
    else:
        return None

@app.route('/get_height', methods=['GET'])
def get_height():
    ip_address = get_remote_address()
    exceeded, limit = rate_limit_exceeded(ip_address)
    
    if exceeded:
        return jsonify({'error': f'429 Too Many Request, Only {limit} request per every 10seconds allowed'}), 429  # Include limit in the response

    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))

        elevation_data = get_elevation(lat, lon)

        if elevation_data:
            return jsonify(elevation_data)
        else:
            return jsonify({'error': 'Failed to retrieve elevation data'}), 500

    except ValueError:
        return jsonify({'error': 'Invalid coordinates'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)