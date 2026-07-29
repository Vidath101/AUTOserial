from typing import Any, List, Dict, Optional
from ..base import BaseDevice

# pyftdi dependencies for SPI and I2C
try:
    from pyftdi.spi import SpiController
    from pyftdi.i2c import I2cController
    from pyftdi.usbtools import UsbTools
    PYFTDI_AVAILABLE = True
except ImportError:
    PYFTDI_AVAILABLE = False


class SPIDevice(BaseDevice):
    def __init__(self, uri: str, cs: int = 0, freq: float = 1E6, **kwargs):
        """
        uri: PyFtdi URI (e.g. 'ftdi://ftdi:232h/1')
        cs: Chip select line (0-3)
        freq: SPI frequency in Hz
        """
        super().__init__(uri=uri, protocol='spi')
        self.cs = cs
        self.freq = freq
        self._spi_ctrl = None
        self._spi_port = None

    def connect(self) -> None:
        if not PYFTDI_AVAILABLE:
            raise RuntimeError("pyftdi is required for SPI support")
            
        if self._connected:
            return

        self._spi_ctrl = SpiController()
        self._spi_ctrl.configure(self.uri)
        self._spi_port = self._spi_ctrl.get_port(cs=self.cs, freq=self.freq, mode=0)
        self._connected = True

    def disconnect(self) -> None:
        self.stop_monitoring()
        if self._spi_ctrl:
            self._spi_ctrl.terminate()
        self._connected = False
        self._spi_ctrl = None
        self._spi_port = None

    def read(self, size: int = 1, timeout: Optional[float] = None) -> Any:
        if not self._connected or not self._spi_port:
            raise RuntimeError("Device is not connected.")
        
        return self._spi_port.read(size)

    def write(self, data: Any) -> int:
        if not self._connected or not self._spi_port:
            raise RuntimeError("Device is not connected.")
        
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        self._spi_port.write(data)
        return len(data)

    @classmethod
    def list_devices(cls) -> List[Dict[str, Any]]:
        devices = []
        if PYFTDI_AVAILABLE:
            # Enumerate FTDI devices
            for dev, interfaces in UsbTools.find_all([]):
                # Basic representation
                devices.append({
                    'uri': f"ftdi://{dev.vid:04x}:{dev.pid:04x}/1", # Assuming interface 1
                    'description': dev.description
                })
        return devices


class I2CDevice(BaseDevice):
    def __init__(self, uri: str, address: int, freq: float = 100E3, **kwargs):
        """
        uri: PyFtdi URI (e.g. 'ftdi://ftdi:232h/1')
        address: I2C device address
        freq: I2C frequency in Hz
        """
        super().__init__(uri=uri, protocol='i2c')
        self.address = address
        self.freq = freq
        self._i2c_ctrl = None
        self._i2c_port = None

    def connect(self) -> None:
        if not PYFTDI_AVAILABLE:
            raise RuntimeError("pyftdi is required for I2C support")
            
        if self._connected:
            return

        self._i2c_ctrl = I2cController()
        self._i2c_ctrl.configure(self.uri)
        self._i2c_port = self._i2c_ctrl.get_port(self.address)
        self._connected = True

    def disconnect(self) -> None:
        self.stop_monitoring()
        if self._i2c_ctrl:
            self._i2c_ctrl.terminate()
        self._connected = False
        self._i2c_ctrl = None
        self._i2c_port = None

    def read(self, size: int = 1, timeout: Optional[float] = None) -> Any:
        if not self._connected or not self._i2c_port:
            raise RuntimeError("Device is not connected.")
        
        return self._i2c_port.read(size)

    def write(self, data: Any) -> int:
        if not self._connected or not self._i2c_port:
            raise RuntimeError("Device is not connected.")
        
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        self._i2c_port.write(data)
        return len(data)

    @classmethod
    def list_devices(cls) -> List[Dict[str, Any]]:
        devices = []
        if PYFTDI_AVAILABLE:
            for dev, interfaces in UsbTools.find_all([]):
                devices.append({
                    'uri': f"ftdi://{dev.vid:04x}:{dev.pid:04x}/1",
                    'description': dev.description
                })
        return devices
