"""REQ-N-17 (V3-01 gap N-17): the commit suite runs with connections refused, so a run-time connection fails its test.

The guard is the autouse fixture `_no_network` of `tests/conftest.py`.
"""

import socket

import pytest

pytestmark = pytest.mark.req("REQ-N-17")


def test_n17_a_connect_to_a_local_port_is_refused_by_the_guard_not_by_the_network():
    """Catches a suite without the guard: there the call would end in ConnectionRefusedError (or a real connection)."""
    with socket.socket() as sock, pytest.raises(AssertionError, match="network connection attempted"):
        sock.connect(("127.0.0.1", 9))


def test_n17_create_connection_is_refused_by_the_guard():
    """Catches a guard that patches `connect` only, which `socket.create_connection` callers would bypass."""
    with pytest.raises(AssertionError, match="network connection attempted"):
        socket.create_connection(("127.0.0.1", 9), timeout=0.1)


def test_n17_local_socket_pairs_still_work():
    """Catches a guard so broad that it breaks in-process IPC, which a Qt or subprocess helper may use."""
    left, right = socket.socketpair()
    with left, right:
        left.sendall(b"ping")
        assert right.recv(4) == b"ping"


def test_n17_a_listen_and_connect_socketpair_works_under_the_guard(monkeypatch):
    """Catches a guard that refuses the loopback connect inside socket.socketpair, as CPython builds it on Windows.

    There `socket.socketpair` is `_fallback_socketpair` (Lib/socket.py): listen on 127.0.0.1, connect to that port,
    accept. Linux uses the native call, so this test binds the fallback by hand to run the Windows code path.
    """
    monkeypatch.setattr(socket, "socketpair", socket._fallback_socketpair)
    left, right = socket.socketpair()
    with left, right:
        left.sendall(b"ping")
        assert right.recv(4) == b"ping"
        right.sendall(b"pong")
        assert left.recv(4) == b"pong"


def test_n17_a_direct_connect_to_a_listening_loopback_port_is_still_refused():
    """Catches a guard that admits loopback in general: here a listener is up, so an unguarded connect would succeed."""
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        with socket.socket() as sock, pytest.raises(AssertionError, match="network connection attempted"):
            sock.connect(listener.getsockname())
