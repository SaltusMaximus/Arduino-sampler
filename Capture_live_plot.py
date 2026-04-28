import os
import sys
import time
import threading
import queue

import serial
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore

PORT = 'COM3'          # CHANGE THIS
BAUD = 1000000
RAW_FILE = 'capacitor_8bit_raw.bin'

START_MARKER = b'START'
END_MARKER = b'END'

# Plot settings
VREF = 5.0
DISPLAY_POINTS = 5000          # keep last N displayed points
UPDATE_INTERVAL_MS = 100       # graph refresh interval
DOWNSAMPLE_FOR_PLOT = 4        # plot every 4th sample to reduce load

sample_queue = queue.Queue()
stop_event = threading.Event()

# Shared display buffer
display_data = []


def serial_worker():
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

    plot_counter = 0

    with open(RAW_FILE, 'wb') as f:
        while True:
            chunk = ser.read(4096)
            if not chunk:
                continue

            buffer += chunk
            end_pos = buffer.find(END_MARKER)

            if end_pos != -1:
                data_part = buffer[:end_pos]
                if data_part:
                    f.write(data_part)

                    for b in data_part:
                        plot_counter += 1
                        if plot_counter % DOWNSAMPLE_FOR_PLOT == 0:
                            sample_queue.put(b)

                break
            else:
                if len(buffer) > 4096:
                    data_part = buffer[:-16]
                    f.write(data_part)

                    for b in data_part:
                        plot_counter += 1
                        if plot_counter % DOWNSAMPLE_FOR_PLOT == 0:
                            sample_queue.put(b)

                    buffer = buffer[-16:]

    ser.close()
    stop_event.set()
    print(f"Saved raw data to: {os.path.abspath(RAW_FILE)}")


class LivePlotWindow(pg.GraphicsLayoutWidget):
    def __init__(self):
        super().__init__(show=True, title="Live Capacitor Capture")
        self.setWindowTitle("Live Capacitor Capture")
        self.resize(1000, 500)

        self.plot_item = self.addPlot(title="Voltage vs Sample Index (live)")
        self.plot_item.setLabel('left', 'Voltage', units='V')
        self.plot_item.setLabel('bottom', 'Displayed Sample Index')
        self.plot_item.showGrid(x=True, y=True)

        self.curve = self.plot_item.plot(pen='y')

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(UPDATE_INTERVAL_MS)

    def update_plot(self):
        global display_data

        updated = False
        while True:
            try:
                sample = sample_queue.get_nowait()
                voltage = sample * VREF / 255.0
                display_data.append(voltage)
                updated = True
            except queue.Empty:
                break

        if len(display_data) > DISPLAY_POINTS:
            display_data = display_data[-DISPLAY_POINTS:]

        if updated:
            self.curve.setData(display_data)

        if stop_event.is_set() and sample_queue.empty():
            print("Capture complete.")
            self.timer.stop()


def main():
    worker = threading.Thread(target=serial_worker, daemon=True)
    worker.start()

    app = QtWidgets.QApplication(sys.argv)
    win = LivePlotWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()