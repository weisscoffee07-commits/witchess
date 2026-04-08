from machine import TouchPad, Pin,PWM
from MX1508 import *
from micropython import const
import uasyncio as asio
from BLEUART import *
from rc522_1 import RC522
from ntag_reader_1 import NTAGReader

debug=0
motor = MX1508(25, 26)
sp=1023
an=0
on=0
comand=''

#Инициализация RFID
rfid_hw = RC522(sck=18, mosi=23, miso=19, cs=5, rst=22)
reader = NTAGReader(rfid_hw)

#настройка сервопривода (ШИМ) на 33 пине
pwm = PWM(Pin(33,Pin.OUT))
pwm.freq(50)
pwm.duty(0)


        
def map(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)
def servo(pin, angle):
    pin.duty(map(angle, 0, 180, 20, 120))

#приём данных по bluetooth

def on_rx(): 
    global comand, on
    raw = uart.read()
    if raw: #чтобы избежать ошибки при пустом сообщении от Bluetooth
        on = 1
        comand = raw.decode()
        comand = comand[2:]
        
#Инициализация bluetooth
ble = bluetooth.BLE()
uart = BLEUART(ble)
uart.irq(handler=on_rx)

#Задача для чтения меток
async def rfid_scanner():
    global an
    while True:
        #Используем функцию read_with_authentication из ntag_reader
        success, uid, data = reader.read_with_authentication()
        
        if success and data:
            #Превращаем байты в текст
            label = "".join([chr(b) for b in data if 32 <= b <= 126])
            print("Найдена метка:", label)
            
            #Если на метке написано "GO", робот закроет клешни (тест)
            if "GO" in label:
                an = 180
                servo(pwm, an)
        
        await asio.sleep_ms(300) #проверка 3 раза в секунду, чтобы не грузить процессор
                
    
async def do_it(int_ms): #Асинхронный цикл управления
    global an, on, comand
    servo(pwm, an) #стартовая позиция
    
    while 1:
        await asio.sleep_ms(int_ms)
        #print(comand)
        if comand=='516':
            motor.forward(sp)
        if comand=='615':
            motor.reverse(sp)
        if (comand=='507')or(comand=='606'):
            motor.stop()
        if comand=='813' and on:
            an+=30
            on=0
            if an>180:
                an=180
            servo(pwm, an) #обновляем положение
        if comand=='714' and on:
            an-=30
            on=0
            if an<0:
                an=0
            servo(pwm, an)
            
# define loop
loop = asio.get_event_loop()

#create looped tasks
loop.create_task(do_it(5))
loop.create_task(rfid_scanner()) #Задача сканирования
# loop run forever
loop.run_forever()

#uart.close()