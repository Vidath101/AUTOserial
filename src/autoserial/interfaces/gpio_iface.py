"""
GPIO sub-interface for a connected device.
Sends standardised GPIO command strings over the underlying transport.
Works great with any firmware that speaks a simple text protocol (e.g. MicroPython REPL,
Arduino Firmata, or a custom command set).
"""
from typing import Optional


class GPIOInterface:
    """
    Provides high-level GPIO control over the connected transport.
    Commands are sent as simple ASCII strings that most embedded firmwares understand.
    For raw/custom protocols you can override the _send() method.
    """

    def __init__(self, device):
        self._device = device

    def _send(self, cmd: str) -> None:
        self._device.write((cmd + "\n").encode("utf-8"))

    def high(self, pin: int) -> None:
        """Set a GPIO pin HIGH."""
        self._send(f"GPIO HIGH {pin}")

    def low(self, pin: int) -> None:
        """Set a GPIO pin LOW."""
        self._send(f"GPIO LOW {pin}")

    def toggle(self, pin: int) -> None:
        """Toggle a GPIO pin."""
        self._send(f"GPIO TOGGLE {pin}")

    def read(self, pin: int) -> Optional[str]:
        """Read the state of a GPIO pin. Returns the raw response string."""
        self._send(f"GPIO READ {pin}")
        response = self._device.read(size=64, timeout=1.0)
        if response:
            return response.decode("utf-8", errors="replace").strip()
        return None

    def pwm(self, pin: int, frequency: int, duty: int) -> None:
        """Start PWM on a pin. duty is 0-100 (percent)."""
        self._send(f"PWM {pin} {frequency} {duty}")

    def pwm_stop(self, pin: int) -> None:
        """Stop PWM on a pin."""
        self._send(f"PWM STOP {pin}")

    def mode(self, pin: int, direction: str = "OUTPUT") -> None:
        """Set pin mode: 'INPUT', 'OUTPUT', 'INPUT_PULLUP'."""
        self._send(f"GPIO MODE {pin} {direction.upper()}")
