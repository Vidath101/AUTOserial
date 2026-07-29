import asyncio
import threading
import queue
from typing import Any, List, Dict, Optional
from bleak import BleakClient, BleakScanner
from ..base import BaseDevice

class BLEDevice(BaseDevice):
    def __init__(self, uri: str, rx_char: str = "", tx_char: str = "", **kwargs):
        """
        uri: MAC address (e.g., '24:71:89:cc:09:05') or UUID on macOS
        rx_char: UUID of the characteristic to read/notify from
        tx_char: UUID of the characteristic to write to
        """
        super().__init__(uri=uri, protocol='ble')
        self.rx_char = rx_char
        self.tx_char = tx_char
        
        self._client: Optional[BleakClient] = None
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._start_loop, daemon=True)
        self._loop_thread.start()
        
        self._rx_queue = queue.Queue()

    def _start_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _notification_handler(self, sender, data):
        self._rx_queue.put(data)

    def connect(self) -> None:
        if self._connected:
            return

        async def _connect():
            self._client = BleakClient(self.uri)
            await self._client.connect()
            if self.rx_char:
                await self._client.start_notify(self.rx_char, self._notification_handler)
        
        future = asyncio.run_coroutine_threadsafe(_connect(), self._loop)
        future.result(timeout=10) # Block until connected
        self._connected = True

    def disconnect(self) -> None:
        self.stop_monitoring()
        if self._connected and self._client:
            async def _disconnect():
                if self.rx_char:
                    try:
                        await self._client.stop_notify(self.rx_char)
                    except Exception:
                        pass
                await self._client.disconnect()
            
            future = asyncio.run_coroutine_threadsafe(_disconnect(), self._loop)
            try:
                future.result(timeout=5)
            except Exception:
                pass
                
        self._connected = False
        self._client = None

    def read(self, size: int = 1, timeout: Optional[float] = None) -> Any:
        if not self._connected:
            raise RuntimeError("Device is not connected.")
        
        if self.rx_char:
            # Using notifications
            try:
                return self._rx_queue.get(block=(timeout is not None or timeout > 0), timeout=timeout)
            except queue.Empty:
                return b''
        else:
            # No RX characteristic defined for notifications, try to do a direct read
            async def _read():
                # We need a characteristic to read from, if not provided we can't read
                raise ValueError("rx_char must be specified to read")
            future = asyncio.run_coroutine_threadsafe(_read(), self._loop)
            return future.result(timeout=timeout)

    def write(self, data: Any) -> int:
        if not self._connected or not self.tx_char:
            raise RuntimeError("Device is not connected or tx_char not specified.")
        
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        async def _write():
            await self._client.write_gatt_char(self.tx_char, data)
            
        future = asyncio.run_coroutine_threadsafe(_write(), self._loop)
        future.result(timeout=5)
        return len(data)

    @classmethod
    def list_devices(cls) -> List[Dict[str, Any]]:
        # Using a temporary event loop for discovery
        async def _scan():
            return await BleakScanner.discover(timeout=5.0)
            
        devices = []
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            # Already in an async context, this class method might need to be async or run differently,
            # but usually list_devices is called from synchronous context.
            import nest_asyncio
            nest_asyncio.apply()
            
        found = loop.run_until_complete(_scan())
        
        for d in found:
            devices.append({
                'uri': d.address,
                'name': d.name,
                'details': d.details
            })
            
        return devices
