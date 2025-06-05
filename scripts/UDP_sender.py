
import socket

UNITY_IP = "130.229.189.54"  # Use the Quest or Unity PC IP if not running on the same machine
UNITY_PORT = 5052

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("Press keys to send to Unity. Press ESC to quit.")

try:
    while True:
        key = input("Press key to send: ").strip()

        if key.lower() == 'esc':
            print("Exiting...")
            break

        if key:
            message = key[0]  # Just the first character
            sock.sendto(message.encode(), (UNITY_IP, UNITY_PORT))
            print(f"Sent '{message}' to Unity at {UNITY_IP}:{UNITY_PORT}")

except KeyboardInterrupt:
    print("\nStopped by user.")

sock.close()
