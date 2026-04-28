import csv

RAW_FILE = 'capacitor_8bit_raw.bin'
CSV_FILE = 'capacitor_8bit_data.csv'
CAPTURE_TIME_S = 17.0
VREF = 5.0


def main():
    with open(RAW_FILE, 'rb') as f:
        raw = f.read()

    num_samples = len(raw)
    fs = num_samples / CAPTURE_TIME_S

    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['index', 'time_s', 'adc_8bit', 'voltage'])

        for i, sample in enumerate(raw):
            t = i / fs
            voltage = sample * VREF / 255.0
            writer.writerow([i, t, sample, voltage])

    print(f"Samples captured: {num_samples}")
    print(f"Estimated sampling rate: {fs:.2f} samples/s")
    print(f"Saved CSV to: {CSV_FILE}")


if __name__ == '__main__':
    main()