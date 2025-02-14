import time
import board
import digitalio
import adafruit_max31855
import csv

print("Running Temp Test")

spi = board.SPI()
cs = digitalio.DigitalInOut(board.D5)
max = adafruit_max31855.MAX31855(spi, cs)

def get_temperature():
	tempC = max.temperature
	tempF = tempC * 9 / 5 + 32
	return tempF

# Write temperature to CSV
def log_temperature():
    ambient_temp = get_temperature()
    if ambient_temp is not None:
        with open('temperature_data.csv', mode='a') as file:
            writer = csv.writer(file)
            writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), ambient_temp])

while True:
	log_temperature()
	time.sleep(2.0)
