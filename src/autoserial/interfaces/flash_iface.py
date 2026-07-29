"""
Flash sub-interface for a connected device.
Supports multiple firmware formats and tools depending on the detected chip.
"""
import os
import subprocess
import shutil
from pathlib import Path


class FlashInterface:
    """
    Provides firmware flashing support over the connected transport.
    Auto-detects the appropriate flash tool based on file extension and
    device protocol.
    """

    TOOL_MAP = {
        '.bin': 'esptool',   # ESP32 / ESP8266
        '.hex': 'avrdude',   # Arduino / AVR
        '.uf2': 'uf2',       # RP2040 / CircuitPython / UF2 bootloaders
        '.dfu': 'dfu-util',  # STM32 and others
    }

    def __init__(self, device):
        self._device = device

    def flash(self, firmware_path: str, **kwargs) -> bool:
        """
        Flash firmware to the device. Auto-selects the correct tool.
        :param firmware_path: Path to the firmware file (.bin, .hex, .uf2, .dfu).
        :param kwargs: Extra options passed to the underlying flash tool.
        :return: True if flashing succeeded.
        """
        path = Path(firmware_path)
        if not path.exists():
            raise FileNotFoundError(f"Firmware file not found: {firmware_path}")

        ext = path.suffix.lower()
        tool = self.TOOL_MAP.get(ext)

        if not tool:
            raise ValueError(
                f"Unknown firmware format '{ext}'. "
                f"Supported: {list(self.TOOL_MAP.keys())}"
            )

        flasher = getattr(self, f'_flash_{tool.replace("-", "_")}', None)
        if flasher:
            return flasher(path, **kwargs)

        raise RuntimeError(f"No flasher implemented for tool: {tool}")

    def _flash_esptool(self, path: Path, baud: int = 460800, **kwargs) -> bool:
        """Flash ESP32/ESP8266 using esptool."""
        if not shutil.which("esptool.py") and not shutil.which("esptool"):
            raise RuntimeError("esptool not found. Install it with: pip install esptool")

        tool = shutil.which("esptool.py") or "esptool"
        cmd = [
            tool,
            "--port", self._device.uri,
            "--baud", str(baud),
            "write_flash", "0x0",
            str(path),
        ]
        print(f"[flash] Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode == 0

    def _flash_avrdude(self, path: Path, mcu: str = "atmega328p", programmer: str = "arduino", baud: int = 115200, **kwargs) -> bool:
        """Flash AVR/Arduino using avrdude."""
        if not shutil.which("avrdude"):
            raise RuntimeError("avrdude not found. Install it with your system package manager.")

        cmd = [
            "avrdude",
            "-v",
            f"-p{mcu}",
            f"-c{programmer}",
            f"-P{self._device.uri}",
            f"-b{baud}",
            "-D",
            f"-Uflash:w:{path}:i",
        ]
        print(f"[flash] Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode == 0

    def _flash_uf2(self, path: Path, **kwargs) -> bool:
        """
        Flash UF2 firmware by copying to the device's mass-storage mount point.
        The device must be in bootloader mode (usually a USB drive named RPI-RP2 or CIRCUITPY).
        """
        import platform

        mount_candidates = []
        system = platform.system()

        if system == "Windows":
            import string
            import ctypes
            drives = [f"{d}:\\" for d in string.ascii_uppercase if ctypes.windll.kernel32.GetDriveTypeW(f"{d}:\\") == 2]
            mount_candidates = drives
        elif system == "Darwin":
            mount_candidates = [str(p) for p in Path("/Volumes").iterdir()]
        else:  # Linux
            mount_candidates = [str(p) for p in Path("/media").rglob("*") if p.is_dir()]

        uf2_names = {"RPI-RP2", "CIRCUITPY", "BOOT", "BOOTLOADER"}
        target_drive = None
        for mount in mount_candidates:
            name = Path(mount).name.upper()
            if any(n in name for n in uf2_names):
                target_drive = Path(mount)
                break

        if not target_drive:
            raise RuntimeError(
                "No UF2 bootloader drive found. Put the device into bootloader mode first "
                "(hold BOOTSEL while plugging in for RP2040)."
            )

        dest = target_drive / path.name
        print(f"[flash] Copying {path} → {dest}")
        shutil.copy2(str(path), str(dest))
        return True

    def _flash_dfu_util(self, path: Path, alt: int = 0, **kwargs) -> bool:
        """Flash DFU firmware using dfu-util."""
        if not shutil.which("dfu-util"):
            raise RuntimeError("dfu-util not found. Install it with your system package manager.")

        cmd = ["dfu-util", "--alt", str(alt), "--download", str(path)]
        print(f"[flash] Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode == 0
