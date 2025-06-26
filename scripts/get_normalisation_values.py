# --------------------- Collect Max Absolute EMG Value Per Channel ---------------------

import socket
import json
import numpy as np
from scipy.signal import butter, filtfilt, iirnotch
import time
import csv
from pathlib import Path
from pynput import keyboard  

# --------------------- Filter functions

def bandpass_filter(data, lowcut=5.0, highcut=50.0, fs=250.0, order=4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, data)

def notch_filter(signal, freq=50.0, fs=250, quality=30):
    nyquist = 0.5 * fs
    norm_freq = freq / nyquist
    b, a = iirnotch(norm_freq, quality)
    return filtfilt(b, a, signal)

def tkeo(signal):  # Teager-Kaiser Energy Operator 
    output = np.zeros_like(signal)
    for i in range(1, len(signal) - 1):
        output[i] = signal[i]**2 - signal[i - 1] * signal[i + 1]  
    return output

# --------------------- OpenBCI UDP settings

UDP_IP = "127.0.0.1"
UDP_PORT = 12345
WINDOW_SIZE = 125  # 0.5 seconds at 250 Hz

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print("Collecting max absolute values... Press ESC to stop and save.")

# Buffers and max trackers
buffer_ch1 = []
buffer_ch2 = []
buffer_ch3 = []

max_abs = [0.0, 0.0, 0.0]  # Will store max absolute value per channel

stop_flag = False

def on_press(key):
    global stop_flag
    if key == keyboard.Key.esc:
        print("ESC pressed. Saving max values and exiting...")
        stop_flag = True
        return False

listener = keyboard.Listener(on_press=on_press)
listener.start()

try:
    while not stop_flag:
        data, addr = sock.recvfrom(4096)
        try:
            packet = json.loads(data.decode())

            if 'data' in packet:
                channel_data = packet['data']

                ch1 = channel_data[0]
                ch2 = channel_data[1]
                ch3 = channel_data[2]

                buffer_ch1.extend(ch1)
                buffer_ch2.extend(ch2)
                buffer_ch3.extend(ch3)

                if len(buffer_ch1) >= WINDOW_SIZE:
                    arr1 = np.array(buffer_ch1)
                    arr2 = np.array(buffer_ch2)
                    arr3 = np.array(buffer_ch3)

                    # Filter
                    arr1 = notch_filter(arr1)
                    arr2 = notch_filter(arr2)
                    arr3 = notch_filter(arr3)

                    arr1 = bandpass_filter(arr1)
                    arr2 = bandpass_filter(arr2)
                    arr3 = bandpass_filter(arr3)

                    arr1 = tkeo(arr1)
                    arr2 = tkeo(arr2)
                    arr3 = tkeo(arr3)

                    # Update max absolute values
                    max_abs[0] = max(max_abs[0], np.max(np.abs(arr1)))
                    max_abs[1] = max(max_abs[1], np.max(np.abs(arr2)))
                    max_abs[2] = max(max_abs[2], np.max(np.abs(arr3)))

                    # Keep only the most recent samples for overlap
                    shift = WINDOW_SIZE - 50
                    buffer_ch1 = buffer_ch1[-shift:]
                    buffer_ch2 = buffer_ch2[-shift:]
                    buffer_ch3 = buffer_ch3[-shift:]

        except Exception as e:
            print("Error decoding JSON:", e)

except KeyboardInterrupt:
    print("Interrupted by user.")

finally:
    sock.close()
    listener.stop()
    # Save to CSV
    save_path = Path("max_abs_values.csv")
    with open(save_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Channel_1_MaxAbs', 'Channel_2_MaxAbs', 'Channel_3_MaxAbs'])
        writer.writerow(max_abs)

    print(f"Saved max absolute values to: {save_path}")
    print(f"Values: {max_abs}")