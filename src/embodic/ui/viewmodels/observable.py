"""A minimal observable value: view-models set it, Qt views subscribe, tests read ``value``."""

from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class Observable(Generic[T]):
    """Minimal pure-Python observable value for view-models; Qt views subscribe, tests call value directly."""

    def __init__(self, initial: T) -> None:
        self._value = initial
        self._callbacks: list[Callable[[T], None]] = []

    @property
    def value(self) -> T:
        """Return the current value."""
        return self._value

    def subscribe(self, callback: Callable[[T], None]) -> Callable[[], None]:
        """Call ``callback`` with every new value; return the function that unsubscribes it."""
        self._callbacks.append(callback)
        return lambda: self._callbacks.remove(callback)

    def set(self, value: T) -> None:
        """Store a value and notify the subscribers; setting an equal value notifies no one."""
        if value == self._value:
            return
        self._value = value
        for callback in tuple(self._callbacks):
            callback(value)
