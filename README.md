# AUTOserial

`AUTOserial` is a universal, cross-platform Python library that simplifies hardware communication. It abstracts away the specific details of different protocols (UART, SPI, I²C, USB HID, CAN, BLE, TCP/UDP, MQTT) behind a single, consistent API. 

With `AUTOserial`, you can easily list available devices, auto-connect to them, and read/write data without worrying about the underlying protocol implementations.

## Features
- **Unified API**: One `read()`, `write()`, and `monitor()` interface for all protocols.
- **Cross-Platform**: Supports Windows, Linux, and macOS.
- **Auto-Detection**: Smart `list()` and `auto_connect()` capabilities to find hardware on the fly.
- **Extensive Protocol Support**: UART, SPI, I²C, USB HID, CAN, Bluetooth Low Energy (BLE), TCP/UDP, and MQTT.

## Installation

You can install `AUTOserial` via pip (note the package name is lowercase):

```bash
pip install autoserial
```

Or, if you're using `uv`:

```bash
uv add autoserial
```

*Note: Since this library covers a wide range of protocols, it will install dependencies like `pyserial`, `hidapi`, `bleak`, `python-can`, `paho-mqtt`, and `pyftdi`.*

## Quickstart

The easiest way to get started is by letting `AUTOserial` auto-detect and connect to your device.

```python
from autoserial import Device
import time

def on_data_received(data):
    print(f"Received data: {data}")

# List all discovered devices on all protocols
print("Available devices:", Device.list())

# Automatically connect to the first available UART or USB HID device
device = Device.auto_connect(hints=['uart', 'usb_hid'])

if device:
    print(f"Connected to {device.protocol} device at {device.uri}")
    
    # Write data
    device.write(b"Hello Hardware!\n")
    
    # Read data directly
    response = device.read(size=64, timeout=1.0)
    print("Response:", response)

    # Or start background monitoring
    device.monitor(on_data_received)
    time.sleep(5)
    device.stop_monitoring()
    
    # Clean up
    device.disconnect()
else:
    print("No devices found.")
```

## Supported Protocols

| Protocol | Hint | Connection URI Example | Backend Library |
|---|---|---|---|
| **UART** | `'uart'` | `COM3`, `/dev/ttyUSB0` | `pyserial` |
| **TCP/UDP** | `'network'` | `192.168.1.10:5000` | `socket` |
| **MQTT** | `'mqtt'` | `test.mosquitto.org:1883` | `paho-mqtt` |
| **CAN Bus** | `'can'` | `can0`, `vcan0` | `python-can` |
| **BLE** | `'ble'` | `24:71:89:cc:09:05` | `bleak` |
| **USB HID** | `'usb_hid'` | `/dev/hidraw0` | `hidapi` |
| **SPI** | `'spi'` | `ftdi://ftdi:232h/1` | `pyftdi` |
| **I²C** | `'i2c'` | `ftdi://ftdi:232h/1` | `pyftdi` |

## Advanced Usage

If you don't want to use `auto_connect()`, you can explicitly create a device for a specific protocol.

### Silencing Errors

By default, `AUTOserial` will log warnings when a protocol fails to scan (e.g. Bluetooth is turned off). You can suppress all these logs with `suppress_errors=True`:

```python
from autoserial import Device

# No warnings or errors will be printed, even if BLE is off or CAN is not available
devices = Device.list(suppress_errors=True)
device  = Device.auto_connect(suppress_errors=True)
```

### Connecting to a CAN bus

```python
from autoserial import Device

# Connect to a CAN interface (e.g. socketcan)
can_device = Device.connect(protocol='can', uri='can0', bustype='socketcan', bitrate=500000)
can_device.write(b"\x01\x02\x03") 
msg = can_device.read(timeout=2.0)
print(msg)
can_device.disconnect()
```

### Connecting to a BLE Device

```python
from autoserial import Device

ble_device = Device.connect(
    protocol='ble', 
    uri='24:71:89:cc:09:05', # MAC address or UUID
    rx_char='00002a37-0000-1000-8000-00805f9b34fb',
    tx_char='00002a38-0000-1000-8000-00805f9b34fb'
)

ble_device.write(b"Start")
print(ble_device.read(timeout=5.0))
ble_device.disconnect()
```

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request if you'd like to add support for a new hardware protocol or improve existing ones.

## License
MIT
