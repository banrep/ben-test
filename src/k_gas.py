#!/usr/bin/python3

import socket
if socket.gethostname() == "raspberrypi":
    import RPi.GPIO as GPIO
    
class Gas:
    debug=False
    
# Define GPIO number not board pin for Gas counters
    pin = 22
    count = 0

def interupt(chan):
    Gas.count += 5 # two pulses for a turn of the wheel
    if (Gas.debug):
        print("chan=",chan," count=",Gas.count)
    
def init():
    bounce=400
    reset()
    # Set pins for counter as input
    GPIO.setmode(GPIO.BCM)  #Set the GPIO pin naming mode to GPIO Name
    GPIO.setwarnings(False) #Supress warnings
    GPIO.setup(Gas.pin, GPIO.IN)
    cleanup()
    #see both up and down
    GPIO.add_event_detect(Gas.pin, GPIO.BOTH, callback=interupt, bouncetime=bounce)

def cleanup():
    GPIO.remove_event_detect(Gas.pin)

def reset():
        Gas.count = 0


def get():
    return(Gas.count)
    # devide by 2 as seeing up and down
    if ((Gas.count % 2) == 0): #Turn of the wheel is 10 points .01 cuM?
        return(Gas.count/2)
    else:
        return((Gas.count -1)/2)


# Testing
if __name__ == '__main__':
    init()
    Gas.debug=True
    while (True):
        print("count=",Gas.get())
        x=input("Again")
        
