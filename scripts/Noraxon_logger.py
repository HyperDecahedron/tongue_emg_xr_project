import numpy as np
import requests
from pynput import keyboard
import time, csv, os
from datetime import datetime
import tkinter as tk
import threading

# Create data directory
save_dir = os.path.join('data', 'Noraxon')
os.makedirs(save_dir, exist_ok=True)

# Output file path
now = datetime.now()
filename = f"6_classes_{now.strftime('%d-%m-hour-%H-min-%M')}.csv"
save_path = os.path.join(save_dir, filename)

# Global list to collect all labeled data
all_data = []
i = 1  # window counter

# Constants
LABEL_KEYS = ['l', 'k', 'f', 'e', 'r', 's', 'n']
SAMPLE_DURATION = 4  # seconds

# --- UI Setup ---
root = tk.Tk()
root.title("Noraxon EMG Logger")
root.configure(bg="white")
canvas = tk.Canvas(root, width=200, height=200, bg="white", highlightthickness=0)
canvas.pack()
label_text = tk.StringVar()
label_display = tk.Label(root, textvariable=label_text, font=("Arial", 16), bg="white")
label_display.pack()

circle = canvas.create_oval(50, 50, 150, 150, fill="red", outline="black")

def set_circle(color, label=None):
    canvas.itemconfig(circle, fill=color)
    if label:
        label_text.set(f"Label: '{label}'")
    else:
        label_text.set("")

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

    # UI feedback
    set_circle("green", label)
    root.update()

    print(f"\nLabel '{label}' pressed. Buffer clear...")
    time.sleep(SAMPLE_DURATION)

    print("Collecting data...")
    samples = get_data()
    if samples:
        for s in samples:
            all_data.append([i, label] + list(s))  # Include window number `i`
        print(f"{i} Collected {len(samples)} samples for label '{label}'.")
        i += 1
    else:
        print("[WARN] No samples collected.")

    # Return UI to idle state
    set_circle("red")
    root.update()

def on_press(key):
    try:
        if key.char in LABEL_KEYS:
            threading.Thread(target=collect_labeled_data, args=(key.char,)).start()
    except AttributeError:
        pass

def on_release(key):
    if key == keyboard.Key.esc:
        print(f"\n[INFO] Saving CSV with {len(all_data)} rows...")
        with open(save_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["window", "label", "ch_1", "ch_2", "ch_3"])  # Updated header
            writer.writerows(all_data)
        print(f"[DONE] Saved annotations to {save_path}")
        root.quit()
        return False

# Start key listener in a thread so it doesn't block tkinter
def start_listener():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

print("Press l = left, k = left-front, f = front, e = right-front, r = right, s = swallow, n = none. ESC to stop.")

listener_thread = threading.Thread(target=start_listener)
listener_thread.daemon = True
listener_thread.start()

# Start the UI loop
root.mainloop()
