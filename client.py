import socket
import select
import sys

if len(sys.argv) != 3:
    print(f"Usage: python {sys.argv[0]} <host> <port>")
    sys.exit(1)

HOST = sys.argv[1]
PORT = int(sys.argv[2])

# Create TCP/IP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client_socket.connect((HOST, PORT))
except Exception as e:
    print(f"Could not connect to {HOST}:{PORT} -> {e}")
    sys.exit(1)

print(f"Connected to chat server at {HOST}:{PORT}")
print("Type your message and press Enter to send. Ctrl+C or Ctrl+D to quit.\n")

try:
    while True:
        # We watch two things:
        # 1. sys.stdin -> what the user types
        # 2. client_socket -> what the server sends
        sockets_list = [sys.stdin, client_socket]

        read_sockets, _, _ = select.select(sockets_list, [], [])

        for notified_socket in read_sockets:
            # Incoming message from server
            if notified_socket == client_socket:
                message = client_socket.recv(1024)

                if not message:
                    print("\nDisconnected from server.")
                    client_socket.close()
                    sys.exit(0)

                # Print message as-is (server already formatted)
                sys.stdout.write(message.decode(errors="ignore"))
                sys.stdout.flush()

            # User typed something
            else:
                # Read one line from terminal
                message = sys.stdin.readline()

                # If empty (Ctrl+D), exit
                if not message:
                    print("\nClosing connection.")
                    client_socket.close()
                    sys.exit(0)

                # Send to server
                client_socket.send(message.encode())

except KeyboardInterrupt:
    print("\nClosing connection.")
    client_socket.close()
    sys.exit(0)
