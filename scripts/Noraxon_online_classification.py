import numpy as np
import requests
import time
import joblib
from scipy.signal import butter, filtfilt, iirnotch, hilbert, find_peaks
from pykalman import KalmanFilter
import pywt
import pandas as pd
import tkinter as tk
from tkinter import ttk
import threading
import socket

# ---------------- Settings -----------------
USE_BANDPASS = 1
USE_NOTCH = 1
USE_HILBERT = 1
USE_KALMAN = 0
USE_TKEO = 0
USE_ENVELOPE = 0
USE_ZSCORE = 0
USE_SCALING = 1

sampling_rate = 1500
window_size_seconds = 1.25
window_size_samples = int(window_size_seconds * sampling_rate)

channels = ['ch_1', 'ch_2', 'ch_3']

# Pressure ranges (slight, medium, hard)
SLIGHT_PRESSURE = 30
MEDIUM_PRESSURE = 60
HARD_PRESSURE = 100

# UDP communication
UNITY_IP = "172.27.228.52"  # Use the Quest or Unity PC IP if not running on the same machine
UNITY_PORT = 5052
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ---------------- Filters -----------------
def bandpass_filter(data, lowcut=5.0, highcut=120.0, fs=sampling_rate, order=4):
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

def hilbert_envelope(signal):
    analytic = hilbert(signal)
    return np.abs(analytic)

def kalman(signal):
    signal = signal.reshape(-1, 1)
    kf = KalmanFilter(transition_matrices=[1],
                      observation_matrices=[1],
                      initial_state_mean=0,
                      observation_covariance=0.01,
                      transition_covariance=1e-5)
    state_means, _ = kf.filter(signal)
    return state_means.flatten()

def tkeo(signal):
    output = np.zeros_like(signal)
    for i in range(1, len(signal) - 1):
        output[i] = signal[i]**2 - signal[i - 1] * signal[i + 1]
    return output

# ---------------- Feature extraction ----------------
def rms(signal):
    return np.sqrt(np.mean(signal**2))

def rms_signed_difference(signal):
    mean_val = np.mean(signal)
    diff = signal - mean_val
    return np.sqrt(np.mean(diff**2))

def zero_crossings(signal):
    signs = np.signbit(signal)
    return np.sum(signs[1:] != signs[:-1])

def waveform_length(signal):
    return np.sum(np.abs(np.diff(signal)))

def mav(signal):
    return np.mean(np.abs(signal))

def iav(signal):
    return np.sum(np.abs(signal))

def mean_frequency(signal, fs=sampling_rate):
    freqs = np.fft.rfftfreq(len(signal), d=1/fs)
    fft_vals = np.abs(np.fft.rfft(signal))
    power = fft_vals**2
    if np.sum(power) == 0:
        return 0
    return np.sum(freqs * power) / np.sum(power)

def extract_features(window):
    feature_names = ['RMS', 'RMS_SD', 'ZC', 'WL', 'MAV', 'STD', 'VAR', 'IAV', 'MF']
    feats = []
    for ch_idx in range(len(channels)):
        ch_signal = window[:, ch_idx]
        feats.extend([
            rms(ch_signal),
            rms_signed_difference(ch_signal),
            zero_crossings(ch_signal),
            waveform_length(ch_signal),
            mav(ch_signal),
            np.std(ch_signal),
            np.var(ch_signal),
            iav(ch_signal),
            mean_frequency(ch_signal)
        ])
    cols = [f"{ch}_{feat}" for ch in channels for feat in feature_names]
    return pd.DataFrame([feats], columns=cols)

# ---------------- GUI Setup ----------------------
class EMGApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EMG UI")
        self.root.geometry("550x300")
        self.root.configure(bg="white")

        self.bulb_colors = {"off": "gray", "l": "green", "f": "green", "r": "green", "s": "yellow"}
        self.positions = ['l', 'f', 'r', 's']

        # Bulbs
        self.bulbs = {}
        for i, pos in enumerate(self.positions):
            canvas = tk.Canvas(root, width=60, height=60, bg="white", highlightthickness=0)
            canvas.grid(row=0, column=i, padx=10, pady=20)
            bulb = canvas.create_oval(10, 10, 50, 50, fill=self.bulb_colors["off"])
            self.bulbs[pos] = (canvas, bulb)

        # Sliders + Labels for pressure level
        self.sliders = {}
        self.slider_labels = {}
        for i, label in enumerate(['Left', 'Front', 'Right']):
            tk.Label(root, text=label, bg="white").grid(row=1+i, column=0, sticky='w', padx=10)

            slider = ttk.Scale(root, from_=0, to=100, orient='horizontal', length=300)
            slider.grid(row=1+i, column=1, columnspan=2, pady=5)
            self.sliders[label.lower()] = slider

            level_label = tk.Label(root, text="None", bg="white", fg="black", width=8)
            level_label.grid(row=1+i, column=3, padx=10)
            self.slider_labels[label.lower()] = level_label

    def update_bulbs(self, pred_label):
        for pos, (canvas, bulb) in self.bulbs.items():
            color = self.bulb_colors[pred_label] if pos == pred_label else self.bulb_colors["off"]
            canvas.itemconfig(bulb, fill=color)

    def update_sliders(self, pressure_values):
        keys = ['left', 'front', 'right']
        for i, val in enumerate(pressure_values):
            key = keys[i]
            val_clamped = max(0, min(100, val))
            self.sliders[key].set(val_clamped)

            # Determine level
            if val_clamped <= 5:
                level_text = "None"
                color = "black"
            elif val_clamped < SLIGHT_PRESSURE:
                level_text = "Slight"
                color = "green"
            elif val_clamped < MEDIUM_PRESSURE:
                level_text = "Medium"
                color = "orange"
            else:
                level_text = "Hard"
                color = "red"

            self.slider_labels[key].config(text=level_text, fg=color)


# ---------------- Data acquisition ----------------
def get_data():
    try:
        url = 'http://127.0.0.1:9220/samples'
        response = requests.get(url)
        if response.status_code == 200:
            json_data = response.json()
            channels_data = json_data.get('channels', [])
            if len(channels_data) < 3:
                #print(f"Warning: expected 3 channels but got {len(channels_data)}")
                return []
            emg_1 = channels_data[0]['samples']
            emg_2 = channels_data[1]['samples']
            emg_3 = channels_data[2]['samples']
            return list(zip(emg_1, emg_2, emg_3))
        else:
            print(f"Error: Unable to fetch data. Status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception in get_data: {e}")
        return []


# ---------------- Main online classification ----------------


def run_model_loop(app):

    # Load models and scalers
    pos_clf = joblib.load("../notebooks/models/4_classes_cont_01_07.pkl")
    pos_scaler = joblib.load("../notebooks/models/4_classes_scaler_cont_01_07.pkl") if USE_SCALING else None
    pressure_regressor = joblib.load("../notebooks/models/regressor_01_07.joblib") # whole pipeline already included, it is not necessary to upload the scaler

    # Buffers for data
    buffer = [] 

    # State variables for your new filtering logic
    swallow_count = 0
    override_to_r = False

    override_active = False
    override_label = None
    override_count = 0

    print(f"Starting online classification with window size {window_size_seconds}s ({window_size_samples} samples)...")

    while True:
        new_data = get_data()
        if not new_data:
            time.sleep(0.1)
            continue

        buffer.extend(new_data)

        # If buffer full enough
        if len(buffer) >= window_size_samples: 
            window = np.array(buffer[:window_size_samples])
            buffer = buffer[window_size_samples:]  # clear buffer

            # Apply filtering channel-wise
            for i in range(window.shape[1]):
                if i in [0,1,2]:
                    if USE_NOTCH == 1:
                        window[:, i] = notch_filter(window[:, i], fs=sampling_rate)
                    if USE_BANDPASS == 1:
                        window[:, i] = bandpass_filter(window[:, i])
                    if USE_HILBERT == 1:
                        window[:, i] = hilbert_envelope(window[:, i])
                    if USE_KALMAN == 1:
                        window[:, i] = kalman(window[:, i])
                    if USE_TKEO == 1:
                        window[:, i] = tkeo(window[:, i])
                    if USE_ENVELOPE == 1:
                        # can use compute_envelope_peaks or compute_envelope
                        pass
                    if USE_ZSCORE == 1:
                        mean = window[:, i].mean()
                        std = window[:, i].std() if window[:, i].std() != 0 else 1
                        window[:, i] = (window[:, i] - mean) / std

            # Extract features
            feats = extract_features(window)

            # Scale features for position classifier if needed
            if USE_SCALING and pos_scaler is not None:
                feats_pos = pos_scaler.transform(feats)
                feats_pos = pd.DataFrame(feats_pos, columns=feats.columns) 
            else:
                feats_pos = feats

            feats_pressure = feats

            # Predict position
            pos_pred = pos_clf.predict(feats_pos)

            # Predict pressure
            pressure_pred = pressure_regressor.predict(feats_pressure)

            # Print original predictions
            print(f"Original Position prediction: {pos_pred[0]}, Original Pressure prediction: {pressure_pred}")

            # -------- Additional filtering ---------

            # Keep only the highest pressure, set others to 0
            pressure_pred = pressure_pred[0]  
            max_idx = np.argmax(pressure_pred)
            filtered_pressure = np.zeros_like(pressure_pred)
            filtered_pressure[max_idx] = pressure_pred[max_idx]

            pos_label = pos_pred[0]  # e.g. 'l', 'f', 'r', 'n', 's'

            # Final filter: if a class l, f or r is happening for more than 4 instances, ALL following classes
            # are overriden to that class until a class 'n' is detected. Class 's' is an exception to this. 

            # Logic: track consecutive 's' (swallow) predictions
            if pos_label == 's':
                swallow_count += 1
            else:
                swallow_count = 0  # reset if not 's'

            # Reset override if position is 'n'
            if pos_label in ['n']:
                override_to_r = False

            # Activate override condition if swallow_count > 3 and max_idx == 2 ('r')
            if swallow_count >= 2 and max_idx == 2:
                override_to_r = True

            # Apply override if active
            if override_to_r:
                pos_label = 'r'

            # Positions that don't require adjustment
            if pos_label in ['n', 's']:
                # do nothing, keep filtered_pressure as is
                pass
            else:
                # Map position label to expected pressure index
                pos_to_idx = {'l': 0, 'f': 1, 'r': 2}
                expected_idx = pos_to_idx.get(pos_label, None)

                if expected_idx is not None:
                    # Check if filtered pressure corresponds to expected position
                    if filtered_pressure.argmax() != expected_idx:
                        # Pressure indicates a different position than predicted
                        # Override position label to the pressure position
                        idx_to_pos = {v: k for k, v in pos_to_idx.items()}
                        pos_label = idx_to_pos[filtered_pressure.argmax()]

            # -------- Override filtering ---------
            # Track how many consecutive times the same 'l','f','r' position occurs
            if pos_label in ['l', 'f', 'r']:
                if override_active:
                    if pos_label == override_label:
                        override_count += 1
                else:
                    override_active = True
                    override_label = pos_label
                    override_count = 1
            elif pos_label == 'n':
                # Reset override on 'n'
                override_active = False
                override_label = None
                override_count = 0

            # If override active for more than x times, force override on all following (except 'n')
            if override_active and override_count > 2:
                if pos_label not in ['n']:
                    pos_label = override_label

            # Print filtered/final predictions
            print(f"--Filtered Position prediction: {pos_label}, Filtered Pressure prediction: {filtered_pressure}")

            # Update UI with filtered predictions
            app.root.after(0, app.update_bulbs, pos_label)
            app.root.after(0, app.update_sliders, filtered_pressure)

            # Send filtered position and filtered pressure to Unity as a string like: "pos_label,filtered_pressure", "l,50,0,0"
            pressure_values = [int(p) for p in filtered_pressure]  
            message = f"{pos_label},{pressure_values[0]},{pressure_values[1]},{pressure_values[2]}"
            try:
                udp_socket.sendto(message.encode('utf-8'), (UNITY_IP, UNITY_PORT))
            except Exception as e:
                print(f"Error sending UDP message: {e}")

        else:
            # Sleep shortly to avoid busy loop
            time.sleep(0.5)

if __name__ == "__main__":
    root = tk.Tk()
    app = EMGApp(root)

    threading.Thread(target=run_model_loop, args=(app,), daemon=True).start()
    root.mainloop()
