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
