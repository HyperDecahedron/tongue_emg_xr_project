# -------------------------- Real Time Classification: Left, Left-front, Front, Right-front, Right, Swallow, None

# When pressing Esc, the application finishes

import socket
import json
import numpy as np
from scipy.signal import butter, filtfilt, iirnotch
import joblib
import pandas as pd
import time
import os
from datetime import datetime
from pathlib import Path
from pynput import keyboard  

# -------------- Filter functions 

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
    filtered_signal = filtfilt(b, a, signal)
    return filtered_signal

def tkeo(signal):  # Teager-Kaiser Energy Operator 
    output = np.zeros_like(signal)
    for i in range(1, len(signal) - 1):
        output[i] = signal[i]**2 - signal[i - 1] * signal[i + 1]  
    return output

# -------------- Feature functions 

def rms(signal):
    return np.sqrt(np.mean(signal**2))

def zero_crossings(signal):
    signs = np.sign(signal)
    for i in range(1, len(signs)):
        if signs[i] == 0:
            signs[i] = signs[i-1] if signs[i-1] != 0 else 1
    return np.sum(np.diff(signs) != 0)

def waveform_length(signal):
    return np.sum(np.abs(np.diff(signal)))

def mav(signal):
    return np.mean(np.abs(signal))

def iav(signal):
    return np.sum(np.abs(signal))

def rms_signed_difference(signal):
    mean_val = np.mean(signal)
    diff = signal - mean_val
    return np.sqrt(np.mean(diff**2))

def mean_frequency(signal, fs=250):
    freqs = np.fft.rfftfreq(len(signal), d=1/fs) # Compute FFT
    fft_vals = np.abs(np.fft.rfft(signal))
    power = fft_vals ** 2
    if np.sum(power) == 0:
        return 0
    mf = np.sum(freqs * power) / np.sum(power)
    return mf

# -----------------------------------------------------

# OPEN BCI SETTINGS
UDP_IP = "127.0.0.1"  
UDP_PORT = 12345  
WINDOW_SIZE = 125  # samples at 250 Hz

# SENDING TO UNITY
#UNITY_IP = "130.229.189.54"  # Replace with Quest/Unity machine's IP 
#UNITY_PORT = 5052

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("Listening for UDP packets... (Press ESC to stop)")

# Buffers for 3 channels
buffer_ch1 = []
buffer_ch2 = []
buffer_ch3 = []

# Get the directory of the current script
script_dir = Path(__file__).resolve().parent

# Navigate to the model and scaler files
notebooks_dir = script_dir.parent / 'notebooks'
clf_rf_path = notebooks_dir / '6_classes_rf_cont_18_06.pkl'
scaler_path = notebooks_dir / '6_classes_scaler_rf_cont_18_06.pkl'

# Load the files
clf_rf = joblib.load(clf_rf_path)
scaler = joblib.load(scaler_path)

# Features names
cols = [f"{ch}_{feat}" for ch in ['ch_1', 'ch_2', 'ch_3'] for feat in ['RMS', 'RMS_SD', 'ZC', 'WL', 'MAV', 'STD', 'VAR', 'IAV', 'MF']]

# CSV logging
#now = datetime.now()
#output_dir = "data/online_annotations"
#os.makedirs(output_dir, exist_ok=True)
#csv_filename = f"{output_dir}/online_classes_{now.day}_{now.month}_{now.hour}_{now.minute}.csv"
#if not os.path.exists(csv_filename):
#    with open(csv_filename, 'w') as f:
#        f.write("class,timestamp\n")

stop_flag = False

def on_press(key):
    global stop_flag
    if key == keyboard.Key.esc:
        print("ESC pressed. Exiting...")
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

                ch1 = channel_data[0] # each batch of data has around 8 samples for each channel
                ch2 = channel_data[1]
                ch3 = channel_data[2]

                buffer_ch1.extend(ch1)
                buffer_ch2.extend(ch2)
                buffer_ch3.extend(ch3)

                if len(buffer_ch1) >= WINDOW_SIZE:
                    # Convert to numpy arrays
                    arr1 = np.array(buffer_ch1)
                    arr2 = np.array(buffer_ch2)
                    arr3 = np.array(buffer_ch3)

                    # Notch filter
                    arr1 = notch_filter(arr1)
                    arr2 = notch_filter(arr2)
                    arr3 = notch_filter(arr3)

                    # Bandpass filter
                    arr1 = bandpass_filter(arr1)
                    arr2 = bandpass_filter(arr2)
                    arr3 = bandpass_filter(arr3)

                    # TKEO
                    arr1 = tkeo(arr1)
                    arr2 = tkeo(arr2)
                    arr3 = tkeo(arr3)

                    # Z-score normalization
                    #arr1_z = (arr1_filt - np.mean(arr1_filt)) / np.std(arr1_filt)
                    #arr2_z = (arr2_filt - np.mean(arr2_filt)) / np.std(arr2_filt)
                    #arr3_z = (arr3_filt - np.mean(arr3_filt)) / np.std(arr3_filt)

                    # Feature extraction
                    feats = []
                    for ch_signal in [arr1, arr2, arr3]:
                        feats.append(rms(ch_signal))
                        feats.append(rms_signed_difference(ch_signal))
                        feats.append(zero_crossings(ch_signal))
                        feats.append(waveform_length(ch_signal))
                        feats.append(mav(ch_signal))
                        feats.append(np.std(ch_signal))
                        feats.append(np.var(ch_signal))
                        feats.append(iav(ch_signal))
                        feats.append(mean_frequency(ch_signal))

                    # Scale features
                    X_live = pd.DataFrame([feats], columns=cols)
                    X_scaled = scaler.transform(X_live)

                    # Prediction
                    X_scaled_df = pd.DataFrame(X_scaled, columns=cols)
                    prediction_rf = clf_rf.predict(X_scaled_df)
                    print("Predicted: ", prediction_rf[0])

                    # Send to Unity
                    #send_sock.sendto(str(prediction_rf[0]).encode(), (UNITY_IP, UNITY_PORT))
                    #print(f"Sent '{prediction_rf}' to Unity at {UNITY_IP}:{UNITY_PORT}")

                    # Log prediction and timestamp
                    #timestamp = time.time()
                    #with open(csv_filename, 'a') as f:
                    #    f.write(f"{prediction_rf[0]},{timestamp}\n")

                    # Clear buffers
                    # keep last 'shift' samples
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