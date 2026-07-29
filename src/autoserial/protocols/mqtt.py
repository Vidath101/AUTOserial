import paho.mqtt.client as mqtt
import queue
from typing import Any, List, Dict, Optional
from ..base import BaseDevice

class MQTTDevice(BaseDevice):
    def __init__(self, uri: str, topic_pub: str = "autoserial/tx", topic_sub: str = "autoserial/rx", **kwargs):
        """
        uri format: 'host:port' (e.g., 'test.mosquitto.org:1883')
        """
        super().__init__(uri=uri, protocol='mqtt')
        
        parts = uri.split(':')
        self.host = parts[0]
        self.port = int(parts[1]) if len(parts) > 1 else 1883
        
        self.topic_pub = topic_pub
        self.topic_sub = topic_sub
        
        self._client = mqtt.Client()
        self._rx_queue = queue.Queue()
        
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._client.subscribe(self.topic_sub)
        
    def _on_message(self, client, userdata, msg):
        self._rx_queue.put(msg.payload)

    def connect(self) -> None:
        if self._connected:
            return

        self._client.connect(self.host, self.port)
        self._client.loop_start()
        self._connected = True

    def disconnect(self) -> None:
        self.stop_monitoring()
        if self._connected:
            self._client.loop_stop()
            self._client.disconnect()
        self._connected = False

    def read(self, size: int = 1, timeout: Optional[float] = None) -> Any:
        if not self._connected:
            raise RuntimeError("Device is not connected.")
        
        try:
            # size is ignored for MQTT as we receive full messages
            # Convert timeout to block parameter for Queue
            data = self._rx_queue.get(block=(timeout is not None or timeout > 0), timeout=timeout)
            return data
        except queue.Empty:
            return b''

    def write(self, data: Any) -> int:
        if not self._connected:
            raise RuntimeError("Device is not connected.")
        
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        info = self._client.publish(self.topic_pub, data)
        info.wait_for_publish()
        return len(data)

    @classmethod
    def list_devices(cls) -> List[Dict[str, Any]]:
        # MQTT brokers are not discoverable by default.
        return []
