from machine import Pin, I2C
import time
import sys
from ssd1306 import SSD1306_I2C
import gc

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
    if platform == "esp32":
        try:
            i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
            return i2c
        except Exception as e:
            print("I2C initialization failed:", e)
    elif platform == "rp2":
        try:
            i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100_000)
            return i2c
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
                out_pin.value(test_value)
                time.sleep(0.01)
                read_value = in_pin.value()
                result = "OK" if read_value == test_value else "FAIL"
                if result == "FAIL":
                    all_ok = False
                msg = "{}:{}>{} {}".format(test_title, test_value, read_value, result)
                print(msg)
                lines.append(msg)
                if oled:
                    oled_print_lines(oled, lines)
            out_pin.value(0)
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
    i2c = detect_board_and_configure_i2c()
    devices = i2c.scan()
    if devices:
        print("Found I2C devices at:", [hex(d) for d in devices])
    else:
        print("No I2C devices found")
    time.sleep(2)
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

    pin_list = detect_board_and_configure_pins()
    if pin_list:
        oled.fill(0)
        oled.text("Test GPIO...", 0, 0)
        oled.show()
        test_gpio_bidirectional(pin_list, oled)
        time.sleep(2)
    else:
        oled.fill(0)
        oled.text("No GPIO test", 0, 0)
        oled.show()
        time.sleep(2)

    # start_time = time.time()
    # while True:
    #     elapsed = time.time() - start_time
    #     ram_usage = gc.mem_alloc() / (gc.mem_alloc() + gc.mem_free()) * 100
    #     oled.fill(0)
    #     oled.text("Time: %.1fs" % elapsed, 0, 0)
    #     oled.text("RAM: %.1f%%" % ram_usage, 0, 10)
    #     oled.show()
    #     print("Elapsed time: %.1fs, RAM usage: %.1f%%" % (elapsed, ram_usage))
    #     time.sleep(0.5)

main()
