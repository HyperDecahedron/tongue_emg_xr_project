from pynput import keyboard
import time, csv, os
from datetime import datetime

log = []

print("Press l = left, r = right, f = front, n = none. ESC to stop.")

# Ensure the save directory exists
save_dir = os.path.join('data', 'annotations')
os.makedirs(save_dir, exist_ok=True)

# Generate filename with current date and hour, e.g. annotations_2025-06-02_14.csv
now = datetime.now()
filename = f"annotations_{now.strftime('%d-%m-hour-%H-min-%M')}.csv"
save_path = os.path.join(save_dir, filename)

i = 1  # Initialize counter

def on_press(key):
    global i  # Tell Python to use the outer i
    try:
        if key.char in ['l', 'r', 'f', 'n']:
            timestamp = time.time()  # Unix timestamp (seconds since epoch)
            log.append((key.char, timestamp))
            print(f"{i}: {key.char.upper()} logged at {timestamp}")
            i = i + 1  # Increment counter after printing
    except AttributeError:
        # Special keys (like shift, ctrl) don't have .char
        pass

def on_release(key):
    if key == keyboard.Key.esc:
        with open(save_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["label", "timestamp"])
            writer.writerows(log)
        print(f"\nSaved annotations to {save_path}")
        return False  # Stop the listener

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()