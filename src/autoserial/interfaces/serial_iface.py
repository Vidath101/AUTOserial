"""
Serial sub-interface for a connected device.
Exposes read, write, monitor, and line-by-line iteration over the serial stream.
"""
import threading
from typing import Optional, Callable, Any, Iterator


class SerialInterface:
    def __init__(self, device):
        self._device = device

    def read(self, size: int = 1, timeout: Optional[float] = None) -> bytes:
        """Read raw bytes from the device."""
        return self._device.read(size=size, timeout=timeout)

    def readline(self, timeout: Optional[float] = 1.0) -> bytes:
        """Read until newline or timeout."""
        buf = b""
        while True:
            ch = self._device.read(size=1, timeout=timeout)
            if not ch or ch == b"\n":
                break
            buf += ch
        return buf

    def write(self, data: Any) -> int:
        """Write data to the device."""
        return self._device.write(data)

    def monitor(self, callback: Optional[Callable[[bytes], None]] = None) -> None:
        """
        Start background monitoring. Prints data to stdout if no callback given.
        """
        def _default_print(data):
            try:
                print(data.decode("utf-8", errors="replace"), end="", flush=True)
            except Exception:
                print(data)

        self._device.monitor(callback or _default_print)

    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self._device.stop_monitoring()

    def lines(self, timeout: Optional[float] = 1.0) -> Iterator[str]:
        """Generator that yields lines from the device as strings."""
        while self._device.is_connected:
            line = self.readline(timeout=timeout)
            if line:
                yield line.decode("utf-8", errors="replace").strip()
