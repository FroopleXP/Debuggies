import network
from machine import Pin, PWM
import time
import gc
import usocket as socket

# NB: This is terrible I know but MicroPython doesn't support enums!
# System states
SystemStates_STARTUP = "STARTUP"
SystemStates_WAITING_FOR_CLIENT = "WAITING_FOR_CLIENT"
SystemStates_SERVING_RESPONSES = "SERVING_RESPONSES"
SystemStates_FATAL_ERROR = "FATAL_ERROR"

# Describes the LED blink frequency based on the system state
LedBlinkDutyCycle_STARTUP = int(1023 / 2)                # 50% duty cyle (500ms)
LedBlinkDutyCycle_WAITING_FOR_CLIENT = int(1023 / 4)     # 25% duty cycle (250ms)
LedBlinkDutyCycle_SERVING_RESPONSES = int(1023 / 2)      # 100% duty cycle (1000ms)
LedBlinkDutyCycle_FATAL_ERROR = int(1023 / 8)            # 12.5% duty cyle (125ms)

# Creating global state
global system_state
system_state = SystemStates_STARTUP

# Define the status LED
stat_led_pwm = PWM(Pin(2), 1)

# Creating the WiFi AP
ap_if = network.WLAN(network.AP_IF)
ap_if.config(essid="My Bitch's Brew", channel=11, password="letmein123")
ap_if.ifconfig(("10.5.0.2", "255.255.255.0", "10.5.0.1", "8.8.8.8"))
ap_if.active(True)

# Creating the socket connection
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("10.5.0.2", 80))
s.listen(5)

# Enable garbage collector to free up memory
gc.enable()

# ---- Functions ----
# NB: This could be ported into another file

# Waits and blocks the CPU unitl a client connects
def wait_for_client_connect():
    while not ap_if.isconnected():
        pass
"""
    Waits for client requests and responds to them.
    The system won't leave this state until power off.
"""
def serve_client_requests():
    while True:
        conn, _ = s.accept()                         # NB: This is a blocking call
        conn.sendall("HTTP/1.1 200 OK\nContent-Type: application/json\nConnection: close\n\n{\"success\":\"Yes, it was succesful\"}")
        conn.close()
        
# ---- Utils ----

# Checks the duty cycle before setting it
def check_and_set_duty_cycle(duty_effect, duty_cycle):
    if not duty_effect.duty() == duty_cycle:
        duty_effect.duty(duty_cycle)

# ---- End Functions ----

# Main program loop
while True:
    try:

        # Checking the system state and acting accord.
        # NB: No fucking 'switch' in Python? FML...

        # Handle default state
        if system_state == SystemStates_STARTUP:
            stat_led_pwm.duty(LedBlinkDutyCycle_STARTUP)
            system_state = SystemStates_WAITING_FOR_CLIENT

        # Fail safe, when all else fail - do it safely.
        elif system_state == SystemStates_FATAL_ERROR:
            stat_led_pwm.duty(LedBlinkDutyCycle_FATAL_ERROR)

        # When waiting for the client to connect
        elif system_state == SystemStates_WAITING_FOR_CLIENT:
            # TODO: Check the duty cycle before setting?
            stat_led_pwm.duty(LedBlinkDutyCycle_WAITING_FOR_CLIENT)
            wait_for_client_connect()
            system_state = SystemStates_SERVING_RESPONSES

        # Wait and serve responses to the user
        elif system_state == SystemStates_SERVING_RESPONSES:
            stat_led_pwm.duty(LedBlinkDutyCycle_SERVING_RESPONSES)
            serve_client_requests()

    except:
        system_state = SystemStates_FATAL_ERROR
