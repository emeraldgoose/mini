import socket
import threading
import time

import pytest

from server import Server


HOST = "127.0.0.1"


@pytest.fixture
def server():
    """
    Start a Mini-Memcached server on a random port.
    """
    server = Server(host=HOST, port=0)

    thread = threading.Thread(
        target=server.start,
        daemon=True,
    )
    thread.start()

    # Server.start()에서 bind가 끝날 때까지 잠시 기다린다.
    while server.port == 0:
        time.sleep(0.01)

    yield server


def send_command(port, command):
    """
    Send one or more raw Memcached protocol commands
    and return the response.
    """
    with socket.create_connection((HOST, port), timeout=2) as client:
        client.sendall(command)
        return client.recv(4096)


def test_set_and_get(server):
    response = send_command(
        server.port,
        b"set foo 0 60 5\r\n"
        b"hello\r\n"
        b"get foo\r\n",
    )

    assert b"STORED\r\n" in response
    assert b"VALUE foo 0 5\r\n" in response
    assert b"hello\r\n" in response
    assert response.endswith(b"END\r\n")


def test_get_missing_key(server):
    response = send_command(
        server.port,
        b"get missing\r\n",
    )

    assert response == b"END\r\n"


def test_delete(server):
    response = send_command(
        server.port,
        b"set foo 0 60 5\r\n"
        b"hello\r\n"
        b"delete foo\r\n",
    )

    assert b"STORED\r\n" in response
    assert b"DELETED\r\n" in response


def test_delete_missing_key(server):
    response = send_command(
        server.port,
        b"delete missing\r\n",
    )

    assert response == b"NOT_FOUND\r\n"


def test_ttl(server):
    response = send_command(
        server.port,
        b"set foo 0 1 5\r\n"
        b"hello\r\n"
        b"get foo\r\n",
    )

    assert b"VALUE foo 0 5\r\n" in response

    time.sleep(1.1)

    response = send_command(
        server.port,
        b"get foo\r\n",
    )

    assert response == b"END\r\n"
