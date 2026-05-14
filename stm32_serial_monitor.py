import serial
import threading
import time

# ==========================
# CHANGE THIS TO YOUR COM PORT
# Example: "COM3", "COM5", etc.
# ==========================
PORT = "COM4"
BAUD = 115200

running = True

def read_serial(ser):
    """Continuously read data coming from STM32."""
    while running:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode(errors='ignore').strip()
                if line:
                    print(f"\n[STM32] {line}")
        except Exception as e:
            print(f"\n[ERROR reading serial] {e}")
            break

def write_serial(ser):
    """Allow user to type messages and send to STM32."""
    global running
    while running:
        try:
            msg = input("[YOU] ")
            if msg.lower() == "exit":
                running = False
                break
            ser.write((msg + "\r\n").encode())
        except Exception as e:
            print(f"\n[ERROR writing serial] {e}")
            break

def main():
    global running

    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        time.sleep(2)  # Give STM32 serial port time to settle
        print(f"Connected to STM32 on {PORT} at {BAUD} baud.")
        print("Type messages to send to STM32.")
        print("Type 'exit' to quit.\n")

        # Start reading thread
        reader_thread = threading.Thread(target=read_serial, args=(ser,), daemon=True)
        reader_thread.start()

        # Main thread handles user typing
        write_serial(ser)

    except serial.SerialException as e:
        print(f"Could not open serial port {PORT}: {e}")
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        running = False
        try:
            ser.close()
        except:
            pass
        print("Serial monitor closed.")

if __name__ == "__main__":
    main()
