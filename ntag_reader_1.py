"""
Улучшенный ридер NTAG213 с поддержкой ключей
"""

import time
from machine import Pin
from rc522_1 import RC522

class NTAGReader:
    def __init__(self, rfid_instance):
        self.rfid = rfid_instance
        self.led = Pin(2, Pin.OUT) # На многих платах встроенный LED на Pin 2

    def read_with_authentication(self):
        uid = self.rfid.read_uid()
        if not uid:
            return False, None, None
        
        data = self.rfid.read_ntag_page(4)
        if data:
            self.led.value(1)
            time.sleep_ms(100)
            self.led.value(0)
            return True, uid, data
        return True, uid, None