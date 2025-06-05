# -------------------------- Real Time Classification of Left, Right, Front, None gestures

import socket
import json
import numpy as np
from scipy.signal import butter, filtfilt
import joblib
import pandas as pd
import keyboard 

# OPEN BCI SETTINGS
UDP_IP = "127.0.0.1"  
UDP_PORT = 12345  
WINDOW_SIZE = 250  # 0.5 seconds at 250 Hz

# SENDING TO UNITY
UNITY_IP = "130.229.189.54"  # Replace with your Quest/Unity machine's IP if needed
UNITY_PORT = 5052

# FUNCTIONS -----------------------------------------------------------------------

lowc = 20.0
highc = 120.0

def bandpass_filter(data, lowcut=lowc, highcut=highc, fs=250, order=4):
    nyq = 0.5 * fs  # Nyquist frequency
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, data)

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

# ---------------------------------------------------------------------------------

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("Listening for UDP packets... (Press ESC to stop)")

# Buffers for 3 channels
buffer_ch1 = []
buffer_ch2 = []
buffer_ch3 = []

# Load SVM and RF models
clf = joblib.load('C:/Quick_Disk/tonge_project/notebooks/4_classes_svm.pkl')
clf_rf = joblib.load('C:/Quick_Disk/tonge_project/notebooks/4_classes_rf.pkl')

# Features names
cols = [f"{ch}_{feat}" for ch in ['ch_1', 'ch_2', 'ch_3'] for feat in ['RMS', 'ZC', 'WL']]


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

                ch1 = channel_data[0] # each batch of data has around 8 samples for each channel
                ch2 = channel_data[1]
                ch3 = channel_data[2]

                buffer_ch1.extend(ch1)
                buffer_ch2.extend(ch2)
                buffer_ch3.extend(ch3)

                if len(buffer_ch1) == WINDOW_SIZE:
                    # Convert to numpy arrays
                    arr1 = np.array(buffer_ch1)
                    arr2 = np.array(buffer_ch2)
                    arr3 = np.array(buffer_ch3)

                    # Bandpass filter
                    arr1_filt = bandpass_filter(arr1)
                    arr2_filt = bandpass_filter(arr2)
                    arr3_filt = bandpass_filter(arr3)

                    # Z-score normalization
                    arr1_z = (arr1_filt - np.mean(arr1_filt)) / np.std(arr1_filt)
                    arr2_z = (arr2_filt - np.mean(arr2_filt)) / np.std(arr2_filt)
                    arr3_z = (arr3_filt - np.mean(arr3_filt)) / np.std(arr3_filt)

                    # Feature extraction
                    feats = []
                    for ch_signal in [arr1_z, arr2_z, arr3_z]:
                        feats.append(rms(ch_signal))
                        feats.append(zero_crossings(ch_signal))
                        feats.append(waveform_length(ch_signal))

                    # Prediction
                    X_live = pd.DataFrame([feats], columns=cols)
                    prediction_svm = clf.predict(X_live)                # SVM
                    prediction_rf = clf_rf.predict(X_live)              # RF
                    print("Predicted SVM: ", prediction_svm[0], " | Predicted RF: ", prediction_rf[0])

                    # Send to Unity
                    send_sock.sendto(str(prediction_rf[0]).encode(), (UNITY_IP, UNITY_PORT))
                    #print(f"Sent '{prediction_rf}' to Unity at {UNITY_IP}:{UNITY_PORT}")

                    # Clear buffers
                    # leave the 50 last samples?
                    buffer_ch1.clear()
                    buffer_ch2.clear()
                    buffer_ch3.clear()

        except Exception as e:
            print("Error decoding JSON:", e)

except KeyboardInterrupt:
    print("Interrupted by user.")

finally:
    sock.close()