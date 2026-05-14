import serial
import threading
import time
import sys

PORT = "COM4"      # change this to your STM32 COM port
BAUD = 115200

running = True


def read_serial(ser):
    while running:
        try:
            line = ser.readline().decode(errors="ignore").strip()
            if line:
                print(f"[STM32] {line}")
        except Exception as e:
            print(f"[READ ERROR] {e}")
            break


def write_serial(ser):
    global running
    while running:
        try:
            msg = input("[YOU] ")
            if msg.lower() == "exit":
                running = False
                break
            ser.write((msg + "\r\n").encode())
        except Exception as e:
            print(f"[WRITE ERROR] {e}")
            break


def main():
    global running
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        time.sleep(2)
        print(f"Connected to {PORT} at {BAUD} baud")
        print("Type commands like:")
        print("  HELP")
        print("  START")
        print("  STOP")
        print("  MODE PI")
        print("  MODE PID")
        print("  SP 2000")
        print("  KP 0.8")
        print("  KI 0.2")
        print("  KD 0.05")
        print("Type 'exit' to quit.\n")

        t = threading.Thread(target=read_serial, args=(ser,), daemon=True)
        t.start()

        write_serial(ser)

    except serial.SerialException as e:
        print(f"Could not open serial port {PORT}: {e}")
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        running = False
        try:
            ser.close()
        except:
            pass
        print("Serial closed.")


if __name__ == "__main__":
    main()
