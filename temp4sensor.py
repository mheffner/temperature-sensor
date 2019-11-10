#!/usr/bin/python
#Based on Adafruit's Raspberry Pi Lesson 11 Temperature sensing tutorial by Simon Monk
#Modified by Tim Massaro 2/2014
#This script now uses a Raspberry Pi, Adafruit PiPlate LCD and 
#two DS18B20 temp sensor to monitor the freezer and fridge unit at Channel One Food Shelf 
#significant changes
#adapt for 2 sensors
#Display temperature on the LCD
#sendtext messages when temperature is out of range 

import os
import glob
import time
import pycurl
import StringIO
import requests
from requests.auth import HTTPBasicAuth
from decimal import Decimal

from time import sleep

import time

# reads the actual files where the DS18B20 temp sensor records it.
def read_temp_raw(device_file):
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

# read the temperature and return the Farenheit value to caller
def read_temp(file):
    lines = read_temp_raw(file)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.1)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_f
#        return temp_c, temp_f   # no need to return celcius
##        print temp_f
        return str(temp_f)[:5]

## MAIN

# need to be root to do this
#os.system('modprobe w1-gpio')
#os.system('modprobe w1-therm')

temps = {}
base_dir = '/sys/bus/w1/devices/'
try:
  devices = glob.glob(base_dir + '28*')
  for device in devices:
      temp = read_temp(device + '/w1_slave')
      basepath = os.path.basename(device)
      print "Device: %s, temp: %.2f" % (basepath, temp)
      temps[basepath] = temp
except:
  print "Error 23 reading temp sensor file, sensors connected?"
  exit(23)

now = int(time.time())
now = (now / 60) * 60

print "now is: %d" % now

gauges = []
for sensor in temps:
    gauges.append({'name': 'temp.sensor',
                   'value': temps[sensor],
                   'source': sensor,
                   'measure_time': now
                   })

print gauges

api_token = os.environ.get('LIBRATO_API_TOKEN')
if api_token == None:
    print 'Not posting to Librato'
    exit(0)

auth = HTTPBasicAuth('token', api_token)
r = requests.post('https://metrics-api.librato.com/v1/metrics', json={'gauges': gauges}, auth=auth)

if r.status_code != 200:
    print "Error: Invalid status code recieved: %d, body: %s" % (r.status_code, r.json())
    exit(1)
