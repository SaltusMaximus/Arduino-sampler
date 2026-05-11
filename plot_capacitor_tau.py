# pip install matplotlib

import csv
import matplotlib.pyplot as plt

ORIGINAL_CSV_FILE = 'capacitor_8bit_data.csv'
ZOOM_CSV_FILE = 'capacitor_tau_zoom_data.csv'

TARGET_VOLTAGE = 3.16
ZERO_THRESHOLD = 0.05
SMOOTHING_WINDOW = 20

times = []
voltages = []
adc_values = []

# --- Load original data ---
with open(ORIGINAL_CSV_FILE, 'r', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        times.append(float(row['time_s']))
        voltages.append(float(row['voltage']))
        adc_values.append(int(row['adc_8bit']))

# --- Smooth data ---
def moving_average(data, window=20):
    smoothed = []
    for i in range(len(data)):
        start = max(0, i - window)
        segment = data[start:i + 1]
        smoothed.append(sum(segment) / len(segment))
    return smoothed

voltages_smooth = moving_average(voltages, SMOOTHING_WINDOW)

# ==================================================
# STEP 1: Find tau first
# ==================================================
tau = None
tau_index = None

for i in range(1, len(voltages_smooth)):
    v1 = voltages_smooth[i - 1]
    v2 = voltages_smooth[i]
    t1 = times[i - 1]
    t2 = times[i]

    if v1 <= TARGET_VOLTAGE <= v2:
        tau = t1 + (TARGET_VOLTAGE - v1) * (t2 - t1) / (v2 - v1)
        tau_index = i
        break

if tau is None:
    print("Voltage never reached 3.16 V.")
    exit()

# ==================================================
# STEP 2: Find latest 0V point BEFORE tau
# ==================================================
start_index = None

for i in range(0, tau_index):
    if voltages_smooth[i] <= ZERO_THRESHOLD:
        start_index = i

if start_index is None:
    print("No 0V point found before tau.")
    exit()

# ==================================================
# STEP 3: Slice only latest 0V → tau
# ==================================================
zoom_times = times[start_index:tau_index + 1]
zoom_voltages = voltages_smooth[start_index:tau_index + 1]
zoom_adc_values = adc_values[start_index:tau_index + 1]

# Normalize time so zoomed graph starts at 0
t0 = times[start_index]
zoom_times = [t - t0 for t in zoom_times]
tau_relative = tau - t0

# Save zoomed data to a NEW file
with open(ZOOM_CSV_FILE, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['index', 'time_s', 'adc_8bit', 'voltage'])

    for i, (t, adc, v) in enumerate(zip(zoom_times, zoom_adc_values, zoom_voltages)):
        writer.writerow([i, t, adc, v])

print(f"Start index used: {start_index}")
print(f"Tau index: {tau_index}")
print(f"Tau absolute time: {tau:.6f} s")
print(f"Tau from latest 0V point: {tau_relative:.6f} s")
print(f"Tau in ms: {tau_relative * 1000:.3f} ms")
# =====================================
# Compute capacitance
# =====================================

R = 10e6  # 10 Megaohms

C = tau_relative / R

print(f"Capacitance (F): {C:.12e}")
print(f"Capacitance (uF): {C * 1e6:.6f} uF")
print(f"Capacitance (nF): {C * 1e9:.6f} nF")
print(f"New zoomed file created: {ZOOM_CSV_FILE}")

# ==================================================
# PLOT 1: Full curve
# ==================================================
plt.figure(figsize=(10, 5))
plt.plot(times, voltages, alpha=0.2, label='Raw')
plt.plot(times, voltages_smooth, linewidth=2, label='Smoothed')

plt.axhline(TARGET_VOLTAGE, linestyle='--', label='3.16 V')
plt.axvline(tau, linestyle='--', label=f'τ absolute = {tau:.6f}s')

plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.title('Full Capacitor Charging Curve')
plt.grid(True)
plt.legend()
plt.tight_layout()

# ==================================================
# PLOT 2: Zoomed curve: latest 0V before tau → 3.16V
# ==================================================
plt.figure(figsize=(10, 5))
plt.plot(zoom_times, zoom_voltages, linewidth=2, label='Zoomed curve')

plt.axhline(TARGET_VOLTAGE, linestyle='--', label='3.16 V')
plt.axvline(tau_relative, linestyle='--', label=f'τ = {tau_relative:.6f}s')
plt.scatter([tau_relative], [TARGET_VOLTAGE], zorder=5)

plt.xlabel('Time from latest 0V point (s)')
plt.ylabel('Voltage (V)')
plt.title('Zoomed Curve: Latest 0V Before τ → 3.16V')
plt.grid(True)
plt.legend()
plt.tight_layout()

plt.show()
