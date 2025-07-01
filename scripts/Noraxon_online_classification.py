import numpy as np
import requests
import time
import joblib
from scipy.signal import butter, filtfilt, iirnotch, hilbert, find_peaks
from pykalman import KalmanFilter
import pywt

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
window_size_seconds = 1.75
window_size_samples = int(window_size_seconds * sampling_rate)

channels = ['ch_1', 'ch_2', 'ch_3']

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
    feats = []
    for ch_idx in range(len(channels)):
        ch_signal = window[:, ch_idx]
        feats.append(rms(ch_signal))
        feats.append(rms_signed_difference(ch_signal))
        feats.append(zero_crossings(ch_signal))
        feats.append(waveform_length(ch_signal))
        feats.append(mav(ch_signal))
        feats.append(np.std(ch_signal))
        feats.append(np.var(ch_signal))
        feats.append(iav(ch_signal))
        feats.append(mean_frequency(ch_signal))
    return np.array(feats).reshape(1, -1)

# ---------------- Data acquisition ----------------
def get_data():
    try:
        url = 'http://127.0.0.1:9220/samples'
        response = requests.get(url)
        if response.status_code == 200:
            json_data = response.json()
            emg_1 = json_data['channels'][0]['samples']
            emg_2 = json_data['channels'][1]['samples']
            emg_3 = json_data['channels'][2]['samples']
            return list(zip(emg_1, emg_2, emg_3))
        else:
            print(f"Error: Unable to fetch data. Status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception in get_data: {e}")
        return []

# ---------------- Main online classification ----------------
def main():
    # Load models and scalers
    pos_clf = joblib.load("../notebooks/models/4_classes_cont_01_07.pkl")
    pos_scaler = joblib.load("../notebooks/models/4_classes_scaler_cont_01_07.pkl") if USE_SCALING else None

    pressure_regressor = joblib.load("../notebooks/models/regressor_01_07.joblib") # whole pipeline already included, it is not necessary to upload the scaler

    # Buffers for data
    buffer = [] 

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
            else:
                feats_pos = feats

            feats_pressure = feats

            # Predict position
            pos_pred = pos_clf.predict(feats_pos)

            # Predict pressure
            pressure_pred = pressure_regressor.predict(feats_pressure)

            print(f"Position prediction: {pos_pred[0]}, Pressure prediction: {pressure_pred[0]}")

        else:
            # Sleep shortly to avoid busy loop
            time.sleep(0.01)

if __name__ == "__main__":
    main()
