'''

This code is used to obtain data from the sensors for the ClimaCare project. The collected data is processed
and classified into a day profile using Decision Tree Classifiers. The processed data will be stored in the
database.

SENSORS:
- Temperature & Humidity Sensor (Port D5)
- Dust Sensor (Port D24)
- Barometer Sensor BME 280 (Port I2C x66)

'''

# Imports
from __future__ import print_function
import math
import pigpio
import time
from seeed_dht import DHT # Temp & humidity sensor
import requests # REST APIs
import subprocess
import datetime

# Temperature and humidity
def getTemperatureHumidity():
    sensor = DHT('11', 5)
    humidity, temperature = sensor.read()
    return temperature, humidity

# External data (REST API: Weatherstack): Wind speed, UV Index
def getWindSpeedUVIndex():
    params = {
        'access_key': '721a04984f62bbfc8900c300327807bb',
        'type': 'Ip',
        'query': '130.206.138.233',
        'units': 'm',
    }
    
    response = requests.get('http://api.weatherstack.com/current', params).json()
    wind_speed = response['current']['wind_speed']
    uv = response['current']['uv_index']
    
    return wind_speed, uv

# External data (REST API: Weatherstack): Pollen concentration (alder, birch, grass, mugwort, olive, ragweed)
def getPollenConcentrations():
    response = requests.get('https://air-quality-api.open-meteo.com/v1/air-quality?latitude=43.270097&longitude=-2.938766&current=alder_pollen,birch_pollen,grass_pollen,mugwort_pollen,olive_pollen,ragweed_pollen&domains=cams_europe').json()

    alder_pollen = response['current']['alder_pollen']
    birch_pollen = response['current']['birch_pollen']
    grass_pollen = response['current']['grass_pollen']
    mugwort_pollen = response['current']['mugwort_pollen']
    olive_pollen = response['current']['olive_pollen']
    ragweed_pollen = response['current']['ragweed_pollen']
    
    return alder_pollen, birch_pollen, grass_pollen, mugwort_pollen, olive_pollen, ragweed_pollen
    
# Air quality (PM2.5 and AQI)

'''
Original from http://abyz.co.uk/rpi/pigpio/examples.html
'''

class Sensor:

   def __init__(self, pi, gpio):
      """
      Instantiate with the Pi and gpio to which the sensor
      is connected.
      """

      self.pi = pi
      self.gpio = gpio

      self._start_tick = None
      self._last_tick = None
      self._low_ticks = 0
      self._high_ticks = 0

      pi.set_mode(gpio, pigpio.INPUT)

      self._cb = pi.callback(gpio, pigpio.EITHER_EDGE, self._cbf)

   def read(self):
      """
      Calculates the percentage low pulse time and calibrated
      concentration in particles per 1/100th of a cubic foot
      since the last read.

      For proper calibration readings should be made over
      30 second intervals.

      Returns a tuple of gpio, percentage, and concentration.
      """
      interval = self._low_ticks + self._high_ticks

      if interval > 0:
         ratio = float(self._low_ticks)/float(interval)*100.0
         conc = 1.1*pow(ratio,3)-3.8*pow(ratio,2)+520*ratio+0.62;
      else:
         ratio = 0
         conc = 0.0

      self._start_tick = None
      self._last_tick = None
      self._low_ticks = 0
      self._high_ticks = 0

      return (self.gpio, ratio, conc)

   def _cbf(self, gpio, level, tick):

      if self._start_tick is not None:

         ticks = pigpio.tickDiff(self._last_tick, tick)

         self._last_tick = tick

         if level == 0: # Falling edge.
            self._high_ticks = self._high_ticks + ticks

         elif level == 1: # Rising edge.
            self._low_ticks = self._low_ticks + ticks

         else: # timeout level, not used
            pass

      else:
         self._start_tick = tick
         self._last_tick = tick
         

   def pcs_to_ugm3(self, concentration_pcf):
        '''
        Convert concentration of PM2.5 particles per 0.01 cubic feet to µg/ metre cubed
        this method outlined by Drexel University students (2009) and is an approximation
        does not contain correction factors for humidity and rain
        '''
        
        if concentration_pcf < 0:
           raise ValueError('Concentration cannot be a negative number')
        
        # Assume all particles are spherical, with a density of 1.65E12 µg/m3
        densitypm25 = 1.65 * math.pow(10, 12)
        
        # Assume the radius of a particle in the PM2.5 channel is .44 µm
        rpm25 = 0.44 * math.pow(10, -6)
        
        # Volume of a sphere = 4/3 * pi * radius^3
        volpm25 = (4/3) * math.pi * (rpm25**3)
        
        # mass = density * volume
        masspm25 = densitypm25 * volpm25
        
        # parts/m3 =  parts/foot3 * 3531.5
        # µg/m3 = parts/m3 * mass in µg
        concentration_ugm3 = concentration_pcf * 3531.5 * masspm25
        
        return concentration_ugm3


   def ugm3_to_aqi(self, ugm3):
        '''
        Convert concentration of PM2.5 particles in µg/ metre cubed to the USA 
        Environment Agency Air Quality Index - AQI
        https://en.wikipedia.org/wiki/Air_quality_index Computing_the_AQI
        https://github.com/intel-iot-devkit/upm/pull/409/commits/ad31559281bb5522511b26309a1ee73cd1fe208a?diff=split
        '''
        
        cbreakpointspm25 = [ [0.0, 12, 0, 50],\
                        [12.1, 35.4, 51, 100],\
                        [35.5, 55.4, 101, 150],\
                        [55.5, 150.4, 151, 200],\
                        [150.5, 250.4, 201, 300],\
                        [250.5, 350.4, 301, 400],\
                        [350.5, 500.4, 401, 500], ]
                        
        C=ugm3
        
        if C > 500.4:
            aqi=500

        else:
           for breakpoint in cbreakpointspm25:
               if breakpoint[0] <= C <= breakpoint[1]:
                   Clow = breakpoint[0]
                   Chigh = breakpoint[1]
                   Ilow = breakpoint[2]
                   Ihigh = breakpoint[3]
                   aqi=(((Ihigh-Ilow)/(Chigh-Clow))*(C-Clow))+Ilow
        
        return aqi

   def get_aqi_and_pm_values(self):

          # Get the gpio, ratio, and concentration in particles / 0.01 ft3
          g, r, c = self.read()

          if c == 1114000.62:
              print("Error\n")
              return 0.0

          # Convert to SI units
          concentration_ugm3 = self.pcs_to_ugm3(c)

          # Convert SI units to US AQI
          # Input should be a 24-hour average of ugm3, not an instantaneous reading
          aqi = self.ugm3_to_aqi(concentration_ugm3)

          self.pi.stop()  # Disconnect from Pi.

          return aqi

# Pressure
def read_pressure():
    # Run the command and capture the output
    result = subprocess.run(["read_bme280", "--pressure"], capture_output=True, text=True)

    # Check if the command was successful (return code 0)
    if result.returncode == 0:
        # Extract and return the pressure value
        pressure = result.stdout.strip()
        return float(pressure[:-4])
    else:
        # Handle the case when the command fails
        print(f"Error: Unable to read pressure. Exit code: {result.returncode}")
        return None

# Main

if __name__ == "__main__":
    
    # Run this command for the Dust Sensor
    import subprocess
    command = "sudo pigpiod"
    process = subprocess.Popen(command, shell=True)
    process.wait()
    if process.returncode == 0:
        print("Command executed successfully")
    else:
        print("Error executing command")
    
    ''' For each parameter we will obtain the value every minute and calculate the average value every 30 minutes '''
    while True:
        
        countMin = 0 # Counter of minutes
        sumTemp = 0
        sumHumidity = 0
        sumWindSpeed = 0
        sumUV = 0
        sumAlderPollen = 0
        sumBirchPollen = 0
        sumGrassPollen = 0
        sumMugwortPollen = 0
        sumOlivePollen = 0
        sumRagweedPollen = 0
        sumAQI = 0
        sumPressure = 0
        
        # Execute for 30 minutes
        while countMin < 30:
            
            print(f"\nMINUTE: {countMin}")
            
            # Temperature and humidity
            temp = 0.0
            humidity = 0.0
            while temp == 0 and humidity == 0:
                temp, humidity = getTemperatureHumidity()
            sumTemp += temp
            sumHumidity += humidity
            
            print("Temperature:", temp, "ºC")
            print("Humidity:", humidity, "%")    
            
            # Wind speed and UV Index
            windsp, uv =  getWindSpeedUVIndex()
            sumWindSpeed += windsp
            sumUV += uv
            
            print("Wind speed:", windsp)
            print("UV Index:", uv)
                       
            # Pollen concentrations
            alder_pollen, birch_pollen, grass_pollen, mugwort_pollen, olive_pollen, ragweed_pollen = getPollenConcentrations()
            sumAlderPollen += alder_pollen
            sumBirchPollen += birch_pollen
            sumGrassPollen += grass_pollen
            sumMugwortPollen += mugwort_pollen
            sumOlivePollen += olive_pollen
            sumRagweedPollen += ragweed_pollen
            
            print("Pollen concentrations:", alder_pollen, birch_pollen, grass_pollen, mugwort_pollen, olive_pollen, ragweed_pollen)

            # Pressure
            pressure_value = read_pressure()
            sumPressure += pressure_value

            if pressure_value is not None:
                print(f"Pressure: {pressure_value} hPa")
            else:
                print("Failed to read pressure.")
            
            # Air quality
            pi = pigpio.pi()  # Connect to Pi
            dustsensor = Sensor(pi, 24)  # Set the GPIO pin number 24
            time.sleep(30) # Wait for 30 seconds for the sensor to calibrate
            aqi = dustsensor.get_aqi_and_pm_values()
            sumAQI += float(aqi)
            
            print("Air Quality:", aqi)
            
            countMin += 1 # Increment the minute count
            time.sleep(30) # Wait for the resting 30 seconds in a minute
        
        # If the number of minutes passed is 30 then calculate the mean values and save them in the DB
        if (countMin == 30):
            # Temperature
            resultTemp = sumTemp / 30
            
            # Humidity
            resultHumidity = sumHumidity / 30
            
            # Wind Speed
            resultWS = sumWindSpeed / 30
            
            # UV
            resultUV = sumUV / 30
            
            # Pollen concentrations
            resultAP = sumAlderPollen / 30
            resultBP = sumBirchPollen / 30
            resultGP = sumGrassPollen / 30
            resultMP = sumMugwortPollen / 30
            resultOP = sumOlivePollen / 30
            resultRP = sumRagweedPollen / 30
            
            # Air quality           
            resultAQI = sumAQI / 30
            
            aqi_category = ""

            if 0 <= int(resultAQI) <= 50:
                aqi_category = "Good"
            elif 51 <= int(resultAQI) <= 100:
                aqi_category = "Moderate"
            elif 101 <= int(resultAQI) <= 150:
                aqi_category = "Unhealthy for sensitive groups"
            elif 151 <= int(resultAQI) <= 200:
                aqi_category = "Unhealthy"
            elif 201 <= int(resultAQI) <= 300:
                aqi_category = "Very unhealthy"
            else:
                aqi_category = "Hazardous"
                
            # Pressure
            resultPressure = sumPressure / 30
            
            # Print results
            print("\nDATA FROM", datetime.datetime.now())
            print("Temperature:", resultTemp, "ºC")
            print("Humidity:", resultHumidity, "%")
            print("Wind Speed:", resultWS, "km/h")
            print("UV:", resultUV)
            print("Pollen concentrations:", resultAP, resultBP, resultGP, resultMP, resultOP, resultRP)
            print("Air Quality:", resultAQI, aqi_category)
            print("Pressure:", resultPressure)
            print("_________________________\n")
            
