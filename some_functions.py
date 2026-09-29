import requests, time
from omega_gpio import OmegaGPIO


def connected_to_internet(url='http://www.google.com/', timeout=5):
    try:
        _ = requests.get(url, timeout=timeout)
        #print("we're online")
        return True
    except requests.ConnectionError:
        #print("No internet connection available.")
        return False
    

def are_you_subscribed():
    #import macID.txt and turn into an obj
    macID_txt = '/root/macID.txt'
    macIDlist = open(macID_txt,'r').read().split('\n')
    macID = macIDlist[0]
    #import unsub list and turn into a list
    unsub_txt = '/root/wthr-pstr/unsubscribed.txt'
    unsub = open(unsub_txt,'r').read().split('\n')
    if macID in unsub:
        return 'unsubscribed'
    else:
        return 'subscribed'
    

def clear_pins():
    try:
        omega = OmegaGPIO()
        
        omega.pin_off(2)
        omega.pin_off(17)
        omega.pin_off(16)

        omega.pin_off(15)
        omega.pin_off(46)
        omega.pin_off(13) 

        omega.pin_off(3)
        omega.pin_off(0)
        omega.pin_off(18)
        omega.pin_off(1)
        omega.pin_off(12)
        
        omega.pin_off(19)
        omega.pin_off(4)
        omega.pin_off(5)
        
    except:
        print('pin problems')

