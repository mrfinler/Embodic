"""REQ-N-17 (V3-01 gap N-17): the commit suite runs with connections refused, so a run-time connection fails its test.

The guard is the autouse fixture `_no_network` of `tests/conftest.py`.
"""

import socket
import types
from collections.abc import Callable

import pytest

pytestmark = pytest.mark.req("REQ-N-17")

SocketPair = Callable[[], tuple[socket.socket, socket.socket]]


def listen_and_connect_pair() -> tuple[socket.socket, socket.socket]:
    """Run the sequence of CPython's pure-Python socketpair: listen on loopback, connect to that port, accept."""
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        client = socket.socket()
        try:
            client.connect(listener.getsockname())
            server, _ = listener.accept()
        except BaseException:
            client.close()
            raise
    return server, client


def native_style_socketpair() -> tuple[socket.socket, socket.socket]:
    """Stand in for the wrapper around the C socketpair, which makes no connect."""
    raise NotImplementedError


def renamed(function: types.FunctionType, name: str) -> types.FunctionType:
    """Return a copy of `function` whose code object carries `name`, as the socket module names its own."""
    code = function.__code__.replace(co_name=name, co_qualname=name)
    return types.FunctionType(code, function.__globals__, name)


@pytest.fixture(params=["3.11.9 on Windows", "3.11.15"])
def socketpair_layout(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> SocketPair:
    """Make the socket module look like one CPython layout and return the function that listens, connects, accepts.

    3.11.9 on Windows has no `_fallback_socketpair`: `socketpair` is itself the fallback. 3.11.15 always defines
    `_fallback_socketpair` and keeps `socketpair` for the native call where there is one.
    """
    if request.param == "3.11.9 on Windows":
        monkeypatch.delattr(socket, "_fallback_socketpair", raising=False)
        fallback = renamed(listen_and_connect_pair, "socketpair")
        monkeypatch.setattr(socket, "socketpair", fallback)
        assert not hasattr(socket, "_fallback_socketpair")
    else:
        fallback = renamed(listen_and_connect_pair, "_fallback_socketpair")
        monkeypatch.setattr(socket, "_fallback_socketpair", fallback, raising=False)
        monkeypatch.setattr(socket, "socketpair", renamed(native_style_socketpair, "socketpair"))
    return fallback


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


def test_n17_every_socketpair_function_of_this_python_works_under_the_guard():
    """Catches a guard that admits the socketpair connect of one CPython layout only.

    Windows builds its pairs with the pure-Python listen-and-connect fallback, which is `socketpair` itself in 3.11.9
    and `_fallback_socketpair` in 3.11.15. This runs whichever functions the running Python has.
    """
    names = [name for name in dir(socket) if name.endswith("socketpair")]
    assert "socketpair" in names
    for name in names:
        left, right = getattr(socket, name)()
        with left, right:
            left.sendall(b"ping")
            assert right.recv(4) == b"ping"
            right.sendall(b"pong")
            assert left.recv(4) == b"pong"


def test_n17_the_listen_and_connect_socketpair_works_under_the_guard_in_each_cpython_layout(socketpair_layout):
    """Catches a guard that names the 3.11.15 fallback: on 3.11.9 it raises AttributeError at every connect."""
    left, right = socketpair_layout()
    with left, right:
        left.sendall(b"ping")
        assert right.recv(4) == b"ping"
        right.sendall(b"pong")
        assert left.recv(4) == b"pong"


def test_n17_a_direct_connect_to_a_listening_loopback_port_is_refused_in_each_cpython_layout(socketpair_layout):
    """Catches a guard that finds the fallback and then admits loopback in general, in either layout."""
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        with socket.socket() as sock, pytest.raises(AssertionError, match="network connection attempted"):
            sock.connect(listener.getsockname())


def test_n17_a_direct_connect_to_a_listening_loopback_port_is_still_refused():
    """Catches a guard that admits loopback in general: here a listener is up, so an unguarded connect would succeed."""
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        with socket.socket() as sock, pytest.raises(AssertionError, match="network connection attempted"):
            sock.connect(listener.getsockname())
