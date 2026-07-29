import abc
from typing import Any, List, Optional, Callable
import threading
import time

class BaseDevice(abc.ABC):
    """
    Abstract base class for all hardware communication devices.
    """

    def __init__(self, uri: str, protocol: str):
        self.uri = uri
        self.protocol = protocol
        self._connected = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_running = False
        self._callbacks: List[Callable[[Any], None]] = []

    @abc.abstractmethod
    def connect(self) -> None:
        """Establish connection to the hardware."""
        pass

    @abc.abstractmethod
    def disconnect(self) -> None:
        """Close connection to the hardware."""
        pass

    @abc.abstractmethod
    def read(self, size: int = 1, timeout: Optional[float] = None) -> Any:
        """Read data from the hardware."""
        pass

    @abc.abstractmethod
    def write(self, data: Any) -> int:
        """Write data to the hardware. Returns number of bytes/items written."""
        pass

    @property
    def is_connected(self) -> bool:
        return self._connected

    def add_callback(self, callback: Callable[[Any], None]) -> None:
        """Add a callback to be called when new data arrives during monitoring."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[Any], None]) -> None:
        """Remove a previously added callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def monitor(self, callback: Optional[Callable[[Any], None]] = None) -> None:
        """
        Start monitoring for incoming data in a background thread.
        If a callback is provided, it will be called with the received data.
        """
        if self._monitor_running:
            return

        if callback:
            self.add_callback(callback)

        self._monitor_running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop the background monitoring thread."""
        self._monitor_running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
        self._monitor_thread = None

    def _monitor_loop(self) -> None:
        """Background loop to read data and dispatch to callbacks."""
        while self._monitor_running and self.is_connected:
            try:
                # Use a short timeout so we can exit the loop cleanly
                data = self.read(size=1024, timeout=0.1)
                if data:
                    for cb in self._callbacks:
                        try:
                            cb(data)
                        except Exception as e:
                            print(f"Error in callback {cb}: {e}")
            except Exception as e:
                # Some read timeout exceptions are expected, ignore them.
                # In a full implementation, we'd filter specific TimeoutErrors
                time.sleep(0.01)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} uri={self.uri} protocol={self.protocol} connected={self.is_connected}>"
