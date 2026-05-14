import serial
import time

ser = serial.Serial('COM4', 115200, timeout=1)

time.sleep(2)  # allow connection to settle

print("Connected to STM32")

while True:
    # -------- RECEIVE FROM STM32 --------
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            print("STM32:", line)

    # -------- SEND TO STM32 --------
    cmd = input("Send to STM32: ")
    ser.write((cmd + "\r\n").encode())
