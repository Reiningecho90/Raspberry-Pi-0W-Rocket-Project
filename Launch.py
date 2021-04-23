# Imports
from datetime import datetime
import smbus
import math
import time
import sys
import pandas as pd
import RPi.GPIO as GPIO


# GPIO initialization 
GPIO.setmode(GPIO.BOARD)
GPIO.setup(18, GPIO.OUT)
pwm = GPIO.PWM(18, 100)
pwm.start(0)


# Register
power_mgmt_1 = 0x6b
power_mgmt_2 = 0x6c

def save_to_file():
    angles =  (int(read_word_2c(0x3b)) / 131,
               int(read_word_2c(0x3d)) / 131,)

    file = open('MPUData.csv', 'a')
    for i in angles:
        file.write(str(angles[0]) + ', ' + str(angles[1]) + '\n')

def read_byte(reg):
    return bus.read_byte_data(address, reg)

def read_word(reg):
    h = bus.read_byte_data(address, reg)
    l = bus.read_byte_data(address, reg+1)
    value = (h << 8) + l
    return value

def read_word_2c(reg):
    val = read_word(reg)
    if (val >= 0x8000):
        return -((65535 - val) + 1)
    else:
        return val

def dist(a,b):
    return math.sqrt((a*a)+(b*b))

def get_y_rotation(x,y,z):
    radians = math.atan2(x, dist(y,z))

def get_x_rotation(x,y,z):
    radians = math.atan2(y, dist(x,z))
    return math.degrees(radians)

bus = smbus.SMBus(1)
address = 0x68

bus.write_byte_data(address, power_mgmt_1, 0)

# Misc value definitions
count = 0
status = True


# Main launch loop
while status:

    deploy = False
    spike = False
    spike_t = 0
    dep_time = 0

    #deployment auto-sequence
    if count == 168:
        GPIO.output(18, True)
        pwm.ChangeDutyCycle(5)
        time.sleep(1)
        pwm.ChangeDutyCycle(0)
        GPIO.output(18, False)
        dep_time = str(datetime.now())

    a_x = read_word_2c(0x3b)
    a_y = read_word_2c(0x3d)
    a_z = read_word_2c(0x3f)


    # Data to screen output
    print ("\033c")

    print ("Accel")
    print ("------")

    print ("\n")
    sys.stdout.write(f"Scaled X: {a_x / 16348}")
    if a_x / 16348 > 1.2:
        spike = True
        spike_t = str(datetime.now())
    sys.stdout.flush()

    print ("\n")
    sys.stdout.write(f"Scaled Y: {a_y / 16348}")
    if a_y / 16348 > 1.2:
        spike = True
        spike_t = str(datetime.now())
    sys.stdout.flush()

    print ("\n")
    sys.stdout.write(f"Scaled Z: {a_z / 16348}")
    if a_z /16348 > 1.2:
        spike = True
        spike_t = str(datetime.now())
    sys.stdout.flush()

    fail = False

    # Data-spike output/failsafe
    if spike_t != dep_time:
        fail = True
        deploy = False
    elif spike_t == dep_time and count > 50:
        print ("\n")
        sys.stdout.write("MPU6050 Data Read: MPU HAS CONFIRMATION OF NOMINAL PARACHUTE DEPLOY")
        sys.stdout.flush()
        deploy = True

    print ("\n")

    print (count)

    if not deploy and fail:
        sys.stdout.write("MPU6050 Data Read: CURRENT MPU DATA HAS SHOWN THAT PARAHUTE DEPLOY SEQUENCE MAY HAVE BEEN ANOMINAL!")
        sys.stdout.flush()

    save_to_file()

    time.sleep(0.1)

    count = count+1

    # TD confirmation
    if not spike and count > 168:
        continue
    elif spike and count > 168:
        sys.stdout.write("\n")
        sys.stdout.flush()
        sys.stdout.write("\n")
        sys.stdout.flush()
        sys.stdout.write("Tango Delta, touchdown confirmed.")
        sys.stdout.flush()
        sys.stdout.write("\n")
        sys.stdout.flush()
        sys.stdout.write("Switching to ground control systems and preparing for data review.")
        sys.stdout.flush()
        status = False
    elif spike and count > 300:
        sys.stdout.write("Tango Delta anominal, touchdown timing failure.")
        sys.stdout.flush()
        status = False
    else:
        continue

status = True

time.sleep(5)

# Data review and shutdown
while status:
    print ("\n")
    print ("Preparing data review systems, stand by for post-flight review.")
    data_read = pd.read_csv('MPUData.csv', sep=', ', header=None, engine='python')
    time.sleep(10)
    for value in data_read:
        if abs(value) > 5:
            sys.stdout.write("\n")
            sys.stdout.flush()
            sys.stdiut.write("\n")
            sys.stdout.flush()
            sys.stdout.write(f"Anamoly found, G-Force value exceded nominal forces, force was equal to: {value} at point of anamoly, note that anomaly may have occured at parachute deploy but G limit still applies for deploy.")
            sys.stdout.flush()
        else:
            sys.stdout.write("\n")
            sys.stdout.flush()
            sys.stdout.write("No anamolies found, craft safe on the ground, proceeding to post-flight calibration.")
            sys.stdout.flush()
            GPIO.output(18, True)
            pwm.ChangeDutyCycle(0)
            sys.stdout.write("Post flight calibration done, exiting program...")
            sys.stdout.flush()
            status = False
