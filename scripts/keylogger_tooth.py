from pynput import keyboard
import time, csv, os
from datetime import datetime

# Mapping of keys to class labels
key_to_label = {
    '1': 'lci',
    '2': 'lli',
    '3': 'lc',
    '4': 'lp1',
    '5': 'lp2',
    '6': 'lm1',
    '7': 'lm2',
    '8': 'lm3',
    'a': 'rci',
    's': 'rli',
    'd': 'rc',
    'f': 'rp1',
    'g': 'rp2',
    'h': 'rm1',
    'j': 'rm2',
    'k': 'rm3'
}

log = []

print("Press a mapped key to log. Press ESC to stop.")

# Ensure the save directory exists
save_dir = os.path.join('data', 'annotations')
os.makedirs(save_dir, exist_ok=True)

# Generate filename with current date and hour
now = datetime.now()
filename = f"annotations_{now.strftime('%d-%m-hour-%H-min-%M')}.csv"
save_path = os.path.join(save_dir, filename)

i = 1  # Initialize counter

def on_press(key):
    global i
    try:
        key_char = key.char.lower()
        if key_char in key_to_label:
            label = key_to_label[key_char]
            timestamp = time.time()
            log.append((label, timestamp))
            print(f"{i}: {label.upper()} logged at {timestamp}")
            i += 1
    except AttributeError:
        # Ignore special keys
        pass

def on_release(key):
    if key == keyboard.Key.esc:
        with open(save_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["label", "timestamp"])
            writer.writerows(log)
        print(f"\nSaved annotations to {save_path}")
        return False  # Stop listener

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
