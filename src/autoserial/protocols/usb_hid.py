import hid
from typing import Any, List, Dict, Optional
from ..base import BaseDevice

class HIDDevice(BaseDevice):
    def __init__(self, uri: str, **kwargs):
        """
        uri: The path of the HID device.
        Alternatively, can pass vendor_id and product_id in kwargs if uri is empty.
        """
        super().__init__(uri=uri, protocol='usb_hid')
        self._kwargs = kwargs
        self._device: Optional[hid.device] = None

    def connect(self) -> None:
        if self._connected:
            return

        self._device = hid.device()
        
        vendor_id = self._kwargs.get('vendor_id')
        product_id = self._kwargs.get('product_id')
        
        if self.uri:
            # Assuming URI is the device path
            self._device.open_path(self.uri.encode('utf-8'))
        elif vendor_id and product_id:
            self._device.open(vendor_id, product_id)
        else:
            raise ValueError("Must provide either uri (path) or vendor_id and product_id.")
            
        self._device.set_nonblocking(0) # block on read
        self._connected = True

    def disconnect(self) -> None:
        self.stop_monitoring()
        if self._device:
            self._device.close()
        self._connected = False
        self._device = None

    def read(self, size: int = 64, timeout: Optional[float] = None) -> Any:
        if not self._connected or not self._device:
            raise RuntimeError("Device is not connected.")
        
        if timeout is not None:
            # hidapi read timeout is in milliseconds
            data = self._device.read(size, timeout_ms=int(timeout * 1000))
        else:
            data = self._device.read(size)
            
        return bytes(data) if data else b''

    def write(self, data: Any) -> int:
        if not self._connected or not self._device:
            raise RuntimeError("Device is not connected.")
        
        if isinstance(data, str):
            data = list(data.encode('utf-8'))
        elif isinstance(data, bytes):
            data = list(data)
            
        # First byte is often the report ID, handled by caller
        return self._device.write(data)

    @classmethod
    def list_devices(cls) -> List[Dict[str, Any]]:
        devices = []
        for d in hid.enumerate():
            devices.append({
                'uri': d['path'].decode('utf-8') if isinstance(d['path'], bytes) else d['path'],
                'vendor_id': d['vendor_id'],
                'product_id': d['product_id'],
                'product_string': d.get('product_string', ''),
                'manufacturer_string': d.get('manufacturer_string', '')
            })
        return devices
