import threading as th
import signal
import sys
import RPi.GPIO as GPIO
import time, math

BUTTON_GPIO = 16
LDR_GPIO = 4
TRIGGER_GPIO = 23
ECHO_GPIO = 24

def signal_handler(sig, frame):
    global power_on

    print("Exiting program")
    power_on = False
    GPIO.cleanup()
    sys.exit(0)

def setup_devices():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(LDR_GPIO, GPIO.IN)
    GPIO.setup(TRIGGER_GPIO, GPIO.OUT)
    GPIO.setup(ECHO_GPIO, GPIO.IN)

def get_luminosity(PIN_LDR):
    count = 0

    GPIO.setup(PIN_LDR, GPIO.OUT)
    GPIO.output(PIN_LDR, GPIO.LOW)
    time.sleep(0.1)

    # Change the pin back to input
    GPIO.setup(PIN_LDR, GPIO.IN)

    # Count until the pin goes high
    while (GPIO.input(PIN_LDR) == GPIO.LOW):
        count += 1

    return count

def get_distance(PIN_TRIGGER, PIN_ECHO):
    # Initialize the trigger pin to low
    GPIO.output(PIN_TRIGGER, GPIO.LOW)
    time.sleep(0.5)

    GPIO.output(PIN_TRIGGER, GPIO.HIGH)
    # 0.01 miliseconds
    time.sleep(0.00001)
    GPIO.output(PIN_TRIGGER, GPIO.LOW)

    pulse_start = time.time()
    while GPIO.input(PIN_ECHO) == GPIO.LOW:
        pulse_start = time.time()

    pulse_end = time.time()
    while GPIO.input(PIN_ECHO) == GPIO.HIGH:
        pulse_end = time.time()

    # If the pulse_end is greater than pulse_start, then calculate the distance
    pulse_duration = pulse_end - pulse_start

    return pulse_duration * 17150

def print_luminosity(light_count):
    MAX = 1000000
    # Ensure light is not zero to avoid math error
    if light_count == 0:
        light_count = 1

    # Calculate logarithmic scale.
    log_light = math.log10(light_count)

    # Normalize log_light to the range 0-1
    normalized_light = log_light / math.log10(MAX)

    print("Luminosity:")
    print("\t|" + ("#" * int(40 * (1 - normalized_light))) + (" " * int(40 * normalized_light)) + "|")
    print("\tCapacitor charge count:", light_count)

def button_callback(channel):
    global power_on
    power_on = not power_on
    print('Vehicle power is', 'on' if power_on else 'off')

def button_thread():
    # Button thread shall live as long as the program is running

    GPIO.add_event_detect(BUTTON_GPIO, GPIO.RISING, callback=button_callback, bouncetime=50)
    while True:
        time.sleep(0.1)

def luminosity_thread():
    global power_on

    while power_on:
        print_luminosity(get_luminosity(LDR_GPIO))
        time.sleep(0.1)

def distance_thread():
    global power_on

    while power_on:
        print("Distance:", get_distance(TRIGGER_GPIO, ECHO_GPIO), "cm")
        time.sleep(0.1)

def launch_threads():
    try:
        th.Thread(target=button_thread, daemon=True).start()
        th.Thread(target=luminosity_thread, daemon=True).start()
        th.Thread(target=distance_thread, daemon=True).start()
        return 0
    except:
        return -1
    

if __name__ == "__main__":
    power_on = False
    threads_initialized = False
    setup_devices()
    
    signal.signal(signal.SIGINT, signal_handler)

    while True:
        if power_on:
            if not threads_initialized:
                if(launch_threads() == 0):
                    threads_initialized = True
                else:
                    print("[ERROR] Something went wrong while initializing the threads")
                    break
        else:
            threads_initialized = False
        
        time.sleep(0.1)