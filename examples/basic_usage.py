"""
AUTOserial - Basic Usage Example
Demonstrates the full Device API: auto_detect, info, serial, gpio, flash, reset.
"""
import time
from autoserial import Device


# ─────────────────────────────────────────────
# 1. List all available devices across protocols
# ─────────────────────────────────────────────
print("=" * 50)
print("  Available Devices")
print("=" * 50)

devices = Device.list(suppress_errors=True)

if not devices:
    print("  No devices found on any protocol.")
else:
    for d in devices:
        print(f"  [{d['protocol'].upper():8s}] {d.get('product_string') or d['uri']}")

print()

# ─────────────────────────────────────────────
# 2. Auto-detect and connect
# ─────────────────────────────────────────────
print("=" * 50)
print("  Auto Detect & Connect")
print("=" * 50)

device = Device.auto_detect(suppress_errors=True)

if not device:
    print("  No device found. Exiting.")
    raise SystemExit(1)

print(f"  Connected: {device}\n")

# ─────────────────────────────────────────────
# 3. Device info
# ─────────────────────────────────────────────
print("=" * 50)
print("  Device Info")
print("=" * 50)

info = device.info()
for k, v in info.items():
    print(f"  {k:<12}: {v}")
print()

try:
    # ─────────────────────────────────────────────
    # 4. Write & Read via serial sub-interface
    # ─────────────────────────────────────────────
    print("=" * 50)
    print("  Serial Read / Write")
    print("=" * 50)

    device.serial.write(b"Hello Hardware!\n")
    print("  Wrote: b'Hello Hardware!'")

    response = device.serial.read(size=64, timeout=0.5)
    print(f"  Read:  {response!r}")
    print()

    # ─────────────────────────────────────────────
    # 5. Background serial monitoring
    # ─────────────────────────────────────────────
    print("=" * 50)
    print("  Serial Monitor (3 seconds)")
    print("=" * 50)

    def on_data(data):
        try:
            print("  >>", data.decode("utf-8", errors="replace"), end="", flush=True)
        except Exception:
            print("  >>", data)

    device.serial.monitor(on_data)
    time.sleep(3)
    device.serial.stop_monitoring()
    print("\n  Monitor stopped.\n")

    # ─────────────────────────────────────────────
    # 6. GPIO control
    # ─────────────────────────────────────────────
    print("=" * 50)
    print("  GPIO Control")
    print("=" * 50)

    device.gpio.mode(12, "OUTPUT")
    device.gpio.high(12)
    print("  GPIO 12 → HIGH")

    time.sleep(0.5)

    device.gpio.low(12)
    print("  GPIO 12 → LOW")

    device.gpio.pwm(9, frequency=1000, duty=50)
    print("  GPIO 9  → PWM 1kHz 50% duty")

    device.gpio.pwm_stop(9)
    print("  GPIO 9  → PWM stopped\n")

    # ─────────────────────────────────────────────
    # 7. Reset the device
    # ─────────────────────────────────────────────
    print("=" * 50)
    print("  Device Reset")
    print("=" * 50)

    device.reset()
    print("  Reset sent.\n")

    # ─────────────────────────────────────────────
    # 8. Flash firmware  (commented out - needs real firmware file)
    # ─────────────────────────────────────────────
    # print("=" * 50)
    # print("  Flashing Firmware")
    # print("=" * 50)
    #
    # device.flash.flash("firmware.bin")   # ESP32 → uses esptool
    # device.flash.flash("firmware.hex")   # Arduino → uses avrdude
    # device.flash.flash("firmware.uf2")   # RP2040 → drag-and-drop copy
    # device.flash.flash("firmware.dfu")   # STM32 → uses dfu-util

finally:
    device.disconnect()
    print("=" * 50)
    print("  Disconnected. Done.")
    print("=" * 50)
