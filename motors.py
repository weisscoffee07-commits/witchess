from machine import TouchPad, Pin,PWM,I2C,
from MX1508 import *
from tcs34725 import *
from time import sleep
from neopixel import NeoPixel
i2c_bus = I2C(0, sda=Pin(17), scl=Pin(16))
tcs = TCS34725(i2c_bus)
tcs.gain(4)#gain must be 1, 4, 16 or 60
tcs.integration_time(80)
debug=0
NUM_OF_LED = 1
np = NeoPixel(Pin(32), NUM_OF_LED)
color=['Cyan','Black','Yellow','Navy','Orange','Green','Red']
touch_pin1 = TouchPad(Pin(13, mode=Pin.IN))
touch_pin2 = TouchPad(Pin(12, mode=Pin.IN))
touch_pin3 = TouchPad(Pin(14, mode=Pin.IN))
touch_pin4 = TouchPad(Pin(27, mode=Pin.IN))
motor = MX1508(25, 26)
sp=150
an=0 
pwm = PWM(Pin(33,Pin.OUT))
pwm.freq(50)
pwm.duty(0)
def map(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)
def servo(pin, angle):
    pin.duty(map(angle, 0, 180, 20, 120))
def color_det():
    rgb=tcs.read(1)
    r,g,b=rgb[0],rgb[1],rgb[2]
    h,s,v=rgb_to_hsv(r,g,b)
    col_id=0
    if (h>340)or(h<10):
        col_id=6
        np[0] = (255,0,0)
    if 10<h<60:
        col_id=4
        np[0] = (255,128,0)
    if 60<h<120:
        col_id=2
        np[0] = (255,255,51)
    if 120<h<180:
        col_id=5
        np[0] = (0,255,0)
    if 180<h<240:
        if v>150:
            col_id=0
            np[0] = (51,255,255)
        if 95<v<150:
            col_id=3
            np[0] = (0,0,153)
        if v<95:
            col_id=1
            np[0] = (0,0,0)
    np.write()
    if debug:
        print('Color is {}. R:{} G:{} B:{} H:{:.0f} S:{:.0f} V:{:.0f}'.format(color[col_id],r,g,b,h,s,v))
        
while True:  
    touch_value1 = touch_pin1.read()
    touch_value2 = touch_pin2.read()
    touch_value3 = touch_pin3.read()
    touch_value4 = touch_pin4.read()
    if touch_value1<300:
        sp+=5
        sleep(0.01)
        if sp>1023:
            sp=1023
        motor.forward(sp)
        #print('sp=',sp)
    if touch_value2<300:
        sp-=5
        if sp<150:
            sp=150
        sleep(0.01)
        #print('sp=',sp)
        motor.reverse(sp)
    if touch_value3<300:
        an+=1
        if an>180:
            an=180
        sleep(0.01)
        #print('an=',an)
        
    if touch_value4<300:
        an-=1
        if an<0:
            an=0
        sleep(0.01)
        #print('an=',an)    
    servo(pwm, an)
    color_det()
     