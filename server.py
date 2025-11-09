import socket
import select
import sys
from colorama import Fore, Style, init
import random
init()
nick_to_socket = {}

colors = [Fore.GREEN, Fore.MAGENTA, Fore.YELLOW, Fore.BLUE, Fore.WHITE]
client_colors = {}


def broadcast(message, sender_socket, sockets_list, clients):
    """
    Send a message to all connected clients except the sender.
    """
    for sock in sockets_list:
        if sock != sender_socket and sock != server_socket:
            try:
                sock.send(message)
            except:
                sock.close()
                if sock in sockets_list:
                    sockets_list.remove(sock)
                if sock in clients:
                    del clients[sock]


if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <port>")
    sys.exit(1)

PORT = int(sys.argv[1])
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
                client_socket, client_address = server_socket.accept()
                sockets_list.append(client_socket)
                nickname = client_socket.recv(1024).decode().strip()
                clients[client_socket] = nickname
                nick_to_socket[nickname] = client_socket
                client_colors[client_socket] = random.choice(colors)
                join_msg = f"{Fore.CYAN}[Server]{Style.RESET_ALL} {nickname} joined the chat.\n"
                print(join_msg.strip())
                broadcast(join_msg.encode(), server_socket, sockets_list, clients)

            else:
                try:
                    message = notified_socket.recv(1024)
                except:
                    message = b""

                if not message:
                    nickname = clients.get(notified_socket, "Unknown")
                    leave_msg = f"{Fore.CYAN}[Server]{Style.RESET_ALL} {nickname} left the chat.\n"
                    print(leave_msg.strip())

                    if notified_socket in sockets_list:
                        sockets_list.remove(notified_socket)
                    if notified_socket in clients:
                        del clients[notified_socket]
                    if nickname in nick_to_socket:
                        del nick_to_socket[nickname]
                    notified_socket.close()

                    broadcast(leave_msg.encode(), server_socket, sockets_list, clients)
                    continue
                else:   
                    nickname = clients.get(notified_socket, "Unknown")
                    text = message.decode(errors="ignore").rstrip()
                    if text.startswith("@"):
                        parts = text.split(" ", 1)
                        if len(parts) < 2:
                            notified_socket.send("[Server] Usage for private message: @nickname your message\n".encode())
                        else:
                            target_name = parts[0][1:]  # remove '@'
                            private_text = parts[1]
                            target_socket = nick_to_socket.get(target_name)
                            if target_socket:
                                msg_to_target = f"[whisper from {nickname}] {private_text}\n"
                                target_socket.send(msg_to_target.encode())
                                msg_to_sender = f"[whisper to {target_name}] {private_text}\n"
                                notified_socket.send(msg_to_sender.encode())
                            else:
                                # Target not found
                                error_msg = f"[Server] User '{target_name}' not found.\n"
                                notified_socket.send(error_msg.encode())
                    else:
                        # Normal public message
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
