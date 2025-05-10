from machine import Pin, WDT
import time
import sys

# Duration to keep feeding the watchdog (3 minutes = 180 seconds)
RUN_DURATION = 180

def detect_board_and_configure_led():
    platform = sys.platform
    if platform == "esp32":
        print("ESP32 detected")
        led_pin = Pin(14, Pin.OUT)  # LED on GPIO 14 for ESP32
    elif platform == "rp2":
        print("RP2040 detected")
        led_pin = Pin(3, Pin.OUT)  # LED on GPIO 3 for RP2040
    else:
        print("Unsupported board:", platform)
        led_pin = None
    return led_pin

def main():
    # Print program start message
    print("Program started")
    
    # Detect board and configure LED
    led = detect_board_and_configure_led()
    if led is None:
        print("Program terminated due to unsupported board")
        return
    
    # Initialize Watchdog Timer with a 5-second timeout
    wdt = WDT(timeout=5000)
    
    start_time = time.time()
    
    while True:
        # Check if 3 minutes have passed
        if time.time() - start_time < RUN_DURATION:
            # Feed the watchdog to prevent reset
            wdt.feed()
            # Toggle LED to show activity
            led.value(not led.value())
            # Print program status
            print(f"Program running, LED state: {led.value()}, Time elapsed: {time.time() - start_time:.1f}s")
            time.sleep(0.5)  # Blink every 0.5 seconds
        else:
            # Stop feeding the watchdog, let it reset the microcontroller
            led.value(0)  # Turn off LED
            print("Stopped feeding watchdog. Awaiting reset...")
            while True:
                # Infinite loop to prevent further watchdog feeding
                pass

# Run the main function
main()