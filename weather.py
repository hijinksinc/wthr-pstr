import requests, json, time, sys
from datetime import datetime
from pytz import timezone
from subprocess import call
from omega_gpio import OmegaGPIO
from some_functions import connected_to_internet, are_you_subscribed, clear_pins

#Making sure we're connected to the internet, otherwise we just loop and keep checking
online = connected_to_internet()

while online is False:
    print('not online')
    call(["logger", "-t", "weather", "Not online"])
    time.sleep(60)
    online = connected_to_internet()

print('We are online')
call(["logger", "-t", "weather", "we are online"])

#Are you subscribed
subscribed = are_you_subscribed()

while subscribed == 'unsubscribed':
    print('unsubscribed')
    call(["logger", "-t", "weather", "unsubscribed"])
    time.sleep(1800)
    subscribed = are_you_subscribed()

#handling creds
config = '/root/.config.txt'
creds = open(config,'r').read().split('\n')

max1 = creds[0]
max2 = creds[1] if len(creds) > 1 else ''

#Optional fixed location, set with lines like latitude=51.5, longitude=-0.12, timezone=Europe/London
settings = {}
for line in creds:
    if '=' in line:
        key, value = line.split('=', 1)
        settings[key.strip().lower()] = value.strip()


#Setting up Omega's pins
try:
    omega = OmegaGPIO()
    clear_pins()
    print('GPIO enabled')
    call(["logger", "-t", "weather", "GPIO enabled"])
           
except:
    print('failed to set up pins')
    call(["logger", "-t", "weather", "failed to set up pins"])
           
#handling creds, lines 1 and 2 are the maxmind account id and license key
config = '/root/.config.txt'

#Fixed location set on the poster's setup page, as lines like latitude=51.5, longitude=-0.12, timezone=Europe/London
#Returns None if it isn't set or is invalid
def fixed_location():
    try:
        settings = {}
        for line in open(config,'r').read().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                settings[key.strip().lower()] = value.strip()

        if 'latitude' not in settings and 'longitude' not in settings and 'timezone' not in settings:
            return None

        location = {
            'latitude': float(settings['latitude']),
            'longitude': float(settings['longitude']),
            'time_zone': settings['timezone'],
        }
        timezone(location['time_zone'])
        return location

    except:
        print('fixed location in config is incomplete or invalid')
        call(["logger", "-t", "weather", "fixed location in config is incomplete or invalid"])
        return None

#getting maxmind info for own IP address
def maxmind_location():
    creds = open(config,'r').read().split('\n')
    max1 = creds[0]
    max2 = creds[1] if len(creds) > 1 else ''
    r = requests.get('https://geoip.maxmind.com/geoip/v2.1/city/me', auth=(max1, max2), timeout=30)
    return r.json()['location']

#Picks up a location changed on the setup page, without needing a restart
def refresh_location():
    global location_info
    location = fixed_location()
    if location is not None and location != location_info:
        location_info = location
        print('location updated from config')
        call(["logger", "-t", "weather", "location updated from config"])

#using fixed location from config if set, otherwise maxmind. Waits until one works, e.g. for a new poster that hasn't been given a location yet
location_info = None
while location_info is None:
    location_info = fixed_location()
    if location_info is not None:
        print('using fixed location from config')
        call(["logger", "-t", "weather", "using fixed location from config"])
    else:
        try:
            location_info = maxmind_location()
            print('using maxmind location')
            call(["logger", "-t", "weather", "using maxmind location"])
        except:
            print('no location yet, set one on the setup page')
            call(["logger", "-t", "weather", "no location yet, set one on the setup page"])
            time.sleep(60)

#getting local time for the poster's location
def get_time():
    TZ = location_info['time_zone']
    #using timezone ID to get local time
    local = timezone(TZ)
    full_local_time = datetime.now(local)
    h_local_time = full_local_time.strftime('%H')
    m_local_time = full_local_time.strftime('%M')
    m_local_time = 1.66666*int(m_local_time)
    local_time = int(h_local_time) + 0.01*(int(m_local_time))
    return local_time

local_time = get_time()
print(local_time)
call(["logger", "-t", "weather", str(local_time)])

#getting weather info from Open-Meteo (free, no API key needed)
#WMO weather codes used by Open-Meteo, converted to readable conditions
WMO_CODES = {
    0: 'Clear sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
    45: 'Fog', 48: 'Rime fog',
    51: 'Light drizzle', 53: 'Drizzle', 55: 'Dense drizzle',
    56: 'Light freezing drizzle', 57: 'Freezing drizzle',
    61: 'Light rain', 63: 'Rain', 65: 'Heavy rain',
    66: 'Light freezing rain', 67: 'Freezing rain',
    71: 'Light snow', 73: 'Snow', 75: 'Heavy snow', 77: 'Snow grains',
    80: 'Light showers', 81: 'Showers', 82: 'Heavy showers',
    85: 'Light snow showers', 86: 'Snow showers',
    95: 'T-storms', 96: 'T-storms w/ hail', 99: 'T-storms w/ heavy hail',
}

#Returns today's hourly weather codes (past hours included) and the current temp in fahrenheit
def get_weather():
    params = {
        'latitude': location_info['latitude'],
        'longitude': location_info['longitude'],
        'hourly': 'weather_code',
        'current': 'temperature_2m',
        'temperature_unit': 'fahrenheit',
        'timezone': location_info['time_zone'],
        'forecast_days': 1,
    }
    res = requests.get('https://api.open-meteo.com/v1/forecast', params=params, timeout=30)
    res.raise_for_status()
    return res.json()

#Creating entries for every hour of the day
forecast = {f'{i}:00': '0' for i in range(24)}

#Setup is complete, now we go into the main loop
while 1 == 1:
    print('enter loop')
    call(["logger", "-t", "weather", "enter loop"])
    #Loops between 4am and 11pm
    while local_time >= 4 and local_time <= 23:
        print('in second loop')
        call(["logger", "-t", "weather", "in second loop"])
        
        refresh_location()

        #Get today's hourly weather (past and future hours) from Open-Meteo
        try:
            weatherdata = get_weather()
            hourly = weatherdata['hourly']

            #Fills forecast with hour:weather cond, keys like '8:00' and '16:00'
            for H, code in zip(hourly['time'], hourly['weather_code']):
                h = str(int(H[11:13])) + ':00'
                forecast[h] = WMO_CODES.get(code, 'Unknown')

            #temp in fahrenheit
            temp = int(weatherdata['current']['temperature_2m'])
            print(temp)

        except:
            print('open-meteo error')
            call(["logger", "-t", "weather", "open-meteo error"])

        print(forecast)
        call(["logger", "-t", "weather", str(forecast)])

        #######GPIO_Allocation#######

        #Turning on correct pins/icons
        pin_timer = 0
        try:
            clear_pins()
        except:
            print('fail clear_pins')
            
        #Class conversions
        Rain = ['Light drizzle', 'Drizzle', 'Dense drizzle', 'Light freezing drizzle', 'Freezing drizzle', 'Light rain', 'Rain', 'Heavy rain', 'Light freezing rain', 'Freezing rain', 'Light snow', 'Snow', 'Heavy snow', 'Snow grains', 'Light showers', 'Showers', 'Heavy showers', 'Light snow showers', 'Snow showers', 'T-storms', 'T-storms w/ hail', 'T-storms w/ heavy hail']
        Cloud = ['Partly cloudy', 'Overcast', 'Fog', 'Rime fog']
        Sun = ['Clear sky', 'Mainly clear']
        #Cycle lasts 60mins
        while pin_timer <= 3599:
                print(pin_timer)
                call(["logger", "-t", "weather", str(pin_timer)])
                try:
                    
                    #8am
                    if forecast['8:00'] in Rain:                        
                        omega.pin_on(2)
                        print('8R')
                        call(["logger", "-t", "weather", "8R"])

                    if forecast['8:00'] in Cloud:
                        omega.pin_on(17)
                        print('8C')
                        call(["logger", "-t", "weather", "8C"])

                    if forecast['8:00'] in Sun:
                        omega.pin_on(16)
                        print('8S')
                        call(["logger", "-t", "weather", "8S"])

                    #12pm
                    if forecast['12:00'] in Rain: 
                        omega.pin_on(15)
                        print('12R')
                        call(["logger", "-t", "weather", "12R"])

                    if forecast['12:00'] in Cloud: 
                        omega.pin_on(46)
                        print('12C')
                        call(["logger", "-t", "weather", "12C"])

                    if forecast['12:00'] in Sun:
                        omega.pin_on(13)
                        print('12S')
                        call(["logger", "-t", "weather", "12S"])

                    #4pm
                    if forecast['16:00'] in Rain:
                        omega.pin_on(19)
                        print('16R')
                        call(["logger", "-t", "weather", "16R"])

                    if forecast['16:00'] in Cloud:
                        omega.pin_on(4)
                        print('16C')
                        call(["logger", "-t", "weather", "16C"])

                    if forecast['16:00'] in Sun:
                        omega.pin_on(5)
                        print('16S')
                        call(["logger", "-t", "weather", "16S"])

                    #8pm
                    if forecast['20:00'] in Rain:
                        omega.pin_on(18)
                        print('20R')
                        call(["logger", "-t", "weather", "20R"])

                    if forecast['20:00'] in Cloud:
                        omega.pin_on(3)
                        print('20C')
                        call(["logger", "-t", "weather", "20C"])

                    if forecast['20:00'] in Sun:
                        omega.pin_on(0)
                        print('20S')
                        call(["logger", "-t", "weather", "20S"])

                    if pin_timer <= 299:
                        #less sleep while pins are on
                        time.sleep(300)
                        pin_timer = pin_timer + 300
                    else:
                        #Pulse - 3mins on
                        time.sleep(180)
                        pin_timer = pin_timer + 180
                        call(["logger", "-t", "weather", "just 3 mins on before 1 min off"])
                        print("just 3 mins on before 1 min off")

                    #Pulse - 1min off
                    #If temp 18c or lower, then pulse for less
                    if temp <= 64:
                        clear_pins()
                        time.sleep(20)
                        pin_timer = pin_timer + 20
                        print('cold, so small pulse')
                    else:
                        clear_pins()
                        time.sleep(120)
                        pin_timer = pin_timer + 120
                        call(["logger", "-t", "weather", "just pulsed for 1min, outside temp above 12c"])
                    
                # If there's problems turning on pins, we wait before re-trying.    
                except:
                    pin_timer = pin_timer + 120
                    time.sleep(120)

                
        else:
            print('pins turning off and resetting pin_timer')
            call(["logger", "-t", "weather", "pins turning off and resetting pin_timer"])
            pin_timer = 0
            try:
                local_time = get_time()
            except:
                print('failed to get time')

            #turning off pins for break, how long dictated by outside temp (v.rough proxy to room temp)
            try:
                #If temp 18c or lower then sleep for shorter
                if temp <= 64:
                    call(["logger", "-t", "weather", "60mins up, cold, so only 1min break"])
                    time.sleep(120)
                    clear_pins()
                    time.sleep(60)
                else:
                    call(["logger", "-t", "weather", "60mins up, warm, time for a 3min break"])
                    clear_pins()
                    time.sleep(180)
                    
            except:
                    print('60mins up, time for a 3min break')
                    time.sleep(180)



        #Updates local_time
        try:
            local_time = get_time()
            print("time is "+(str(local_time)))
            call(["logger", "-t", "weather", str(local_time)])
        except:
            print('fail')

    else:
        try:
            #sleeps and updates local_time
            print('sleep_mode')
            call(["logger", "-t", "weather", "sleep_mode"])
            print("time is "+(str(local_time)))
            call(["logger", "-t", "weather", str(local_time)])
        except:
            print('fail 1')
            
        time.sleep(1800)
        
        #turning pins off for sleep mode
        try:
            clear_pins()
        except:
            print('')

        refresh_location()
        local_time = get_time()
        
