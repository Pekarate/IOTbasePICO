import sys
from machine import Pin, UART
import time

selected_port_test = None
selected_rs485_port = None

# Modify the configure_uart function
def configure_uart(baudrate):
    global selected_port_test, selected_rs485_port
    platform = sys.platform

    if platform == "esp32":
        # Only ask for selection if it hasn't been done before
        if selected_port_test is None and selected_rs485_port is None:
            print("ESP32 detected")
            print("Select ESP32 board type:")
            print("1. NANO (TX1=1(INT PIN)/RX1=5(PWM), TX2=7/RX2=8)")
            print("2. NON_NANO (TX1=11(TX)/RX1=12(RX PIN), TX2=33/RX2=34)")
            while True:
                choice = input("Enter a number (1-2): ").strip()
                if choice == "1":
                    selected_port_test = (1, 5)  # Store pin numbers
                    selected_rs485_port = (7, 8)
                    break
                elif choice == "2":
                    selected_port_test = (11, 12)
                    selected_rs485_port = (33, 34)
                    break
                else:
                    print("Invalid choice. Try again.")
        
        # Use the stored pin configurations
        port_test = UART(1, baudrate=baudrate, tx=Pin(selected_port_test[0]), 
                        rx=Pin(selected_port_test[1]), rxbuf=1024, timeout=500)
        rs485_port = UART(2, baudrate=baudrate, tx=Pin(selected_rs485_port[0]), 
                         rx=Pin(selected_rs485_port[1]), rxbuf=1024, timeout=500)

    elif platform == "rp2":
        print("RP2040 detected")
        port_test = UART(0, baudrate=baudrate, tx=Pin(0), rx=Pin(1), rxbuf=1024, timeout=500)
        rs485_port = UART(1, baudrate=baudrate, tx=Pin(8), rx=Pin(9), rxbuf=1024, timeout=500)
    else:
        print("Unsupported board:", platform)
        return None, None

    return port_test, rs485_port


def send_data(uart, message):
    # Encode message to bytes
    message_bytes = message.encode('utf-8')
    # print(f"Sending data from {uart} (TX):", message.strip())
    uart.write(message_bytes)
    # time.sleep(0.2)  # Increase sleep to ensure proper transmission

def receive_data(uart, expected_message):
    if uart.any():
        received = uart.read()
        if received:
            try:
                received_str = received.decode('utf-8')
                if received_str.strip() == expected_message.strip():
                    print(f"UART transmission successful")
                else:
                    print(f"Data mismatch in transmission")
            except UnicodeError:
                print(f"UnicodeError: Received data is not valid UTF-8: {received}")
        else:
            print(f"No data received on {uart}")
    else:
        print(f"No data available on {uart}")

def test_uart_transmission():
    baudrates = [9600, 14400, 19200, 38400, 57600, 115200, 230400, 460800, 921600, 2000000]

    pass_count = 0
    fail_count = 0

    for baudrate in baudrates:
        print(f"\nTesting with baudrate: {baudrate}")
        port_test, rs485_port = configure_uart(baudrate)
        if not port_test or not rs485_port:
            continue

        # Test port_test TX to rs485_port RX
        message = "Hello from port_test\n"
        # Clear RX buffer of rs485_port
        while rs485_port.any():
            rs485_port.read()
        send_data(port_test, message)
        received = rs485_port.readline()  # Use readline to read until newline
        if received:
            print(f"Length of received data: {len(received)}")
            try:
                received_str = received.decode('utf-8')
                if received_str.strip() == message.strip():
                    print("rs485_port: PASS - Data matches")
                    pass_count += 1
                else:
                    print("rs485_port: FAIL - Data mismatch")
                    fail_count += 1
            except UnicodeError:
                print(f"Test 1: FAIL - UnicodeError: Received data is not valid UTF-8: {received}")
                fail_count += 1
        else:
            print("rs485_port: FAIL - No data received")
            fail_count += 1

        # Test rs485_port TX to port_test RX
        message_2 = "Hello from rs485_port\n"
        while port_test.any():
            port_test.read()
        send_data(rs485_port, message_2)
        # time.sleep(0.2)  # Add delay to allow data to be received
        received = port_test.readline()  # Use readline to read until newline
        if received:
            try:
                received_str = received.decode('utf-8')
                if received_str.strip() == message_2.strip():
                    print("port_test : PASS - Data matches")
                    pass_count += 1
                else:
                    print("port_test : FAIL - Data mismatch")
                    fail_count += 1
            except UnicodeError:
                print(f"Test 2: FAIL - UnicodeError: Received data is not valid UTF-8: {received}")
                fail_count += 1
        else:
            print("Test 2: FAIL - No data received")
            fail_count += 1

    print(f"\nSummary: {pass_count} test(s) passed, {fail_count} test(s) failed")

# Run the test
test_uart_transmission()