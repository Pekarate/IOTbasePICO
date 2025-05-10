import sys
from machine import Pin, UART
import time

def configure_uart(baudrate):
    platform = sys.platform

    if platform == "esp32":
        print("ESP32 detected")
        port_test = UART(1, baudrate=baudrate, tx=Pin(11), rx=Pin(12), rxbuf=1024, timeout=500)
        rs485_port = UART(2, baudrate=baudrate, tx=Pin(33), rx=Pin(34), rxbuf=1024, timeout=500)
    elif platform == "rp2":
        print("RP2040 detected")
        # Check if baudrate is supported (RP2040 typically supports up to 921600 reliably)
        # if baudrate > 921600:
        #     print(f"Baudrate {baudrate} may not be supported on RP2040. Skipping.")
        #     return None, None
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
                    print("Test 1: PASS - Data matches")
                    pass_count += 1
                else:
                    print("Test 1: FAIL - Data mismatch")
                    fail_count += 1
            except UnicodeError:
                print(f"Test 1: FAIL - UnicodeError: Received data is not valid UTF-8: {received}")
                fail_count += 1
        else:
            print("Test 1: FAIL - No data received")
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
                    print("Test 2: PASS - Data matches")
                    pass_count += 1
                else:
                    print("Test 2: FAIL - Data mismatch")
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