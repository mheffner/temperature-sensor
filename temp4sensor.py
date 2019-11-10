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
from decimal import Decimal
global textsent  # used to avoid sending too many texts
global toggledots # toggle the colon on LCD to indicate running
textsent = 0
toggledots = 0

# init the acceptable temperature ranges - these will be overridden by config file 
# TODO: Define Workhours & Offhours, ranges could be different
workLowFridge = 30
workHiFridge = 45
workLowFreezer = 30
workHiFreezer = 45

from time import sleep
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate

import threading
import time

# Timer thread will kick off every xx seconds and measure the temperature
class TimerClass(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.event = threading.Event()

    def run(self):
        while not self.event.is_set():
##            print "Checking Temperature......"
            fridgeTemp = read_temp(1) # sensor 1 is the Fridge unit
            freezerTemp = read_temp(2) # sensor 2 is the Freezer unit
            checkTempRanges(fridgeTemp, freezerTemp)       
            time.sleep(2)  # Sleep between temperature checks
            lcd.backlight(lcd.GREEN) # if temp is too warm or cold this causes a flash
            self.event.wait( 3 )

    def stop(self):
        self.event.set()


# reads the actual files where the DS18B20 temp sensor records it.
def read_temp_raw(sense):
    global toggledots
    semi = ((' ',':'))   # toggle colon to prove we are running

    if sense == 1:
##      print "----sensor 1:----"
      if toggledots is 0:
        toggledots = 1
      else:    
        toggledots = 0
      lcd.home()
      lcd.message(" Fridge" + semi[toggledots] + '  ')
      f = open(device_file, 'r')
    else:
##      print "sensor 2:"
      lcd.message('\n Freezer'+ semi[toggledots] + ' ' )
      f = open(device_file_two, 'r')
 
    lines = f.readlines()
    f.close()
    return lines

# read the temperature and return the Farenheit value to caller
def read_temp(sense):
    lines = read_temp_raw(sense)	 
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.1)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        lcd.message(str(temp_f)[:5])
#        return temp_c, temp_f   # no need to return celcius
##        print temp_f
        return str(temp_f)[:5]

# check the fridge and freezer temps passed in vs the allowed ranges and error out if invalid
def checkTempRanges(fridgeTemp, freezerTemp):
    global textsent
    # TODO: if workhours could have a different range
    if ((Decimal(fridgeTemp) > Decimal(workHiFridge)) or (Decimal(freezerTemp) > Decimal(workHiFreezer))):
##       print ("Temp too warm! Fridge: " + str(fridgeTemp) + " Freezer: " + str(freezerTemp) ) 
##       print workHiFridge
##       print workHiFreezer
##       print ("Text to number: " + phonenumber)
       lcd.backlight(lcd.RED)
	# Play alert sound (had to sudo apt-get mpg321 to get this command)
       os.system('mpg321 -l 3 -q /home/pi/bin/Robot_blip_2-Marianne_Gagnon-299056732.mp3 1>&- 2>&-')
#       os.system('mpg321 -l 3 /home/pi/bin/Robot_blip_2-Marianne_Gagnon-299056732.mp3 &')
#       os.system('mpg321 Alien_Siren-KevanGC-610357990.mp3 &')

       if textsent is 0: # don't sent too many texts   
         sendTextMessageHub("Temp too warm " + str(fridgeTemp) + ' ' + str(freezerTemp),"15073986309")
    if ((Decimal(fridgeTemp) < Decimal(workLowFridge)) or (Decimal(freezerTemp) < Decimal(workLowFreezer))):
##       print ("temp too cold! " + str(fridgeTemp) + ' ' + str(freezerTemp))
       lcd.backlight(lcd.BLUE)
##       print ("Text to number: " + phonenumber)
	# Play alert sound (had to sudo apt-get mpg321 to get this command)
       os.system('mpg321 -q Alien_Siren-KevanGC-610357990.mp3 > /dev/null > 2&1  &')
       if textsent is 0: # don't sent too many texts   
         sendTextMessageHub("Temp too cold " + str(fridgeTemp) + ' ' + str(freezerTemp),"15073986309")

# sentTextMessage - using the Twilio services
def sendTextMessage(message,number):
    # using Twilio Account, costs 1 cent per message
    #TODO only text every xx mins
    global textsent
    c = pycurl.Curl()
    # send text via Twilio acct
    c.setopt(c.URL, 'https://api.twilio.com/2010-04-01/Accounts/AC4bf7d2e514927e130c3b365057c6063e/SMS/Messages.json')
    c.setopt(c.USERPWD,'AC4bf7d2e514927e130c3b365057c6063e:b8c65e3890a310e553200b518d442672')
    c.setopt(c.POSTFIELDS,"From=+15072982476&To=+15073986309&Body=TOOwarmmessage")
    contents = StringIO.StringIO()
    c.setopt(c.WRITEFUNCTION, contents.write)
    c.perform()
    lineout = contents.getvalue()
##    print lineout

# send a text message with the SendHub service (free within limits)
#curl -H "Content-Type: application/json" -X POST --data '{"contacts" : [10814508],"text" : "Testing"}' 
#https://api.sendhub.com/v1/messages/?username=15073986309\&api_key=41babd0e296dacd4f66e67c5ab6c12ac0e5676bb
def sendTextMessageHub(message,number):
    global textsent
    #TODO only text every xx mins
    c = pycurl.Curl()
    # send text via sendhub
    headers = {"Content-Type": "application/json"}
#contact 10814508 sends to my google voice account
#    data = '{"contacts" : [10814508],"text" : "Testing"}'
#contact 10805718 sends to my cellphone
    data = '{"contacts" : [10805718],"text" : "%s "}' % (message)
##    print 'sending to sendhub contact:' + data
    c.setopt(c.URL, 'https://api.sendhub.com/v1/messages/?username=15073986309&api_key=41babd0e296dacd4f66e67c5ab6c12ac0e5676bb')
    c.setopt(pycurl.HTTPHEADER, ['Accept:application/json','Content-Type:application/json'])
    c.setopt(pycurl.POST, 1)
    c.setopt(c.POSTFIELDS,data)
    contents = StringIO.StringIO()
    c.setopt(c.WRITEFUNCTION, contents.write)

    try: 
##tjm      c.perform()
      textsent = 1
    except:
      print "could not send text, internet access?"
    lineout = contents.getvalue()
##    print lineout

# getButton - poll the buttons on the Adafruit PiPlate return button pressed
def getButton():
    global prev
    while True:
      for b in btn:
        if lcd.buttonPressed(b[0]):
          if b is not prev:
              lcd.clear()
              prev = b
              return b[0]
          break

## Codebegins here:

prev = -1
try:   #sudo authority required
  lcd = Adafruit_CharLCDPlate()
except:
  print "Error, sudo authority required"
  exit(21)  

# define backlight colors
col = (lcd.RED , lcd.YELLOW, lcd.GREEN, lcd.TEAL,
       lcd.BLUE, lcd.VIOLET, lcd.ON   , lcd.OFF)

# Define buttons on the PiPlate
btn = ((lcd.SELECT, 'Select', lcd.ON),
           (lcd.LEFT  , 'Left'  , lcd.RED),
           (lcd.UP    , 'Up'    , lcd.BLUE),
           (lcd.DOWN  , 'Down'  , lcd.GREEN),
           (lcd.RIGHT , 'Right' , lcd.VIOLET))
lcd.ON
lcd.clear()
lcd.message("Temp4Sensor\nMonitor Start...")
# scroll through colors for the fun of it
for c in col:
    lcd.backlight(c)
    sleep(.3)
lcd.backlight(lcd.GREEN)

# need to be root to do this
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
try:
  device_folder = glob.glob(base_dir + '28*')[0]
  device_file = device_folder + '/w1_slave'
##  print device_folder
  device_folder_two = glob.glob(base_dir + '28*')[1]
  device_file_two = device_folder_two + '/w1_slave'
##  print device_folder_two
except:
  print "Error 23 reading temp sensor file, sensors connected?"
  lcd.backlight(lcd.RED)
  lcd.clear()
  lcd.home()
  lcd.message("Error 23 Reading\nTemp Sensor!")
  exit(23)  

# Read config file to set defaults
# Config file contains a separate line for each of these(in Farenheit)
# Low Fridge Temp, High Fridge Temp
# Low Freezer Temp, High Freezer Temp
# Phone number to text 1xxxyyyzzzz
try: 
  f = open('/home/pi/bin/temp4sensor.cfg', 'r')
except:
  print "Error on file Open tempsense.cfg"
  lcd.clear()
  lcd.message("Error on open \ntempsense.cfg")
  lcd.backlight(lcd.RED)
  exit(22)
lines = f.readlines()
f.close()
workLowFridge = int(lines[1])
workHiFridge = int(lines[2])
workLowFreezer=int(lines[3])
workHiFreezer=int(lines[4])
phonenumber=lines[5]
#Debug print lines

message = "Fridge:  %sF-%sF" % (workLowFridge,workHiFridge)
##print message
lcd.clear()
lcd.message(message)

message = "\nFreezer: %sF-%sF" % (workLowFreezer,workHiFreezer)
# display acceptable temperature ranges from config file
##print message
lcd.message(message)
time.sleep( 3 )
##print "setting up timer for tempcheck"
lcd.clear()

tmr = TimerClass()
tmr.start()  # start the timer thread which will wake up and measure temperature

time.sleep( 1 )
but = getButton()  # if user presses a button we'll exit
tmr.stop()
time.sleep( 1 )    # sleep so we can clear the screen

##print but

lcd.clear()
lcd.backlight(lcd.OFF)
