import serial
import time
import os

PORT = 'COM3'          # CHANGE THIS
BAUD = 1000000
RAW_FILE = 'capacitor_8bit_raw.bin'

START_MARKER = b'START'
END_MARKER = b'END'


def main():
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)  # allow Arduino reset after opening serial

    print("Logger ready.")
    print("Saving to:", os.path.abspath(RAW_FILE))

    # Tell Arduino to begin
    ser.write(b'GO\n')
    ser.flush()

    print("Sent GO command. Waiting for START marker...")

    buffer = b''

    while True:
        chunk = ser.read(1024)
        if chunk:
            buffer += chunk
            pos = buffer.find(START_MARKER)
            if pos != -1:
                buffer = buffer[pos + len(START_MARKER):]
                break

        if len(buffer) > 8192:
            buffer = buffer[-16:]

    print("START found. Capturing data...")

    with open(RAW_FILE, 'wb') as f:
        while True:
            chunk = ser.read(4096)
            if not chunk:
                continue

            buffer += chunk
            end_pos = buffer.find(END_MARKER)

            if end_pos != -1:
                f.write(buffer[:end_pos])
                break
            else:
                if len(buffer) > 4096:
                    f.write(buffer[:-16])
                    buffer = buffer[-16:]

    ser.close()
    print(f"Saved raw data to: {os.path.abspath(RAW_FILE)}")


if __name__ == '__main__':
    main()