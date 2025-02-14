from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS
import csv
import time
import adafruit_max31855
import digitalio
import board
import threading
import subprocess
import requests
import os
import shutil
from datetime import datetime, timedelta


app = Flask(__name__, static_folder='static', template_folder='static')
CORS(app)

spi = board.SPI()
cs = digitalio.DigitalInOut(board.D5)
max = adafruit_max31855.MAX31855(spi, cs)

# def get_nest_data():
#     try:
#         # Move these to environment variables or config file for security
#         projectID = 'templog-450802'
#         oauth2_client_id = '761748715430-hq015v4quo94cbiqphr3u6abrc5attdv.apps.googleusercontent.com'    
#         oauth2_client_secret = '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'
#         # You'll need to generate a new refresh token
#         refreshToken = '1//01U413t74wj9nCgYIARAAGAESNwF-L9Ir51AnYdpfRcfarEsMaqJFN8roF5MOYQ3R7I3sDdbdl0TaTANIq6jKJPriCPmp1Bn6MQ'

#         # Get new access token
#         get_access_token_url = "https://oauth2.googleapis.com/token"  # Updated URL
#         get_access_token_data = {
#             "client_id": oauth2_client_id,
#             "client_secret": oauth2_client_secret,
#             "refresh_token": refreshToken,
#             "grant_type": "refresh_token"
#         }

#         get_access_token_response = requests.post(
#             get_access_token_url, 
#             data=get_access_token_data,
#             headers={
#                 "Content-Type": "application/x-www-form-urlencoded"
#             }
#         )
        
#         if not get_access_token_response.ok:
#             return f"Token Error Response: {get_access_token_response.text}"
            
#         access_token = get_access_token_response.json().get("access_token")

#         # Get Nest data with new access token
#         get_nest_data_url = f"https://smartdevicemanagement.googleapis.com/v1/enterprises/{projectID}/devices"
#         get_nest_data_headers = {
#             "Content-Type": "application/json",
#             "Authorization": f"Bearer {access_token}"
#         }

#         data_response = requests.get(get_nest_data_url, headers=get_nest_data_headers)
#         if not data_response.ok:
#             return f"Nest Data Error Response: {data_response.text}"
            
#         devices = data_response.json().get('devices', [])
#         temperatures = []
        
#         for device in devices:
#             if 'traits' in device and 'sdm.devices.traits.Temperature' in device['traits']:
#                 temp_celsius = device['traits']['sdm.devices.traits.Temperature']['ambientTemperatureCelsius']
#                 temp_fahrenheit = (temp_celsius * 9/5) + 32
#                 device_name = device.get('traits', {}).get('sdm.devices.traits.Info', {}).get('customName', 'Unknown Device')
#                 temperatures.append({
#                     'name': device_name,
#                     'temperature': round(temp_fahrenheit, 1)
#                 })
        
#         return temperatures
#     except Exception as e:
#         print(f"Error getting Nest data: {str(e)}")
#         return f"Error getting Nest data: {str(e)}"

def get_cpu_temp():
    temp = subprocess.check_output("vcgencmd measure_temp", shell=True).decode()
    return (float(temp.replace("temp=", "").replace("'C\n", "")) * 9 / 5) + 32

def get_gpu_temp():
    temp = subprocess.check_output("cat /sys/class/thermal/thermal_zone0/temp", shell=True).decode()
    return (float(temp) / 1000) * 9 / 5 + 32  # Convert from millidegrees

@app.route('/temps', methods=['GET'])
def temps():
    return jsonify({"cpu_temp": get_cpu_temp(), "gpu_temp": get_gpu_temp()})

def get_temperature():
    tempC = max.temperature
    tempF = tempC * 9 / 5 + 32
    print(tempF)
    return tempF

def get_csv_filename():
    return f'temperature_data_{time.strftime("%Y-%m-%d")}.csv'

def log_temperature():
    temp = get_temperature()
    if temp != 32:
        filename = get_csv_filename()
        with open(filename, mode='a') as file:
            writer = csv.writer(file)
            writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), temp])

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/get_latest_temperature', methods=['GET'])
def get_latest_temperature():
    try:
        filename = get_csv_filename()
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            last_row = list(reader)[-1]  # Get the last row
            timestamp, temperature = last_row
            return jsonify({'timestamp': timestamp, 'temperature': temperature})
    except (FileNotFoundError, IndexError):
        return jsonify({'error': 'No data available'}), 500

@app.route('/get_csv')
def get_csv():
    filename = get_csv_filename()
    return send_from_directory('.', filename, as_attachment=True)

@app.route('/get_csv_json')
def get_csv_json():
    try:
        filename = get_csv_filename()
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            data = [{"timestamp": row[0], "temperature": float(row[1])} for row in reader if row]  # Convert CSV to JSON
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({'error': 'No data available'}), 500

def archive_old_files():
    # Create archive directory if it doesn't exist
    archive_dir = 'temperature_archives'
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
    
    # Get current date
    current_date = datetime.now()
    
    # Look for CSV files in current directory
    for filename in os.listdir('.'):
        if filename.startswith('temperature_data_') and filename.endswith('.csv'):
            # Extract date from filename
            try:
                file_date_str = filename.replace('temperature_data_', '').replace('.csv', '')
                file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
                
                # If file is older than 7 days, move it to archive
                if (current_date - file_date).days > 7:
                    shutil.move(filename, os.path.join(archive_dir, filename))
            except ValueError:
                continue  # Skip files that don't match expected format

@app.route('/historical_data', methods=['GET'])
def get_historical_data():
    try:
        # Get date from query parameters, default to today
        date_str = request.args.get('date', time.strftime("%Y-%m-%d"))
        
        # Construct filename
        filename = f'temperature_data_{date_str}.csv'
        
        # Check current directory first
        if os.path.exists(filename):
            file_path = filename
        else:
            # Check archive directory
            archive_path = os.path.join('temperature_archives', filename)
            if os.path.exists(archive_path):
                file_path = archive_path
            else:
                return jsonify({'error': f'No data available for {date_str}'}), 404
        
        # Read and return the data
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            data = [{"timestamp": row[0], "temperature": float(row[1])} for row in reader if row]
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def log_temperature_background():
    while True:
        log_temperature()
        # Archive old files once per day at midnight
        if datetime.now().hour == 0 and datetime.now().minute == 0:
            archive_old_files()
        time.sleep(2.0)

# @app.route('/nest_temperatures', methods=['GET'])
# def nest_temperatures():
#     temps = get_nest_data()
#     return jsonify(temps)

if __name__ == '__main__':
    threading.Thread(target=log_temperature_background, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=True)
