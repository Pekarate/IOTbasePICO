from machine import Pin, I2C
import time
import sys
from ssd1306 import SSD1306_I2C
import gc
import tca9534

RELAY0=0
RELAY1=1
RELAY2=2
RELAY3=3

RELAY_ON = 0
RELAY_OFF = 1

bitmask = "0x00"  # Default bitmask for all pins
tca9534_mask = int(bitmask, 16)

def detect_board_and_configure_pins():
    platform = sys.platform
    pin_names = ["AP0", "AP1", "AP2", "AP3", "AP4", "AP5", "AP6", "AP7"]

    if platform == "esp32":
        pin_numbers = [35, 36, 37, 38, 39, 40, 1, 2]
    elif platform == "rp2":
        pin_numbers = [10, 11, 12, 13, 14, 15, 18, 19]
    else:
        return None

    return [{"name": name, "pin_number": num} for name, num in zip(pin_names, pin_numbers)]

def detect_board_and_configure_i2c():
    platform = sys.platform
    global tca9534_mask
    if platform == "esp32":
        try:
            i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100000)
            dev = tca9534.TCA9534(tca9534_address=0x3f,scl=Pin(5), sda=Pin(4), bitmask=tca9534_mask)  # ESP32-
            # dev = None  # Placeholder for TCA9534 initialization
            return i2c, dev
        except Exception as e:
            print("I2C initialization failed:", e)
    elif platform == "rp2":
        try:
            i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100_000)
            dev = tca9534.TCA9534(tca9534_address=0x20,scl=Pin(5), sda=Pin(4), bitmask=tca9534_mask)  # ESP32-S3

            return i2c,dev
        except Exception as e:
            print("I2C initialization failed:", e)
    else:
        return None

def oled_print_lines(oled, lines, delay=1):
    oled.fill(0)
    for i, line in enumerate(lines[-3:]):  # Hiển thị tối đa 3 dòng cuối
        oled.text(line, 0, i*10)
    oled.show()
    time.sleep(delay)

def test_gpio_bidirectional(pin_list, oled=None):
    pin_pairs = [(0, 4), (1, 5), (2, 6), (3, 7)]
    lines = []
    all_ok = True
    for idx1, idx2 in pin_pairs:
        pin1_info = pin_list[idx1]
        pin2_info = pin_list[idx2]
        for direction in [(pin1_info, pin2_info), (pin2_info, pin1_info)]:
            out_info = direction[0]
            in_info  = direction[1]
            out_pin = Pin(out_info["pin_number"], Pin.OUT)
            in_pin = Pin(in_info["pin_number"], Pin.IN)
            test_title = "{}->{}".format(out_info['name'], in_info['name'])
            for test_value in [0, 1]:
                out_pin.tca9534_mask(test_value)
                time.sleep(0.01)
                read_value = in_pin.tca9534_mask()
                result = "OK" if read_value == test_value else "FAIL"
                if result == "FAIL":
                    all_ok = False
                msg = "{}:{}>{} {}".format(test_title, test_value, read_value, result)
                print(msg)
                lines.append(msg)
                if oled:
                    oled_print_lines(oled, lines)
            out_pin.tca9534_mask(0)
    final_msg = "HOSTP12 OK!" if all_ok else "HOST P12 FAIL!"
    print(final_msg)
    if oled:
        oled_print_lines(oled, [final_msg])
    print("GPIO Test Done!")

def test_oled_display(oled):
    oled.fill(0)
    oled.text("Test OLED", 0, 0)
    oled.text("Top Left", 0, 10)
    oled.text("Bottom", 0, 20)
    oled.text("Right", 80, 10)
    oled.show()
    time.sleep(2)
    oled.fill(0)
    oled.hline(0, 16, 128, 1)
    oled.vline(64, 0, 32, 1)
    oled.rect(10, 5, 30, 20, 1)
    oled.fill_rect(90, 5, 30, 20, 1)
    oled.show()
    time.sleep(2)
    oled.fill(0)
    oled.text("Inverted", 0, 0)
    try:
        oled.invert(1)
        oled.show()
        time.sleep(1)
        oled.invert(0)
        oled.show()
        time.sleep(1)
    except:
        pass
    oled.fill(0)
    oled.show()

def main():
    print("Program started")
    i2c,tca = detect_board_and_configure_i2c()
    devices = i2c.scan()
    if devices:
        print("Found I2C devices at:", [hex(d) for d in devices])
    else:
        print("No I2C devices found")

    tca.write_pin(RELAY0, RELAY_OFF)
    tca.write_pin(RELAY1, RELAY_OFF)
    tca.write_pin(RELAY2, RELAY_OFF)
    tca.write_pin(RELAY3, RELAY_OFF)
    if i2c is None:
        print("I2C not available")
        return
    try:
        oled = SSD1306_I2C(128, 32, i2c)
        oled.fill(0)
        oled.text("Program Started", 0, 0)
        oled.show()
        test_oled_display(oled)
    except Exception as e:
        print("OLED init failed:", e)
        return

    for i in range(10):  # Lặp 10 lần, bạn có thể thay đổi số lần lặp nếu muốn
        for relay_num in [RELAY0, RELAY1, RELAY2, RELAY3]:
            tca.write_pin(relay_num, RELAY_ON)
            oled.fill(0)
            oled.text(f"Relay {relay_num+1} ON", 0, 0)
            oled.show()
            time.sleep(2)
            tca.write_pin(relay_num, RELAY_OFF)
            oled.fill(0)
            oled.text(f"Relay {relay_num+1} OFF", 0, 0)
            oled.show()
            time.sleep(2)
main()
