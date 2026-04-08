"""
RC522 RFID Reader класс для MicroPython
Поддержка ключей для чтения защищенных NTAG213 меток
"""

from machine import Pin, SoftSPI
import time

class RC522:
    OK = 0
    NOTAGERR = 1
    ERR = 2
    REQIDL = 0x26

    # Регистры
    CommandReg = 0x01
    ComIEnReg = 0x02
    ComIrqReg = 0x04
    ErrorReg = 0x06
    Status2Reg = 0x08
    FIFODataReg = 0x09
    FIFOLevelReg = 0x0A
    ControlReg = 0x0C
    BitFramingReg = 0x0D
    ModeReg = 0x11
    TxControlReg = 0x14
    TxAutoReg = 0x15
    TModeReg = 0x2A
    TPrescalerReg = 0x2B
    TReloadRegH = 0x2C
    TReloadRegL = 0x2D

    # Команды
    CMD_IDLE = 0x00
    CMD_TRANSCEIVE = 0x0C
    CMD_SOFT_RESET = 0x0F

    def __init__(self, sck=18, mosi=23, miso=19, cs=5, rst=22):
        self.spi = SoftSPI(baudrate=100000, polarity=0, phase=0, sck=Pin(sck), mosi=Pin(mosi), miso=Pin(miso))
        self.cs = Pin(cs, Pin.OUT)
        self.rst = Pin(rst, Pin.OUT)
        self.cs.value(1)
        self.reset()
        self.init()

    def reset(self):
        self.rst.value(0)
        time.sleep_ms(50)
        self.rst.value(1)
        self.write_register(self.CommandReg, self.CMD_SOFT_RESET)
        time.sleep_ms(50)

    def write_register(self, addr, val):
        self.cs.value(0)
        self.spi.write(bytes([((addr << 1) & 0x7E), val]))
        self.cs.value(1)

    def read_register(self, addr):
        self.cs.value(0)
        self.spi.write(bytes([((addr << 1) & 0x7E) | 0x80]))
        data = self.spi.read(1)
        self.cs.value(1)
        return data[0]

    def set_bitmask(self, reg, mask):
        self.write_register(reg, self.read_register(reg) | mask)

    def clear_bitmask(self, reg, mask):
        self.write_register(reg, self.read_register(reg) & (~mask))

    def init(self):
        self.write_register(self.TModeReg, 0x8D)
        self.write_register(self.TPrescalerReg, 0x3E)
        self.write_register(self.TReloadRegL, 30)
        self.write_register(self.TReloadRegH, 0)
        self.write_register(self.TxAutoReg, 0x40)
        self.write_register(self.ModeReg, 0x3D)
        self.antenna_on()

    def antenna_on(self):
        if not (self.read_register(self.TxControlReg) & 0x03):
            self.set_bitmask(self.TxControlReg, 0x03)

    def to_card(self, command, send_data):
        back_data = []
        status = self.ERR
        self.write_register(self.ComIEnReg, 0x80 | 0x77)
        self.clear_bitmask(self.ComIrqReg, 0x80)
        self.set_bitmask(self.FIFOLevelReg, 0x80)
        self.write_register(self.CommandReg, self.CMD_IDLE)
        for byte in send_data: self.write_register(self.FIFODataReg, byte)
        self.write_register(self.CommandReg, command)
        self.set_bitmask(self.BitFramingReg, 0x80)
        i = 100
        while i > 0:
            n = self.read_register(self.ComIrqReg)
            i -= 1
            if (n & 0x01) or (n & 0x30): break
            time.sleep_ms(1)
        self.clear_bitmask(self.BitFramingReg, 0x80)
        if i != 0 and (self.read_register(self.ErrorReg) & 0x1B) == 0x00:
            status = self.OK
            n = self.read_register(self.FIFOLevelReg)
            for _ in range(n): back_data.append(self.read_register(self.FIFODataReg))
        return status, back_data

    def read_uid(self):
        self.write_register(self.BitFramingReg, 0x07)
        status, _ = self.to_card(self.CMD_TRANSCEIVE, [self.REQIDL])
        if status != self.OK: return None
        self.write_register(self.BitFramingReg, 0x00)
        status, back_data = self.to_card(self.CMD_TRANSCEIVE, [0x93, 0x20])
        return back_data[:4] if status == self.OK else None

    def read_ntag_page(self, page_addr):
        """Читает 4-байтную страницу NTAG"""
        status, data = self.to_card(self.CMD_TRANSCEIVE, [0x30, page_addr])
        return data[:4] if status == self.OK else None