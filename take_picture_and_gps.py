import datetime
import time
from typing import Tuple

import cv2
import numpy as np
from pysbf2 import SBFReader, SBF_PROTOCOL
# import RPi.GPIO as GPIO
import serial
import io



SBF_PIN = 18 # The GPIO pin on the Pi to send to the SBF Event
SERIAL_PORT_NAME = "/dev/ttyS0' # The serial connection to the receiver
CAMERA_USB_PORT = 0 # The camera USB port

DEBUG_MODE=True # Set to not cause errors due to lack of position

PICTURE_FREQUENCY = 1 # Take a picture and get position every second

def configure_pulse(python_debug_file : io.TextIOWrapper) -> bool:
    """Configures a GPIO pin to output low
    Args:
        python_debug_file (io.TextIOWrapper): The general debug file

    Returns:
        bool: True, if successfully configured
    """
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SBF_PIN, GPIO.OUT)
        GPIO.output(SBF_PIN, GPIO.LOW)
    except (ValueError, RuntimeError) as e:
        python_debug_file.write("ERROR: Could not connect to the GPIO pin ")
        print("Failed to connect to the GPIO pin")
        return False        
    return True

def configure_receiver_connection(python_debug_file : io.TextIOWrapper) -> SBFReader:
    """
    Connect to the receiver
    Args:
        python_debug_file (io.TextIOWrapper): The general debug file

    Returns:
        sbfconnection: Septentrio parser connected to reciever
    """
    # Open serial port
    try:
        # Open serial port
        stream = serial.Serial(
            port=SERIAL_PORT_NAME,  # Change to your port
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,              # 1 second read timeout
            xonxoff=False,          # Disable software flow control
            rtscts=False,           # Disable hardware (RTS/CTS)
            dsrdtr=False            # Disable hardware (DSR/DTR)
        )
    except serial.SerialException as e:
        python_debug_file.write("ERROR: Could not connect to serial port ")
        print("Failed to connect to the receiver")
        return None  # or raise a custom exception
    
    sbfconnection = SBFReader(stream, protfilter= SBF_PROTOCOL)

    return sbfconnection

def configure_camera() -> cv2.VideoCapture:
    """Connect to the camera

    Returns:
        cv2.VideoCapture: The camera connection. Warning, may still be an unsuccessful connection
    """

    camera_connection = cv2.VideoCapture(CAMERA_USB_PORT)
    return camera_connection

def configure_logging() -> Tuple[io.TextIOWrapper, io.BufferedWriter, io.TextIOWrapper]:
    """ Sets up various output files for logging
    Returns:
        io.TextIOWrapper : A file to output raw camera frames
        io.BufferedWriter: A file to output raw septentrio data
        io.TextIOWrapper : A file to output general config and error data
    """
    # Current timestamp
    timestamp = datetime.datetime.now()

    filename = timestamp.strftime("%Y%m%d_%H%M%S")

    # Open the file
    camera_file = open("camerapi_" + filename + ".txt", "w")
    sbf_file = open("sbfpi_" + filename + ".sbf", "wb")
    python_debug_file = open("pythonpi_" + filename + ".txt", "w")

    python_debug_file.write("SBF_PIN: " + str(SBF_PIN))
    python_debug_file.write("\nSBF_PORT: " + SERIAL_PORT_NAME)
    python_debug_file.write("\nCAMERA_PORT: " + str(CAMERA_USB_PORT))
    python_debug_file.write("\nCAMERA_PORT: " + str(CAMERA_USB_PORT))
    python_debug_file.write("\nCAMERA_FREQUENCY: " + str(PICTURE_FREQUENCY))
    python_debug_file.write("\n")

    return camera_file, sbf_file, python_debug_file


def send_pulse():
    """
    Send a 10 ms pulse, reset to Low
    """
    GPIO.output(SBF_PIN, GPIO.HIGH)
    time.sleep(0.010)
    GPIO.output(SBF_PIN,GPIO.LOW)
    
def get_gps_position(sbfconnection,sbf_file, python_debug_file) -> None | dict:
    """
    Control reading the GPS output

    Args:
        sbfconnection: Septentrio parser connected to reciever
        sbf_file: 
        
    """
    # ser.reset_input_buffer()
    # data = ser.read(1028)
    all_data = {}
    raw_data, parsed_data = sbfconnection.read()
    sbf_file.write(raw_data)
    if parsed_data is not None:
        if parsed_data.identity in ["PVTGeodetic","ExtEventPVTGeodetic"]:
            all_data["lat_rad"] = parsed_data.Latitude
            all_data["long_rad"] = parsed_data.Longitude
            all_data["height_m"] = parsed_data.Height
            all_data["week_number"] = parsed_data.WNc
            all_data["time_of_week_ms"] = parsed_data.TOW
            all_data['mode'] = parsed_data.Type
            all_data['error'] = parsed_data.Error
            all_data['horizontal_accuracy_95_m'] = parsed_data.HAccuracy/100
            all_data['vertical_accuracy_95_m'] = parsed_data.VAccuracy/100
            return all_data
        else:
            python_debug_file.write("WARN: Invalid Log ID: ")
            python_debug_file.write(str(parsed_data))
            print("Invalid Log ID")
            return None

    else:
        python_debug_file.write("WARN: No parsable data from the receiver")
        print("No data from receiver")
        return None


def get_camera_frame(camera_connection, python_debug_file):
    """:"""
    # Clear camera buffer to get newest data
    for _ in range(5):
        camera_connection.grab()

    ret, frame = camera_connection.read()
    if not ret:
        python_debug_file.write("WARN: Failed to capture image")
        print("Failed to capture image")
        
    return frame

def send_data(all_data):
    #TODO send the data off the pi to the GCS
    print("Sending data: ")
    print(all_data)

def check_data(all_data):
    key = 'lat_rad'
    if all_data.get(key) is None:
        return False

    if all_data['lat_rad'] == -20000000000.0:
        return False
    if all_data['long_rad'] == -20000000000.0:
        return False
    if all_data["height_m"] == -20000000000.0:
        return False
    if all_data["week_number"] == 65535:
        return False 
    if all_data["time_of_week_ms"] == 42949667295:
        return False
    if all_data['mode'] == 0:
        return False

    if all_data['error'] != 0:
        return False
    if all_data['horizontal_accuracy_95_m'] == 65535/100:
        return False
    if all_data['vertical_accuracy_95_m'] == 65535/100:
        return False
    
    return True
    

def main():
    camera_file, sbf_file, python_debug_file = configure_logging()

    print(type(camera_file))
    print(type(sbf_file))
    print(type(python_debug_file))

    sbfconnection = configure_receiver_connection(python_debug_file)
    while not sbfconnection:
        time.sleep(1)
        sbfconnection = configure_receiver_connection(python_debug_file)

    # gpio_connected = configure_pulse(python_debug_file)
    # if not gpio_connected:
    #     time.sleep(1)
    #     gpio_connected = configure_pulse(python_debug_file)

    camera_connection = configure_camera()
    if not camera_connection.isOpened():
        python_debug_file.write("ERROR: Could not connect to camera")
        print("Failed to connect to the camera")
        time.sleep(1)
        camera_connection = configure_camera()

    while (True):
        target_time = time.time() + PICTURE_FREQUENCY
        camera_frame = get_camera_frame(camera_connection, python_debug_file)
        #send_pulse()
        all_data = get_gps_position(sbfconnection, sbf_file, python_debug_file)

        all_data["Image"] = camera_frame

        camera_file.write(np.array_str(camera_frame))

        if (check_data(all_data) or DEBUG_MODE):
            send_data(all_data)
        else:
            python_debug_file.write("WARN: Invalid Data: ")
            python_debug_file.write(str(all_data))
            print("Invalid Data")


        time_left = target_time - time.time()
        if time_left < 0:
            python_debug_file.write("WARN: Data loop unable to keep up with data collection by: " + str(time_left))
            print("Data loop too slow")

        time.sleep(time_left)

if(__name__=="__main__"):
    main()

