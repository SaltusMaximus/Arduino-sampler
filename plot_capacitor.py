#pip install matplotlib

import csv
import matplotlib.pyplot as plt

CSV_FILE = 'capacitor_8bit_data.csv'

times = []
voltages = []

with open(CSV_FILE, 'r', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        times.append(float(row['time_s']))
        voltages.append(float(row['voltage']))

plt.figure(figsize=(10, 5))
plt.plot(times, voltages)
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.title('Capacitor Voltage vs Time')
plt.grid(True)
plt.tight_layout()
plt.show()