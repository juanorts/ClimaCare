# -*- coding: utf-8 -*-
'''
Original from http://abyz.co.uk/rpi/pigpio/examples.html
'''

from __future__ import print_function
import math
import pigpio

class sensor:
   """
   A class to read a Shinyei PPD42NS Dust Sensor, e.g. as used
   in the Grove dust sensor.

   This code calculates the percentage of low pulse time and
   calibrated concentration in particles per 1/100th of a cubic
   foot at user chosen intervals.

   You need to use a voltage divider to cut the sensor output
   voltage to a Pi safe 3.3V (alternatively use an in-line
   20k resistor to limit the current at your own risk).
   """

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
        https://en.wikipedia.org/wiki/Air_quality_index
	Computing_the_AQI
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
       

if __name__ == "__main__":

   import time

   while True:
      pi = pigpio.pi() # Connect to Pi.
   
      s = sensor(pi, 24) # set the GPIO pin number

      # Use 30s for a properly calibrated reading.
      time.sleep(30) 
      
      # get the gpio, ratio and concentration in particles / 0.01 ft3
      g, r, c = s.read()

      if (c==1114000.62):
          print("Error\n")
          continue

      print("Air Quality Measurements for PM2.5:")
      print("  " + str(int(c)) + " particles/0.01ft^3")

      # convert to SI units
      concentration_ugm3=s.pcs_to_ugm3(c)
      print("  " + str(int(concentration_ugm3)) + " ugm^3")
      
      # convert SI units to US AQI
      # input should be 24 hour average of ugm3, not instantaneous reading
      aqi=s.ugm3_to_aqi(concentration_ugm3)
      
      print("  Current AQI (not 24 hour avg): " + str(int(aqi)))
      
      if(int(aqi) >= 0 and int(aqi) <= 50):
          print("	Good")
      elif(int(aqi) >= 51 and int(aqi) <= 100):
          print("	Moderate")
      elif(int(aqi) >= 101 and int(aqi) <= 150):
          print("	Unhealthy for sensitive groups")
      elif(int(aqi) >= 151 and int(aqi) <= 200):
          print("	Unhealthy")
      elif(int(aqi) >= 201 and int(aqi) <= 300):
          print("	Very unhealthy")
      else:
          print("	Hazardous")
          
      print("")

      pi.stop() # Disconnect from Pi.

      time.sleep(5)
