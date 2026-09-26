import socket
import threading

from protocol import (
    ProtocolParser,
    ProtocolError,
    GetCommand,
    SetCommand,
    DeleteCommand,
    ResponseBuilder
)

from store import Store
from connection import ConnectionBuffer


HOST = "127.0.0.1"
PORT = 11211
BUFFER_SIZE = 4096


class Server:
    """
        A simple multi-threaded TCP server that implements a basic in-memory key-value store
        using a custom protocol similar to Memcached. It supports GET, SET, and DELETE commands
        with optional expiration times (TTL) for stored items.
        The server listens for incoming connections, parses commands, executes them against
        the store, and sends back appropriate responses.
    """
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port

        self.store = Store()
        self.parser = ProtocolParser()
        self.response_builder = ResponseBuilder()

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:

            server_socket.setsockopt(
                socket.SOL_SOCKET, 
                socket.SO_REUSEADDR, 
                1
            )

            server_socket.bind((self.host, self.port))
            self.port = server_socket.getsockname()[1]
            server_socket.listen()

            print(f"Server listening on {self.host}:{self.port}")

            while True:
                client, addr = server_socket.accept()

                print(f"Connected by {addr}")

                thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client,),
                    daemon=True
                )

                thread.start()

    def handle_client(self, client):
        buffer = ConnectionBuffer()

        with client:
            while True:
                data = client.recv(BUFFER_SIZE)
                
                if not data:
                    break

                command = buffer.feed(data)

                for raw_command in command:
                    try:
                        cmd = self.parser.parse(raw_command)
                        response = self.execute(cmd)
                    
                    except ProtocolError as e:
                        response = f"ERROR: {str(e)}\r\n".encode()

                    except Exception as e:
                        print(f"Internal error: {e}")
                        response = b"ERROR\r\n"

                    client.sendall(response)

    def execute(self, command):
        if isinstance(command, GetCommand):
            item = self.store.get(command.key)
            return self.response_builder.get_response(command.key, item)

        elif isinstance(command, SetCommand):
            self.store.set(command.key, command.value, command.flags, command.ttl)
            return self.response_builder.set_response(True)

        elif isinstance(command, DeleteCommand):
            success = self.store.delete(command.key)
            return self.response_builder.delete_response(success)

        else:
            raise ProtocolError(f"Unknown command type: {type(command)}")
