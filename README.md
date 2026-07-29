# AUTOserial

`AUTOserial` is a universal, cross-platform Python library that simplifies hardware communication. It abstracts away the specific details of different protocols (UART, SPI, I²C, USB HID, CAN, BLE, TCP/UDP, MQTT) behind a single, consistent API — with namespaced sub-interfaces for serial, GPIO, and firmware flashing.

## Features
- **Unified API**: One `device` object works across all protocols.
- **Sub-interfaces**: Clean namespaced access via `device.serial`, `device.gpio`, `device.flash`.
- **Auto-Detection**: `Device.auto_detect()` and `Device.list()` scan all protocols automatically.
- **Cross-Platform**: Supports Windows, Linux, and macOS.
- **Firmware Flashing**: Auto-selects `esptool`, `avrdude`, `uf2`, or `dfu-util` based on file extension.
- **Silent Mode**: `suppress_errors=True` silences warnings for unavailable protocols.
- **Extensive Protocol Support**: UART, SPI, I²C, USB HID, CAN, BLE, TCP/UDP, MQTT.

## Installation

Install via pip (package name is lowercase):

```bash
pip install autoserial
```

Or with `uv`:

```bash
uv add autoserial
```

*Installs: `pyserial`, `hidapi`, `bleak`, `python-can`, `paho-mqtt`, `pyftdi`.*

---

## Quickstart

```python
from autoserial import Device

# Auto-detect and connect to the first available hardware device
device = Device.auto_detect()

# Get device metadata
print(device.info())
# {'uri': 'COM3', 'protocol': 'uart', 'connected': True, 'platform': 'Windows', ...}

# Serial communication
device.serial.write(b"Hello Hardware!\n")
response = device.serial.read(size=64, timeout=1.0)

# Background serial monitor (prints to stdout)
device.serial.monitor()

# GPIO control
device.gpio.mode(12, "OUTPUT")
device.gpio.high(12)
device.gpio.low(12)
device.gpio.pwm(9, frequency=1000, duty=50)

# Reset the device (DTR toggle on UART, Ctrl-D on others)
device.reset()

# Flash firmware — tool is auto-selected by file extension
device.flash.flash("firmware.bin")   # ESP32  → esptool
device.flash.flash("firmware.hex")   # Arduino → avrdude
device.flash.flash("firmware.uf2")   # RP2040  → USB drag-and-drop
device.flash.flash("firmware.dfu")   # STM32   → dfu-util

device.disconnect()
```

---

## API Reference

### `Device` (Factory class)

| Method | Description |
|---|---|
| `Device.auto_detect(hints, suppress_errors)` | Scan all protocols and connect to the first device found. |
| `Device.auto_connect(hints, suppress_errors)` | Alias for `auto_detect()`. |
| `Device.list(hints, suppress_errors)` | Return a list of all detected devices across protocols. |
| `Device.connect(protocol, uri, **kwargs)` | Explicitly connect to a device by protocol and URI. |

### `device` (Connected device instance)

| Method / Property | Description |
|---|---|
| `device.info()` | Returns a dict with `uri`, `protocol`, `connected`, `platform`, `class`. |
| `device.reset()` | Resets the hardware (DTR toggle on UART, Ctrl-D elsewhere). |
| `device.read(size, timeout)` | Read raw bytes from the transport. |
| `device.write(data)` | Write bytes to the transport. |
| `device.monitor(callback)` | Start background monitoring thread. |
| `device.stop_monitoring()` | Stop the background monitor. |
| `device.serial` | Serial sub-interface. |
| `device.gpio` | GPIO sub-interface. |
| `device.flash` | Flash sub-interface. |

### `device.serial`

| Method | Description |
|---|---|
| `.read(size, timeout)` | Read raw bytes. |
| `.readline(timeout)` | Read until newline. |
| `.write(data)` | Write bytes or string. |
| `.monitor(callback)` | Start background monitor (prints to stdout if no callback). |
| `.stop_monitoring()` | Stop background monitor. |
| `.lines(timeout)` | Generator yielding decoded lines from the device. |

### `device.gpio`

| Method | Description |
|---|---|
| `.mode(pin, direction)` | Set pin mode: `'INPUT'`, `'OUTPUT'`, `'INPUT_PULLUP'`. |
| `.high(pin)` | Set pin HIGH. |
| `.low(pin)` | Set pin LOW. |
| `.toggle(pin)` | Toggle pin state. |
| `.read(pin)` | Read pin state — returns raw response string. |
| `.pwm(pin, frequency, duty)` | Start PWM. `duty` is 0–100 (%). |
| `.pwm_stop(pin)` | Stop PWM on a pin. |

### `device.flash`

| Method | Description |
|---|---|
| `.flash(firmware_path, **kwargs)` | Flash firmware. Tool auto-selected by extension. |

| Extension | Tool | Target |
|---|---|---|
| `.bin` | `esptool` | ESP32 / ESP8266 |
| `.hex` | `avrdude` | Arduino / AVR |
| `.uf2` | USB copy | RP2040 / CircuitPython |
| `.dfu` | `dfu-util` | STM32 and others |

---

## Supported Protocols

| Protocol | Hint | Connection URI Example | Backend |
|---|---|---|---|
| **UART** | `'uart'` | `COM3`, `/dev/ttyUSB0` | `pyserial` |
| **TCP/UDP** | `'network'` | `192.168.1.10:5000` | `socket` |
| **MQTT** | `'mqtt'` | `test.mosquitto.org:1883` | `paho-mqtt` |
| **CAN Bus** | `'can'` | `can0`, `vcan0` | `python-can` |
| **BLE** | `'ble'` | `24:71:89:cc:09:05` | `bleak` |
| **USB HID** | `'usb_hid'` | `/dev/hidraw0` | `hidapi` |
| **SPI** | `'spi'` | `ftdi://ftdi:232h/1` | `pyftdi` |
| **I²C** | `'i2c'` | `ftdi://ftdi:232h/1` | `pyftdi` |

---

## Advanced Usage

### Suppress protocol errors (e.g. Bluetooth off)

```python
devices = Device.list(suppress_errors=True)
device  = Device.auto_detect(suppress_errors=True)
```

### Explicit connection

```python
# UART
device = Device.connect(protocol='uart', uri='COM3', baudrate=115200)

# TCP
device = Device.connect(protocol='network', uri='192.168.1.10:5000', protocol_type='tcp')

# BLE
device = Device.connect(
    protocol='ble',
    uri='24:71:89:cc:09:05',
    rx_char='00002a37-0000-1000-8000-00805f9b34fb',
    tx_char='00002a38-0000-1000-8000-00805f9b34fb',
)

# CAN Bus
device = Device.connect(protocol='can', uri='can0', bustype='socketcan', bitrate=500000)
```

### Context manager (auto disconnect)

```python
with Device.connect(protocol='uart', uri='/dev/ttyUSB0') as device:
    device.serial.write(b"ping\n")
    print(device.serial.readline())
```

### Stream lines from a serial device

```python
device = Device.connect(protocol='uart', uri='COM3')
for line in device.serial.lines(timeout=1.0):
    print(line)
```

---

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request if you'd like to add support for a new hardware protocol or improve existing ones.

## License
MIT
