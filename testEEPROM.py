import sys
from machine import I2C, Pin
import time

class EEPROM:
    def __init__(self, i2c, address, size, page_size, block_bits):
        self.i2c = i2c
        self.base_addr = address
        self.size = size
        self.page_size = page_size
        self.block_bits = block_bits

    def get_device_addr(self, addr):
        block = (addr >> 8) & ((1 << self.block_bits) - 1)
        return self.base_addr | block

    def write_byte(self, addr, data):
        if addr < 0 or addr >= self.size:
            return False
        try:
            device_addr = self.get_device_addr(addr)
            offset = addr & 0xFF
            print(f"[WRITE] DevAddr: {hex(device_addr)}, Offset: {hex(offset)}, Data: {hex(data)}")
            self.i2c.writeto_mem(device_addr, offset, bytes([data]))
            time.sleep_ms(5)
            return True
        except Exception as e:
            print("Write error at address " + hex(addr) + ": " + str(e))
            return False

    def read_byte(self, addr):
        if addr < 0 or addr >= self.size:
            return None
        try:
            device_addr = self.get_device_addr(addr)
            offset = addr & 0xFF
            print(f"[READ] DevAddr: {hex(device_addr)}, Offset: {hex(offset)})")
            return self.i2c.readfrom_mem(device_addr, offset, 1)[0]
        except Exception as e:
            print("Read error at address " + hex(addr) + ": " + str(e))
            return None

    def write_array(self, start, data):
        try:
            for i in range(0, len(data), self.page_size):
                chunk = data[i:i + self.page_size]
                for j, b in enumerate(chunk):
                    self.write_byte(start + i + j, b)
            return True
        except Exception as e:
            print("Write array error at address " + str(start) + ": " + str(e))
            return False

    def read_array(self, start, length):
        try:
            return bytes([self.read_byte(start + i) for i in range(length)])
        except Exception as e:
            print("Read array error at address " + str(start) + ": " + str(e))
            return None

    def test(self):
        print(f"\n--- Testing {self.__class__.__name__} ---")
        max_addr = self.size - 1
        print(f"\nTesting highest valid address: {hex(max_addr)}")
        if self.write_byte(max_addr, 0xAA):
            print("Write to max address succeeded.")
            val = self.read_byte(max_addr)
            if val == 0xAA:
                print("Read matches written value: 0xAA")
            else:
                print("Mismatch: read " + str(val))
        else:
            print("Write to max address failed.")

        test_len = 100 if self.size < 2048 else 200
        start = self.size // 2
        test_data = bytes([i % 256 for i in range(test_len)])

        print(f"\nTesting write/read of {test_len} bytes at address {hex(start)}")
        t0 = time.ticks_ms()
        if self.write_array(start, test_data):
            result = self.read_array(start, test_len)
            if result == test_data:
                print("Data matches. Test passed.")
            else:
                print("Data mismatch.")
        else:
            print("Write failed.")
        t1 = time.ticks_ms()
        print("Test duration: " + str(time.ticks_diff(t1, t0)) + " ms")

# EEPROM subclasses
class M24C08(EEPROM):
    def __init__(self, i2c):
        super().__init__(i2c, address=0x54, size=1024, page_size=16, block_bits=3)

class AT24C08(EEPROM):
    def __init__(self, i2c):
        super().__init__(i2c, address=0x50, size=1024, page_size=16, block_bits=3)

class M24C64(EEPROM):
    def __init__(self, i2c):
        super().__init__(i2c, address=0x50, size=8192, page_size=32, block_bits=0)

class AT24C64(EEPROM):
    def __init__(self, i2c):
        super().__init__(i2c, address=0x50, size=8192, page_size=32, block_bits=0)

def check_board():
    platform = sys.platform
    if platform == "esp32":
        print("ESP32 board detected.")
        print("Select ESP32 board type:")
        print("1. NANO (SDA=11, SCL=12, freq=400kHz)")
        print("2. NON_NANO (SDA=4, SCL=5, freq=400kHz)")
        while True:
            choice = input("Enter a number (1-2): ").strip()
            if choice == "1":
                return I2C(0, sda=Pin(11), scl=Pin(12), freq=400000)
            elif choice == "2":
                return I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
            else:
                print("Invalid choice. Try again.")
    elif platform == "rp2":
        print("RP2040 board detected.")
        return I2C(0, sda=Pin(20), scl=Pin(21), freq=400000)
    else:
        print("Unsupported platform: " + platform)
        sys.exit(1)

def scan_i2c(i2c):
    print("Scanning I2C bus for devices...")
    devices = i2c.scan()
    if devices:
        for device in devices:
            print(" - Address: " + hex(device))
    else:
        print("No I2C devices found.")

def select_eeprom(i2c):
    print("\nSelect EEPROM to test:")
    print("1. M24C08-RMN6TP")
    print("2. AT24C08C-SSHM-T")
    print("3. M24C64-WMN6TP")
    print("4. AT24C64D-SSHM-T")
    while True:
        choice = input("Enter a number (1-4): ").strip()
        if choice == "1":
            return M24C08(i2c)
        elif choice == "2":
            return AT24C08(i2c)
        elif choice == "3":
            return M24C64(i2c)
        elif choice == "4":
            return AT24C64(i2c)
        else:
            print("Invalid choice. Try again.")

# ---- MAIN ----
i2c = check_board()
scan_i2c(i2c)
eeprom = select_eeprom(i2c)
eeprom.test()
