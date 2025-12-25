import socket
import threading
from typing import Dict, Optional


HOST = "0.0.0.0"   # Listen on all network interfaces
PORT = 10000
BUFFER_SIZE = 1024


def get_local_ip():
    """Get the local machine's IP address on the network."""
    try:
        # Connect to an external host (doesn't actually send data)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class ChatServer:
    """
    Multi-client TCP chat server.
    Handles connections, message broadcasting, and graceful shutdown.
    """

    def __init__(self, host: str = HOST, port: int = PORT):
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.clients: Dict[socket.socket, str] = {}  # socket -> username
        self.lock = threading.Lock()
        self.running = True

    # ---------- START ----------

    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)

            local_ip = get_local_ip()
            print(f"\n{'='*60}")
            print(f"[SERVER] Listening on {self.host}:{self.port}")
            print(f"[SERVER] Server IP for clients: {local_ip}:{self.port}")
            print(f"[SERVER] Waiting for clients...")
            print(f"{'='*60}\n")

            while self.running:
                client_socket, client_address = self.server_socket.accept()
                print(f"[NEW CONNECTION] {client_address}")

                handler = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                handler.start()

        except KeyboardInterrupt:
            print("\n[SERVER] Shutdown requested by user")

        except Exception as e:
            print(f"[SERVER ERROR] {e}")

        finally:
            self.shutdown()

    # ---------- CLIENT HANDLING ----------

    def _handle_client(self, client_socket: socket.socket, client_address):
        username = None
        try:
            # Welcome + username
            client_socket.send(b"Welcome! Please enter your username")
            username = client_socket.recv(BUFFER_SIZE).decode("utf-8").strip()

            if not username:
                return

            with self.lock:
                self.clients[client_socket] = username

            print(f"[USER JOINED] {username} from {client_address}")
            self.broadcast(f"[SYSTEM] {username} joined the chat", exclude=client_socket)

            # Message loop
            while True:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break

                message = data.decode("utf-8")
                print(f"[{username}] {message}")
                self.broadcast(f"{username}: {message}", exclude=client_socket)

        except Exception as e:
            print(f"[ERROR] {username or 'Unknown'}: {e}")

        finally:
            self._disconnect_client(client_socket)

    # ---------- BROADCAST ----------

    def broadcast(self, message: str, exclude: Optional[socket.socket] = None):
        with self.lock:
            for client in list(self.clients.keys()):
                if client != exclude:
                    try:
                        client.send(message.encode("utf-8"))
                    except:
                        pass

    # ---------- DISCONNECT ----------

    def _disconnect_client(self, client_socket: socket.socket):
        with self.lock:
            username = self.clients.pop(client_socket, None)

        if username:
            print(f"[USER LEFT] {username}")
            self.broadcast(f"[SYSTEM] {username} left the chat")

        try:
            client_socket.close()
        except:
            pass

    # ---------- SHUTDOWN ----------

    def shutdown(self):
        self.running = False

        with self.lock:
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()

        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        print("[SERVER] Shutdown complete.")


if __name__ == "__main__":
    server = ChatServer()
    server.start()
