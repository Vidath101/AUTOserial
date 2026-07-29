import serial
import serial.tools.list_ports
from typing import Any, List, Dict, Optional
from ..base import BaseDevice

class UARTDevice(BaseDevice):
    def __init__(self, uri: str, baudrate: int = 115200, **kwargs):
        super().__init__(uri=uri, protocol='uart')
        self.baudrate = baudrate
        self._kwargs = kwargs
        self._serial: Optional[serial.Serial] = None

    def connect(self) -> None:
        if self._connected:
            return
        
        self._serial = serial.Serial(
            port=self.uri,
            baudrate=self.baudrate,
            **self._kwargs
        )
        self._connected = True

    def disconnect(self) -> None:
        self.stop_monitoring()
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._connected = False
        self._serial = None

    def read(self, size: int = 1, timeout: Optional[float] = None) -> Any:
        if not self._connected or not self._serial:
            raise RuntimeError("Device is not connected.")
        
        # Save old timeout, apply new one temporarily
        old_timeout = self._serial.timeout
        self._serial.timeout = timeout
        
        data = self._serial.read(size)
        
        # Restore old timeout
        self._serial.timeout = old_timeout
        return data

    def write(self, data: Any) -> int:
        if not self._connected or not self._serial:
            raise RuntimeError("Device is not connected.")
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        return self._serial.write(data)

    @classmethod
    def list_devices(cls) -> List[Dict[str, Any]]:
        ports = serial.tools.list_ports.comports()
        devices = []
        for port in ports:
            devices.append({
                'uri': port.device,
                'description': port.description,
                'hwid': port.hwid
            })
        return devices
