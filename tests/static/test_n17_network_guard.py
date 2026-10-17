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
