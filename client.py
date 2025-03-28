import sys

from socket import AF_INET
from socket import SOCK_STREAM
from socket import socket
from threading import Thread
from time import sleep


class TCPClient(Thread):
    def __init__(self, client: socket, **kw):
        super(TCPClient, self).__init__(**kw)
        self._client = client

    def run(self) -> None:
        try:
            while True:
                # Receive data
                data = self._client.recv(1024)
                if not data:
                    print("Server closed the connection")
                    break

                # Print received message
                print(f"Received: {data.decode('utf-8')}")
        except ConnectionResetError:
            print("Server Reset connection")
        except Exception as e:
            print(f"Something went wrong while receiving incoming message: {e}")
        finally:
            self._client.close()
            print("Connection closed")
            sys.exit(0)


def main() -> None:
    HOST = '127.0.0.1'
    PORT = 5000

    try:
        # Create connection to server using socket
        client = socket(AF_INET, SOCK_STREAM)
        print(f"Connecting to {HOST}:{PORT}...")
        client.connect((HOST, PORT))
        print("Connected")

        client_receiver = TCPClient(client)
        client_receiver.start()

        # Sending messages in an endless loop
        print("Enter your message or type 'DESCONEXION' to quit")
        while True:
            message = input()
            if not message:
                continue
            client.sendall(message.encode('utf-8'))

            if message.lower() == 'DESCONEXION':
                sleep(0.5)
                break

    except ConnectionRefusedError:
        print("Connection refused. Make sure the server is running.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            client.close()
        except:
            pass
        print("Client terminated")


if __name__ == "__main__":
    main()
