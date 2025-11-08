import socket
import select
import sys


def broadcast(message, sender_socket, sockets_list, clients):
    """
    Send a message to all connected clients except the sender.
    """
    for sock in sockets_list:
        # Skip the server socket itself and the sender
        if sock != sender_socket and sock != server_socket:
            try:
                sock.send(message)
            except:
                # If sending fails, close and remove that socket
                sock.close()
                if sock in sockets_list:
                    sockets_list.remove(sock)
                if sock in clients:
                    del clients[sock]


if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <port>")
    sys.exit(1)

PORT = int(sys.argv[1])

# Create TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Allow address reuse so you can restart the server quickly
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind and listen
server_socket.bind(("0.0.0.0", PORT))
server_socket.listen()

print(f"Server started on port {PORT}. Waiting for connections...")

# List of sockets to watch with select()
sockets_list = [server_socket]

# Map client socket -> address (just for display)
clients = {}

try:
    while True:
        # select() tells us which sockets are ready to be read
        read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

        for notified_socket in read_sockets:
            # New connection
            if notified_socket == server_socket:
            #     This part works without username 
            #     client_socket, client_address = server_socket.accept()
            #     sockets_list.append(client_socket)
            #     clients[client_socket] = client_address
              
                #This part used nikname
                client_socket, client_address = server_socket.accept()
                sockets_list.append(client_socket)
                # First message from new client will be their nickname
                nickname = client_socket.recv(1024).decode().strip()
                clients[client_socket] = nickname
                join_msg = f"[Server] {nickname} joined the chat.\n"
                print(join_msg.strip())
                broadcast(join_msg.encode(), server_socket, sockets_list, clients)


                #join_msg = f"[Server] {client_address[0]}:{client_address[1]} joined the chat.\n"
                #print(join_msg.strip())
                #broadcast(join_msg.encode(), server_socket, sockets_list, clients)

            # Existing client sent a message
            else:
                try:
                    message = notified_socket.recv(1024)
                except:
                    message = b""

                # Empty message = client disconnected
                if not message:
                    # addr = clients.get(notified_socket, ("unknown", 0))
                    # leave_msg = f"[Server] {addr[0]}:{addr[1]} left the chat.\n"
                    nickname = clients.get(notified_socket, "Unknown")
                    leave_msg = f"[Server] {nickname} left the chat.\n"
                    print(leave_msg.strip())

                    if notified_socket in sockets_list:
                        sockets_list.remove(notified_socket)
                    if notified_socket in clients:
                        del clients[notified_socket]
                    notified_socket.close()

                    broadcast(leave_msg.encode(), server_socket, sockets_list, clients)
                    continue
                else:    
                    # Normal message: broadcast to everyone else
                    # addr = clients.get(notified_socket, ("unknown", 0))
                    # text = message.decode(errors="ignore").rstrip()
                    # formatted = f"[{addr[0]}:{addr[1]}] {text}\n"
                    # print(formatted, end="")  # also show on server
                    # broadcast(formatted.encode(), notified_socket, sockets_list, clients)

                    nickname = clients.get(notified_socket, "Unknown")
                    text = message.decode(errors="ignore").rstrip()
                    formatted = f"[{nickname}] {text}\n"
                    print(formatted, end="")
                    broadcast(formatted.encode(), notified_socket, sockets_list, clients)

        # Handle sockets with errors
        for notified_socket in exception_sockets:
            if notified_socket in sockets_list:
                sockets_list.remove(notified_socket)
            if notified_socket in clients:
                del clients[notified_socket]
            notified_socket.close()

except KeyboardInterrupt:
    print("\nShutting down server...")
    for sock in sockets_list:
        sock.close()
    sys.exit(0)
