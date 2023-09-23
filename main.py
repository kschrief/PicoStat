import network
import machine
import utime
import dht
import variables
import json
import _thread

import urequests as requests
 
sensor = dht.DHT22(machine.Pin(2)) 

led_pin = machine.Pin("LED", machine.Pin.OUT)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

retry = 5
timeToRetry = 2

def connectToWiFi(force):
    
    #Return if we're already connected
    if wlan.isconnected() is True and force is False:
        print("WiFi already connected")
        return
    
    print("Connecting to WiFi")
    wlan.disconnect()

    for x in range(retry):
        try:
            wlan.connect(variables.UUID, variables.Password)
            utime.sleep(0.5)
        except:
            print("WiFi Connection Error")
        
        if wlan.isconnected() is True:
            print("WiFi connected. Sleeping to allow proper connection")
            utime.sleep(5)
            return
        
        print("WiFi did not connect after attempt number " + str(x) + ".")
        utime.sleep(timeToRetry)
            
connectToWiFi(False)
concurrentExceptions = 0

try: 
    while True:
        #Get reading
        sensor.measure()
        
        #Get temperature and set to freedom units
        tempCelsius = sensor.temperature()
        tempFahrenheit = (tempCelsius * 9/5) + 32
        
        #Get humidity
        hum = sensor.humidity()
                
        #Re-Connect to WiFi if necessary
        if wlan.isconnected() is False:
            connectToWiFi(False)
        
        #If we're STILL not online, print an error and loop
        if wlan.isconnected() is False:
            print("Unable to connect to WiFi to push data")
            utime.sleep(variables.readingInterval)
            continue
        
        #Generate Temperature/Humidity URLs
        temperatureUrl = variables.AdafruitUrl + variables.AdafruitGroup + "." + variables.AdafruitTemperatureName + "/data"
        humidityUrl = variables.AdafruitUrl + variables.AdafruitGroup + "." + variables.AdafruitHumidityName + "/data"
            
        headers = {'X-AIO-Key': variables.AdafruitKey,
               'content-type': 'application/json'}

        temperatureData = '{"value": "' + str(tempFahrenheit) + '"}'
        humidityData = '{"value": "' + str(hum) + '"}'
        
        print("-----")
        print("Temperature: {}°F   Humidity: {:.0f}% ".format(tempFahrenheit, hum))
        print("-----")
        print(temperatureUrl)
        print(headers)
        print(temperatureData)
        print("-----")
        print(humidityUrl)
        print(headers)
        print(humidityData)
        print("-----")
        
        exception = False

        #Push Temperature
        try:
            r = requests.post(temperatureUrl, data=temperatureData, headers=headers)
            results = r.json()
            print(results)
        except Exception as e:
            connectToWiFi(True)
            print("Unable to post temperature data")
            print(e)
            exception = True
        
        #Push Humidity
        try:
            r = requests.post(humidityUrl, data=humidityData, headers=headers)
            results = r.json()
            print(results)
        except Exception as e:
            connectToWiFi(True)
            print("Unable to post humidity data")
            print(e)
            exception = True
            
        if exception is False:
            concurrentExceptions = 0
            led_pin.value(1)
        else:
            concurrentExceptions += 1
            led_pin.value(0)
            
        #Check for unacceptable number of exceptions
        if concurrentExceptions == retry:
            raise Exception("Too many concurrent exceptions")
        
        #Sleep until the next reading
        utime.sleep(variables.readingInterval)
        
except Exception as fatal:
    
    #Just reset and start over
    machine.reset()
