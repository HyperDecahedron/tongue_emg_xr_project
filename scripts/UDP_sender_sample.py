
import socket

UNITY_IP = "192.168.1.40"  # Use the Quest or Unity PC IP if not running on the same machine
UNITY_PORT = 5052

pressure = [40,0,0]

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

            message = f"{message},{pressure[0]},{pressure[1]},{pressure[2]}"
            try:
                sock.sendto(message.encode('utf-8'), (UNITY_IP, UNITY_PORT))
            except Exception as e:
                print(f"Error sending UDP message: {e}")

except KeyboardInterrupt:
    print("\nStopped by user.")

sock.close()
