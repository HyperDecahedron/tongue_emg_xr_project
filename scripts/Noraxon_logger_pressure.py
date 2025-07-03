import numpy as np
import requests
from pynput import keyboard
import time, csv, os
from datetime import datetime
import threading

# Create data directory
save_dir = os.path.join('data', 'Noraxon')
os.makedirs(save_dir, exist_ok=True)

# Output file path
now = datetime.now()
filename = f"pressure_{now.strftime('%d-%m-hour-%H-min-%M')}.csv"
save_path = os.path.join(save_dir, filename)

# Global list to collect all labeled data
all_data = []
i = 1  # window counter
SAMPLE_DURATION = 3  # seconds
current_class_label = "l0"

# --- Data Acquisition ---
def get_data():
    """Fetch EMG data from Noraxon HTTP API"""
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
        print(f"An error occurred: {e}")
        return []

def collect_labeled_data(label):
    global i

    _ = get_data()  # Clear buffer

    print(f"\nLabel '{label}' triggered. Buffer cleared...")
    time.sleep(SAMPLE_DURATION)

    samples = get_data()
    if samples:
        for s in samples:
            all_data.append([i, label] + list(s))  # Include window number `i`
        print(f"Window {i}: Collected {len(samples)} samples for label '{label}'.")
        i += 1
    else:
        print("[WARN] No samples collected.")

def on_press(key):
    global current_class_label

    try:
        key_char = key.char.lower()

        if key_char == 'q':
            # Use current class label
            threading.Thread(target=collect_labeled_data, args=(current_class_label,)).start()

        elif key_char == 'p':
            # Ask for new class name in terminal
            new_label = input("\nEnter new class label (e.g., r100, r50): ").strip()
            if new_label:
                current_class_label = new_label
                print(f"[INFO] Class label changed to: '{current_class_label}'")

        else:
            # Any other key uses current label
            threading.Thread(target=collect_labeled_data, args=(current_class_label,)).start()

    except AttributeError:
        pass


def on_release(key):
    if key == keyboard.Key.esc:
        print(f"\n[INFO] Saving CSV with {len(all_data)} rows...")
        with open(save_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["window", "label", "ch_1", "ch_2", "ch_3"])
            writer.writerows(all_data)
        print(f"[DONE] Saved annotations to {save_path}")
        return False

# Start key listener
def start_listener():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

print("Objective: 10 samples/class. Total: 120")
print("Press Q = 'l0' class, P = change class via terminal, other keys = current class. ESC to stop.")

listener_thread = threading.Thread(target=start_listener)
listener_thread.daemon = True
listener_thread.start()

# Keep main thread alive
while listener_thread.is_alive():
    time.sleep(0.1)
