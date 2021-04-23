# Imports
import picamera
import time

# Camera initialization
cam  = picamera.PiCamera()

# Camera go for launch confirmations and recording start
confirm = input("Confirm camera go for flight: ")
if confirm == 'GO':
  cam.start_recording('/home/pi/launch.h264')
  time.sleep(30)
  cam.stop_recording()
  
