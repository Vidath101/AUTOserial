import abc
import platform
from typing import Any, List, Optional, Callable, Dict
import threading
import time

class BaseDevice(abc.ABC):
    """
    Abstract base class for all hardware communication devices.
    Includes namespaced sub-interfaces: device.serial, device.gpio, device.flash
    """

    def __init__(self, uri: str, protocol: str):
        self.uri = uri
        self.protocol = protocol
        self._connected = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_running = False
        self._callbacks: List[Callable[[Any], None]] = []

        # Lazy-loaded sub-interfaces
        self._serial_iface = None
        self._gpio_iface = None
        self._flash_iface = None

    # ------------------------------------------------------------------ #
    # Abstract transport methods (implemented by each protocol class)
    # ------------------------------------------------------------------ #

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

    # ------------------------------------------------------------------ #
    # Sub-interfaces (lazy-loaded properties)
    # ------------------------------------------------------------------ #

    @property
    def serial(self):
        """Serial sub-interface: device.serial.monitor(), .read(), .write(), .lines()"""
        if self._serial_iface is None:
            from .interfaces.serial_iface import SerialInterface
            self._serial_iface = SerialInterface(self)
        return self._serial_iface

    @property
    def gpio(self):
        """GPIO sub-interface: device.gpio.high(pin), .low(pin), .toggle(pin), .read(pin), .pwm(...)"""
        if self._gpio_iface is None:
            from .interfaces.gpio_iface import GPIOInterface
            self._gpio_iface = GPIOInterface(self)
        return self._gpio_iface

    @property
    def flash(self):
        """Flash sub-interface: device.flash('firmware.bin')"""
        if self._flash_iface is None:
            from .interfaces.flash_iface import FlashInterface
            self._flash_iface = FlashInterface(self)
        return self._flash_iface

    # ------------------------------------------------------------------ #
    # High-level device methods
    # ------------------------------------------------------------------ #

    def info(self) -> Dict[str, Any]:
        """Return a dictionary of device metadata."""
        return {
            "uri":        self.uri,
            "protocol":   self.protocol,
            "connected":  self.is_connected,
            "platform":   platform.system(),
            "class":      self.__class__.__name__,
        }

    def reset(self) -> None:
        """
        Send a reset command to the device.
        For serial-based devices this toggles DTR. Subclasses can override for
        protocol-specific resets (e.g. CAN bus-off recovery, BLE reconnect).
        """
        self._reset()

    def _reset(self) -> None:
        """Default reset: send a generic RESET command string over the transport."""
        try:
            self.write(b"\x04")       # Ctrl-D (soft reset in MicroPython REPL)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Monitoring
    # ------------------------------------------------------------------ #

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
                data = self.read(size=1024, timeout=0.1)
                if data:
                    for cb in self._callbacks:
                        try:
                            cb(data)
                        except Exception as e:
                            print(f"Error in callback {cb}: {e}")
            except Exception:
                time.sleep(0.01)

    # ------------------------------------------------------------------ #
    # Context manager & repr
    # ------------------------------------------------------------------ #

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"uri={self.uri!r} "
            f"protocol={self.protocol!r} "
            f"connected={self.is_connected}>"
        )
