from machine import UART, Pin, SPI
import time
import uasyncio as asyncio
import my_oled  # OLED Library

# Constants
MAX_MESSAGE_LEN = 64
team = [b'W', b'S', b'D', b'A', b'X']
id = b'W'
broadcast = b'X'
led = Pin(2, Pin.OUT)

# SPI Setup for L9958SB (Motor Driver)
spi = SPI(1, baudrate=1000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
cs_motor1 = Pin(5, Pin.OUT)  # Chip Select for Motor 1
cs_motor2 = Pin(21, Pin.OUT) # Chip Select for Motor 2

# UART Setup
uart = UART(2, baudrate=9600, tx=17, rx=16)

# Define motor speed mappings
motor_speed_commands = {
    b'MotorSpeed0YB': 0,
    b'MotorSpeed20YB': 20,
    b'MotorSpeed40YB': 40,
    b'MotorSpeed60YB': 60,
    b'MotorSpeed80YB': 80,
    b'MotorSpeed100YB': 100
}

def log(message):
    """Print and display log messages."""
    print(f"ESP: {message}")
    my_oled.print_text(message, 0, 0)  # OLED Display Feedback
    time.sleep(0.5)

def send_spi(cs_pin, command, value):
    """Send SPI command to motor driver."""
    cs_pin.value(0)  # Select motor driver
    spi.write(bytearray([command, value]))  # Send command + speed value
    cs_pin.value(1)  # Deselect motor driver
    log(f"Sent SPI: CMD {command}, VALUE {value}")

def set_motor_speed(speed):
    """Control both motors using SPI."""
    send_spi(cs_motor1, 0x01, speed)  # Send speed to Motor 1
    send_spi(cs_motor2, 0x01, speed)  # Send speed to Motor 2

async def process_rx():
    """Handles UART messages, validates sender/receiver, and forwards valid messages."""
    stream = b''
    receiving_message = False

    while True:
        c = uart.read(1)
        if c:
            stream += c

            # Detect message start
            if stream.endswith(b'AZ'):
                log("Msg Start")
                receiving_message = True

            # Process known motor speed commands
            for command, speed in motor_speed_commands.items():
                if stream.endswith(command):
                    log(f"Setting Motor Speed: {speed}%")
                    set_motor_speed(speed)  # Adjust both motors
                    stream = b''  # Reset stream after successful parsing
                    receiving_message = False

            # Detect message end
            if stream.endswith(b'YB'):
                log("Message Received")
                receiving_message = False

                # Validate sender & receiver before forwarding
                if len(stream) >= 4:
                    sender, receiver = stream[-4:-3], stream[-3:-2]

                    if sender in team and receiver in team:
                        log(f"Forwarding to {receiver}")
                        uart.write(stream)  # Pass valid message to teammate
                    else:
                        log("Invalid sender/receiver, discarding message")

                stream = b''  # Reset for next message

            # Prevent buffer overflow
            if len(stream) > MAX_MESSAGE_LEN:
                log("Message Too Long, Resetting")
                stream = b''
                receiving_message = False

        await asyncio.sleep_ms(10)

async def heartbeat():
    """Periodic heartbeat messages over UART."""
    while True:
        uart.write(b'AZDS444YB')
        log("Sending Heartbeat")
        await asyncio.sleep(10)

async def main():
    """Main async event loop."""
    while True:
        await asyncio.sleep(1)

# Run tasks
asyncio.create_task(process_rx())
asyncio.create_task(heartbeat())

try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
