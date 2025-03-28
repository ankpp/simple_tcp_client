import logging

from signal import signal
from signal import SIGINT
from signal import SIGTERM
from socket import AF_INET
from socket import SOCK_STREAM
from socket import SOL_SOCKET
from socket import SO_REUSEADDR
from socket import socket
from threading import Thread
from time import strftime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(funcName)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class TCPServer:
    """TCP Server implementation. Supports up to 5 connections."""

    def __init__(
            self,
            host='127.0.0.1',
            port=5000,
            max_connections=5,
            buffer_size=1024,
            timeout=None
    ):
        """Server initialization.

        Args:
            host: IP address to bind to
            port: Port to listen on
            max_connections: Maximum number of connections
            buffer_size: Receive buffer size
            timeout: Timeout in seconds (None for no timeout)
        """
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.buffer_size = buffer_size
        self.timeout = timeout
        self.server = None
        self.running = False
        self.clients = []
        self.client_threads = []

    def start(self):
        try:
            # Creation of the socket allowing reuse of the address
            self.server = socket(AF_INET, SOCK_STREAM)
            self.server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            if self.timeout is not None:
                self.server.settimeout(self.timeout)
            self.server.bind((self.host, self.port))
            self.server.listen(self.max_connections)
            self.running = True
            logger.info(f"Server started {self.host}:{self.port}")

            # Handling of special signals, interruptions and termination
            signal(SIGINT, self._signal_handler)
            signal(SIGTERM, self._signal_handler)

            # Main loop
            while self.running:
                try:
                    # Set up incoming connections
                    client_connection, client_addr = self.server.accept()
                    logger.info(f"New connection from {client_addr[0]}:{client_addr[1]}")
                    self.clients.append(client_connection)  # Enqueue client

                    # New client is assigned its own thread (daemonized)
                    client_thread = Thread(
                        target=self._handle_client,
                        args=(client_connection, client_addr),
                        daemon=True
                    )
                    self.client_threads.append(client_thread)
                    client_thread.start()
                except socket.timeout:
                    continue  # do nothing but keep trying
                except Exception as e:
                    if self.running:
                        logger.error(f"Error accepting connection: {e}")

        except Exception as e:
            logger.error(f"Server initialization error: {e}")
            self.stop()

    def _handle_client(self, client_socket, address):
        """Communication with client.

        Args:
            client_socket: The client's socket object
            address: The client's address (ip, port)
        """
        try:
            while self.running:
                data = client_socket.recv(self.buffer_size)

                if not data:
                    logger.info(f"Client {address[0]}:{address[1]} disconnected")
                    break

                message = data.decode('utf-8').strip()
                logger.info(f"Received from {address[0]}:{address[1]}: {message}")
                if message.upper() == 'DESCONEXION':
                    response = "DISCONNECTED!"
                    client_socket.sendall(response.encode('utf-8'))
                    break
                else:
                    # Echo the message in uppercase
                    response = f"{message.upper()} CLIENTE"
                    client_socket.sendall(response.encode('utf-8'))

        except ConnectionResetError:
            logger.info(f"Connection reset by client {address[0]}:{address[1]}")
        except ConnectionAbortedError:
            logger.info(f"Connection aborted by client {address[0]}:{address[1]}")
        except socket.timeout:
            logger.info(f"Connection to {address[0]}:{address[1]} timed out")
        except Exception as e:
            logger.error(f"Error handling client {address[0]}:{address[1]}: {e}")
        finally:  # Clean up
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            client_socket.close()

    def _signal_handler(self, sig, frame) -> None:
        """Handle signals."""
        logger.info(f"Signal {sig} received, shutting down...")
        self.stop()

    def stop(self) -> None:
        """Stop the server and clean up resources."""
        logger.info("Shutting down server...")
        self.running = False
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        self.clients.clear()

        # Close server socket
        if self.server:
            try:
                self.server.close()
            except:
                pass

        logger.info("Server shutdown complete")

    def broadcast(self, message: str) -> None:
        """Send a message to all connected clients.

        Args:
            message: The message to broadcast
        """
        encoded_message = message.encode('utf-8')
        for client in self.clients[:]:
            try:
                client.sendall(encoded_message)
            except:
                pass


if __name__ == "__main__":
    server = TCPServer(host='127.0.0.1', port=5000, timeout=None)

    try:
        server.start()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
