import importlib
import logging
from typing import List, Optional, Type, Dict, Any
from .base import BaseDevice

logger = logging.getLogger(__name__)

class Device:
    """
    Factory and utility class for detecting and connecting to hardware devices.
    """

    # We will dynamically load protocols to avoid failing if a dependency is missing
    _SUPPORTED_PROTOCOLS = {
        'uart': 'autoserial.protocols.uart.UARTDevice',
        'network': 'autoserial.protocols.network.NetworkDevice',
        'mqtt': 'autoserial.protocols.mqtt.MQTTDevice',
        'can': 'autoserial.protocols.can_bus.CANDevice',
        'ble': 'autoserial.protocols.ble.BLEDevice',
        'usb_hid': 'autoserial.protocols.usb_hid.HIDDevice',
        'spi': 'autoserial.protocols.spi_i2c.SPIDevice',
        'i2c': 'autoserial.protocols.spi_i2c.I2CDevice',
    }

    _loaded_classes: Dict[str, Type[BaseDevice]] = {}

    @classmethod
    def _load_protocol(cls, name: str) -> Optional[Type[BaseDevice]]:
        if name in cls._loaded_classes:
            return cls._loaded_classes[name]
        
        if name not in cls._SUPPORTED_PROTOCOLS:
            return None

        module_path, class_name = cls._SUPPORTED_PROTOCOLS[name].rsplit('.', 1)
        try:
            module = importlib.import_module(module_path)
            device_class = getattr(module, class_name)
            cls._loaded_classes[name] = device_class
            return device_class
        except ImportError as e:
            logger.debug(f"Protocol '{name}' could not be loaded: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading protocol '{name}': {e}")
            return None

    @classmethod
    def list(cls, hints: Optional[List[str]] = None, suppress_errors: bool = False) -> List[Dict[str, Any]]:
        """
        List all detected devices.
        :param hints: List of protocol names to restrict the search (e.g., ['uart', 'ble']).
        :param suppress_errors: If True, suppresses warning logs when a protocol fails to list devices.
        :return: A list of dictionaries containing device info (e.g., {'protocol': 'uart', 'uri': 'COM3', 'description': '...'}).
        """
        protocols_to_check = hints if hints else list(cls._SUPPORTED_PROTOCOLS.keys())
        
        detected_devices = []
        for protocol in protocols_to_check:
            device_class = cls._load_protocol(protocol)
            if device_class and hasattr(device_class, 'list_devices'):
                try:
                    devices = device_class.list_devices()
                    for d in devices:
                        d['protocol'] = protocol
                        detected_devices.append(d)
                except Exception as e:
                    if not suppress_errors:
                        logger.warning(f"Error listing devices for protocol '{protocol}': {e}")

        return detected_devices

    @classmethod
    def auto_connect(cls, hints: Optional[List[str]] = None, suppress_errors: bool = False) -> Optional[BaseDevice]:
        """
        Smart detection mechanism to scan and automatically connect to the first available device.
        :param hints: List of protocol names to restrict the search.
        :param suppress_errors: If True, suppresses warning/error logs during the process.
        :return: Connected BaseDevice instance, or None if no device found.
        """
        available_devices = cls.list(hints=hints, suppress_errors=suppress_errors)
        
        if not available_devices:
            if not suppress_errors:
                logger.info("No devices detected.")
            return None

        # Just pick the first one and connect
        target_info = available_devices[0]
        protocol = target_info['protocol']
        uri = target_info['uri']

        if not suppress_errors:
            logger.info(f"Auto-connecting to {protocol} device at {uri}")
            
        device_class = cls._load_protocol(protocol)
        
        if device_class:
            device = device_class(uri=uri)
            try:
                device.connect()
                return device
            except Exception as e:
                if not suppress_errors:
                    logger.error(f"Failed to connect to {uri}: {e}")
                
        return None

    @classmethod
    def connect(cls, protocol: str, uri: str, **kwargs) -> BaseDevice:
        """
        Explicitly connect to a device.
        :param protocol: Protocol name (e.g., 'uart').
        :param uri: Connection URI (e.g., 'COM3', '192.168.1.10:5000').
        :param kwargs: Additional arguments for the protocol class.
        """
        device_class = cls._load_protocol(protocol)
        if not device_class:
            raise ValueError(f"Protocol '{protocol}' is not supported or its dependencies are not installed.")
        
        device = device_class(uri=uri, **kwargs)
        device.connect()
        return device

    @classmethod
    def auto_detect(cls, hints: Optional[List[str]] = None, suppress_errors: bool = True) -> Optional[BaseDevice]:
        """
        Alias for auto_connect(). Scans all protocols and connects to the first available device.
        :param hints: Limit search to specific protocols (e.g., ['uart', 'ble']).
        :param suppress_errors: Suppress warnings for unavailable protocols (default: True).
        """
        return cls.auto_connect(hints=hints, suppress_errors=suppress_errors)
