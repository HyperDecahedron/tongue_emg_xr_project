import socket
import json
import numpy as np
from scipy.signal import butter, filtfilt
import joblib
import pandas as pd
import keyboard 
import time
import matplotlib.pyplot as plt
from collections import deque

# OPEN BCI SETTINGS
UDP_IP = "127.0.0.1"
UDP_PORT = 12345
WINDOW_SIZE = 250

# UNITY SETTINGS
UNITY_IP = "130.229.189.54"
UNITY_PORT = 5052

# FILTER FUNCTIONS
lowc = 20.0
highc = 120.0

def bandpass_filter(data, lowcut=lowc, highcut=highc, fs=250, order=4):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, data)

# FEATURE FUNCTIONS
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

# Setup sockets
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("Listening for UDP packets... (Press ESC to stop)")

# Buffers
buffer_ch1, buffer_ch2, buffer_ch3, buffer_ch4 = [], [], [], []

# Load classifiers
clf = joblib.load('C:/Quick_Disk/tonge_project/notebooks/7_classes_svm.pkl')
#clf_rf = joblib.load('C:/Quick_Disk/tonge_project/notebooks/7_classes_rf.pkl')

# Load normalization parameters
global_means, global_stds = joblib.load('C:/Quick_Disk/tonge_project/notebooks/normalization_params.pkl')

# Column names
cols = [f"{ch}_{feat}" for ch in ['ch_1', 'ch_2', 'ch_3', 'ch_4'] for feat in ['RMS', 'ZC', 'WL']]

# Plotting setup
plotting = 0


# Rolling window buffers for mean/std (e.g., last 5 seconds @ 250Hz = 1250 samples)
ROLLING_WINDOW_SIZE = 1250 # 8s

rolling_buffers = {
    'ch_1': deque(maxlen=ROLLING_WINDOW_SIZE),
    'ch_2': deque(maxlen=ROLLING_WINDOW_SIZE),
    'ch_3': deque(maxlen=ROLLING_WINDOW_SIZE),
    'ch_4': deque(maxlen=ROLLING_WINDOW_SIZE)
}


# Real-time loop
try:
    while True:
        if keyboard.is_pressed('esc'):
            print("ESC pressed. Exiting...")
            break

        data, addr = sock.recvfrom(4096)
        try:
            packet = json.loads(data.decode())

            if 'data' in packet:
                channel_data = packet['data']

                ch1 = channel_data[0]
                ch2 = channel_data[1]
                ch3 = channel_data[2]
                ch4 = channel_data[3]

                buffer_ch1.extend(ch1)
                buffer_ch2.extend(ch2)
                buffer_ch3.extend(ch3)
                buffer_ch4.extend(ch4)

                if len(buffer_ch1) >= WINDOW_SIZE:
                    arr1 = np.array(buffer_ch1)
                    arr2 = np.array(buffer_ch2)
                    arr3 = np.array(buffer_ch3)
                    arr4 = np.array(buffer_ch4)

                    # Filtering
                    arr1_filt = bandpass_filter(arr1)
                    arr2_filt = bandpass_filter(arr2)
                    arr3_filt = bandpass_filter(arr3)
                    arr4_filt = bandpass_filter(arr4)

                    # Z-score using global params
                    #arr1_z = (arr1_filt - global_means['ch_1']) / global_stds['ch_1']
                    #arr2_z = (arr2_filt - global_means['ch_2']) / global_stds['ch_2']
                    #arr3_z = (arr3_filt - global_means['ch_3']) / global_stds['ch_3']
                    #arr4_z = (arr4_filt - global_means['ch_4']) / global_stds['ch_4']

                    # Update rolling buffer with new filtered samples
                    rolling_buffers['ch_1'].extend(arr1_filt)
                    rolling_buffers['ch_2'].extend(arr2_filt)
                    rolling_buffers['ch_3'].extend(arr3_filt)
                    rolling_buffers['ch_4'].extend(arr4_filt)

                    # Compute rolling stats
                    mean1, std1 = np.mean(rolling_buffers['ch_1']), np.std(rolling_buffers['ch_1'])
                    mean2, std2 = np.mean(rolling_buffers['ch_2']), np.std(rolling_buffers['ch_2'])
                    mean3, std3 = np.mean(rolling_buffers['ch_3']), np.std(rolling_buffers['ch_3'])
                    mean4, std4 = np.mean(rolling_buffers['ch_4']), np.std(rolling_buffers['ch_4'])

                    # Z-score normalization using rolling stats
                    arr1_z = (arr1_filt - mean1) / (std1 if std1 > 1e-6 else 1.0)
                    arr2_z = (arr2_filt - mean2) / (std2 if std2 > 1e-6 else 1.0)
                    arr3_z = (arr3_filt - mean3) / (std3 if std3 > 1e-6 else 1.0)
                    arr4_z = (arr4_filt - mean4) / (std4 if std4 > 1e-6 else 1.0)

                    if len(rolling_buffers['ch_1']) < 500:
                        print("waiting to populate buffer")
                        continue  # Skip until buffer is populated


                   
                    # Feature extraction
                    feats = []
                    for ch_signal in [arr1_z, arr2_z, arr3_z, arr4_z]:
                        feats.extend([
                            rms(ch_signal),
                            zero_crossings(ch_signal),
                            waveform_length(ch_signal)
                        ])

                    X_live = pd.DataFrame([feats], columns=cols)
                    prediction_svm = clf.predict(X_live)
                    print("Predicted SVM:", prediction_svm[0])

                    # Clear buffers with overlap
                    shift = 50
                    #buffer_ch1 = buffer_ch1[-shift:]
                    #buffer_ch2 = buffer_ch2[-shift:]
                    #buffer_ch3 = buffer_ch3[-shift:]
                    #buffer_ch4 = buffer_ch4[-shift:]

                    buffer_ch1.clear()
                    buffer_ch2.clear()
                    buffer_ch3.clear()
                    buffer_ch4.clear()

        except Exception as e:
            print("Error decoding JSON:", e)

except KeyboardInterrupt:
    print("Interrupted by user.")

finally:
    sock.close()
    plt.ioff()
    plt.show()
