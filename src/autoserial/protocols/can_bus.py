import can
from typing import Any, List, Dict, Optional
from ..base import BaseDevice

class CANDevice(BaseDevice):
    def __init__(self, uri: str, bustype: str = 'socketcan', bitrate: int = 500000, **kwargs):
        """
        uri: The channel to use (e.g., 'can0', 'vcan0')
        bustype: Type of interface ('socketcan', 'ixxat', 'pcan', 'slcan', etc.)
        """
        super().__init__(uri=uri, protocol='can')
        self.bustype = bustype
        self.bitrate = bitrate
        self._kwargs = kwargs
        self._bus: Optional[can.BusABC] = None

    def connect(self) -> None:
        if self._connected:
            return

        self._bus = can.Bus(
            channel=self.uri,
            interface=self.bustype,
            bitrate=self.bitrate,
            **self._kwargs
        )
        self._connected = True

    def disconnect(self) -> None:
        self.stop_monitoring()
        if self._bus:
            self._bus.shutdown()
        self._connected = False
        self._bus = None

    def read(self, size: int = 1, timeout: Optional[float] = None) -> Any:
        # Size parameter is often irrelevant for CAN messages, as we read frame by frame
        if not self._connected or not self._bus:
            raise RuntimeError("Device is not connected.")
        
        # In python-can, timeout defaults to blocking (None)
        msg = self._bus.recv(timeout=timeout)
        return msg

    def write(self, data: Any) -> int:
        if not self._connected or not self._bus:
            raise RuntimeError("Device is not connected.")
        
        if not isinstance(data, can.Message):
            # Try to build a generic CAN message if just raw bytes are passed
            # A real implementation might require passing Arbitration ID as kwargs
            data = can.Message(
                arbitration_id=self._kwargs.get('tx_arbitration_id', 0x123),
                data=data,
                is_extended_id=False
            )
            
        self._bus.send(data)
        return len(data.data)

    @classmethod
    def list_devices(cls) -> List[Dict[str, Any]]:
        devices = []
        # Python-can doesn't have a universal `list_interfaces` command that works everywhere.
        # This is interface specific, we can try to return virtual interfaces or rely on OS-specific commands.
        # For a universal library, we'll return an empty list or try specific backends.
        try:
            # E.g., for vector or other specific hardware we could probe
            pass
        except Exception:
            pass
            
        return devices
