'''

This code is used to obtain data from the sensors for the ClimaCare project. The collected data is processed
and classified into a day profile using Decision Tree Classifiers. The processed data will be stored in the
InfluxDB server and displayed in a Grafana dashboard.

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
import pandas as pd
import pandas as pd
from sklearn.tree import DecisionTreeClassifier # Import Decision Tree Classifier
from sklearn.model_selection import train_test_split # Import train_test_split function
from sklearn import metrics #Import scikit-learn metrics module for accuracy calculation
from sklearn.preprocessing import LabelEncoder
import os
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

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
    # Connect to InfluxDB

    INFLUXDB_TOKEN=os.getenv('INFLUX_TOKEN')
    token = INFLUXDB_TOKEN
    org = "ClimaCare"
    url = "http://localhost:8086"

    client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)

    bucket="climacare-db"

    write_api = client.write_api(write_options=SYNCHRONOUS)
        
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
            
            # Wind speed and UV Index
            windsp, uv =  getWindSpeedUVIndex()
            sumWindSpeed += windsp
            sumUV += uv
                       
            # Pollen concentrations
            alder_pollen, birch_pollen, grass_pollen, mugwort_pollen, olive_pollen, ragweed_pollen = getPollenConcentrations()
            sumAlderPollen += alder_pollen
            sumBirchPollen += birch_pollen
            sumGrassPollen += grass_pollen
            sumMugwortPollen += mugwort_pollen
            sumOlivePollen += olive_pollen
            sumRagweedPollen += ragweed_pollen

            # Pressure
            pressure_value = read_pressure()
            sumPressure += pressure_value
            
            # Air quality
            pi = pigpio.pi()  # Connect to Pi
            dustsensor = Sensor(pi, 24)  # Set the GPIO pin number 24
            time.sleep(30) # Wait for 30 seconds for the sensor to calibrate
            aqi = dustsensor.get_aqi_and_pm_values()
            sumAQI += float(aqi)
            
            countMin += 1 # Increment the minute count
            time.sleep(30) # Wait for the resting 30 seconds in a minute
        
        '''

        If 30 minutes passed calculate the mean value for each parameter and classify the data into a day parameter
        using a Decision Tree Classifier. Then, write the data into InfluxDB.

        '''
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
                
            # Pressure
            resultPressure = sumPressure / 30
            
            '''
            
            Decision Tree Classification
            
            '''
            
            # Data classification (DECISION TREE CLASSIFICATION)
            
            # Read the training dataset

            df = pd.read_csv("data/BilbaoWeatherDataset.csv", sep = ";")

            # Data processing

            # Remove ending hypens in the labels
            df['DAY-PROFILE 1'] = df['DAY-PROFILE 1'].apply(lambda x: x[:-3] if x.endswith(" - ") else x)
            df['DAY-PROFILE 2'] = df['DAY-PROFILE 2'].apply(lambda x: x[:-3] if x.endswith(" - ") else x)

            # Convert the 'date' column to a datetime type
            df['DATE'] = pd.to_datetime(df['DATE'], format = '%d/%m/%Y')

            # Extract the month and create a new column 'month' to be used as a feature variable
            df['MONTH'] = df['DATE'].dt.month

            # Training sets

            X1_train = df[['TEMPERATURE', 'HUMIDITY', 'WINDSPEED', 'MONTH']] # Features
            y1_train = df['DAY-PROFILE 1'] # Target variable

            X2_train = df[['PRESSURE', 'UV INDEX', 'AIR QUALITY', 'MONTH']] # Features
            y2_train = df['DAY-PROFILE 2'] # Target variable

            # Create dataframes for the collected weather conditions

            X1_test = pd.DataFrame(data=[[resultTemp, resultHumidity, resultWS, datetime.datetime.now().month]], columns=['TEMPERATURE', 'HUMIDITY', 'WINDSPEED', 'MONTH'])

            X2_test = pd.DataFrame([[resultPressure, resultUV, resultAQI, datetime.datetime.now().month]], columns=['PRESSURE', 'UV INDEX', 'AIR QUALITY', 'MONTH'])

            # Decision Tree Classification

            # Create Decision Tree classifer object
            clf = DecisionTreeClassifier()

            # First day profile: temp, humidity, wind speed and month

            # Train Decision Tree Classifer
            clf1 = clf.fit(X1_train, y1_train)

            #Predict the response for test dataset
            y1_pred = clf1.predict(X1_test)

            # Second day profile: atmospheric pressure, uv index, air quality index, month

            # Train Decision Tree Classifer
            clf2 = clf.fit(X2_train, y2_train)

            # Predict the response for test dataset
            y2_pred = clf2.predict(X2_test)

            # Classification results

            result_df1 = pd.DataFrame({'Predicted 1': y1_pred})
            result_df2 = pd.DataFrame({'Predicted 2': y2_pred})
            result_df = pd.concat([result_df1, result_df2], axis=1)
            test_df1 = pd.DataFrame(X1_test, columns=['TEMPERATURE', 'HUMIDITY', 'WINDSPEED', 'MONTH'])
            test_df2 = pd.DataFrame(X2_test, columns=['PRESSURE', 'UV INDEX', 'AIR QUALITY', 'MONTH'])
            test_df = pd.concat([test_df1, test_df2], axis=1)
            result_df = pd.concat([test_df, result_df], axis=1)
            
            '''

            Recommendations for predicted day profiles
            
            '''
            
            recommendationStr = []
            
            # Day profile 1
            if(result_df['Predicted 1'].values[0] == "Cold"):
                recommendationStr = ["Llevar una chaqueta aislante de alta calidad para mantenerse abrigado", "Vestir con una capa intermedia entre la camisa y el abrigo", "Cubrir el cuello y cabeza, y usar guantes para las manos"]
            elif("Cold - High Humidity" in result_df['Predicted 1'].values[0]):
                recommendationStr = ["Vestir con una capa con materiales transpirables", "Llevar una capa exterior resistente al agua", "Usar calzado cálido e impermeable"]
            elif(result_df['Predicted 1'].values[0] == "Hot"):
                recommendationStr = ["Optar por comidas ligeras y ricas en agua, como vegetales y frutas, y evitar platos pesados", "Beber uno o dos litros de agua al día y evitar el alcohol", "Mantener algunas partes de tu cuerpo frescas, como los pies, tobillos, muñecas, la nuca, antebrazos y la sien", "Vestir ropa ligera y de colores claros"]
            elif("Hot - High Humidity" in result_df['Predicted 1'].values[0]):
                recommendationStr = ["Optar por comidas ligeras y ricas en agua, como vegetales y frutas, y evitar platos pesados", "Beber uno o dos litros de agua al día y evitar el alcohol", "Mantener algunas partes de tu cuerpo frescas, como los pies, tobillos, muñecas, la nuca, antebrazos y la sien", "Vestir ropa ligera y de colores claros", "A la hora de hacer ejercicio optar por las partes más frescas del día, temprano en la mañana o al atardecer"]
            elif(result_df['Predicted 1'].values[0] == "High Humidity"):
                recommendationStr = ["Vestir con una capa con materiales transpirables", "Es crucial mantener una hidratación constante", "A la hora de realizar actividad física optar por áreas bien ventiladas"]

            if("Windy" in result_df['Predicted 1'].values[0]):
                recommendationStr = recommendationStr + ["Usar chaquetas y pantalones fabricados con materiales diseñados para bloquear el viento", "Proteger los ojos con gafas de sol o gafas protectoras"]
            elif("Strong Wind" in result_df['Predicted 1'].values[0]):
                recommendationStr = recommendationStr + ["Usar chaquetas y pantalones fabricados con materiales diseñados para bloquear el viento", "En la calle, mantenterse alejado de cornisas, balcones y evitar áreas con sitios en construcción", "Evitar viajar en motocicleta o bicicleta;Proteger los ojos con gafas de sol o gafas protectoras"]

            # Day profile 2
            if("High UV" in result_df['Predicted 2'].values[0]):
                recommendationStr = recommendationStr + ["Al mediodía, mantenerse a la sombra", "Vestir ropa adecuada, un sombrero y gafas de sol", "Usar suficiente protector solar con la protección adecuada para la piel"]
            if("Extreme UV" in result_df['Predicted 2'].values[0]):
                recommendationStr = recommendationStr + ["Tomar precauciones adicionales, la piel no protegida puede dañarse y quemarse rápidamente", "Mantenterse alejado de reflectores de rayos UV como la arena blanca o superficies brillantes", "Usar suficiente protector solar con la protección adecuada para la piel", "Evitar el sol entre las 11:00 y las 16:00"]
            if("Low Pressure" in result_df['Predicted 2'].values[0]):
                recommendationStr = recommendationStr + ["Llevar un paraguas resistente al viento para protegerte de la lluvia", "Extremar las precauciones al conducir, ya que puede haber tormentas", "Si se es sensible a los cambios en la presión atmosférica, tomar precauciones adicionales, llevar los medicamentos necesarios y mantenerse hidratado"]
            if("Moderate AQI" in result_df['Predicted 2'].values[0]):
                recommendationStr = recommendationStr + ["Es seguro participar en actividades al aire libre, pero las personas extremadamente sensibles a la calidad del aire pueden considerar reducir la intensidad y duración de dichas actividades", "Si perteneces a un grupo sensible (como niños pequeños, personas mayores o aquellos con problemas respiratorios o cardíacos), puedes considerar limitar tu tiempo al aire libre"]
            if("Unhealthy AQI" in result_df['Predicted 2'].values[0]):
                recommendationStr = recommendationStr + ["Si se experimentan síntomas como irritación ocular, irritación de garganta, dificultad para respirar o problemas respiratorios, considerar reducir las actividades al aire libre", "El uso de mascarillas protectoras puede ser considerado, especialmente para aquellos sensibles a la calidad del aire"]

            '''
            
            Add pollen alerts

            '''
            pollenLevel = ""

            if((40 < resultAP < 80) or (40 < resultBP < 80) or (10 < resultGP < 50) or (20 < resultMP < 30) or (50 < resultOP < 200) or (10 < resultRP < 50)):
                pollenLevel = "Medio"
            if((resultAP > 80) or (resultBP > 80) or (resultGP > 50) or (resultMP > 30) or (resultOP > 200) or (resultRP > 50)):
                pollenLevel = "Alto"
            if(pollenLevel == ""):
                pollenLevel = "Bajo"          
            
            '''
            
            InfluxDB: write data into bucket
            
            '''
            
            # Write data into InfluxDB bucket
            influxdata = influxdb_client.Point("measure").tag("location", "Universidad de Deusto").field("temperture", result_df['TEMPERATURE'].values[0]).field("humidity", result_df['HUMIDITY'].values[0]).field("windspeed", result_df['WINDSPEED'].values[0]).field("pressure", result_df['PRESSURE'].values[0]).field("uv", result_df['UV INDEX'].values[0]).field("air_quality", result_df['AIR QUALITY'].values[0]).field("pollen", pollenLevel)
            write_api.write(bucket=bucket, org=org, record=influxdata)
            for r in recommendationStr:
                influxdata = influxdb_client.Point("measure").tag("location", "Universidad de Deusto").field("recommendations", r)
                write_api.write(bucket=bucket, org=org, record=influxdata)
                
            print("Data written succesfully")
