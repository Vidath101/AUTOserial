import socket
import select
from typing import Any, List, Dict, Optional
from ..base import BaseDevice

class NetworkDevice(BaseDevice):
    def __init__(self, uri: str, protocol_type: str = 'tcp', **kwargs):
        """
        uri format: 'ip:port', e.g., '192.168.1.10:5000'
        protocol_type: 'tcp' or 'udp'
        """
        super().__init__(uri=uri, protocol='network')
        
        parts = uri.split(':')
        if len(parts) != 2:
            raise ValueError("URI must be in format 'host:port'")
        
        self.host = parts[0]
        self.port = int(parts[1])
        self.protocol_type = protocol_type.lower()
        self._sock: Optional[socket.socket] = None

    def connect(self) -> None:
        if self._connected:
            return

        if self.protocol_type == 'tcp':
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.connect((self.host, self.port))
        elif self.protocol_type == 'udp':
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # UDP is connectionless, but we can bind to receive or just use sendto
        else:
            raise ValueError(f"Unknown network protocol: {self.protocol_type}")
        
        self._connected = True

    def disconnect(self) -> None:
        self.stop_monitoring()
        if self._sock:
            self._sock.close()
        self._connected = False
        self._sock = None

    def read(self, size: int = 1024, timeout: Optional[float] = None) -> Any:
        if not self._connected or not self._sock:
            raise RuntimeError("Device is not connected.")
        
        # Use select for timeout
        ready = select.select([self._sock], [], [], timeout)
        if ready[0]:
            if self.protocol_type == 'tcp':
                data = self._sock.recv(size)
                if not data:
                    self.disconnect() # connection closed by peer
                return data
            else: # UDP
                data, _ = self._sock.recvfrom(size)
                return data
        
        return b'' # timeout

    def write(self, data: Any) -> int:
        if not self._connected or not self._sock:
            raise RuntimeError("Device is not connected.")
        
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        if self.protocol_type == 'tcp':
            self._sock.sendall(data)
            return len(data)
        else: # UDP
            return self._sock.sendto(data, (self.host, self.port))

    @classmethod
    def list_devices(cls) -> List[Dict[str, Any]]:
        # Network devices cannot be automatically listed easily without a specific discovery protocol (like mDNS).
        return []
