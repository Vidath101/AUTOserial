import time
import logging
from autoserial import Device

logging.basicConfig(level=logging.INFO)

def callback(data):
    print(f"Received via monitor: {data}")

def main():
    print("--- Listing Available Devices ---")
    devices = Device.list(suppress_errors=True)
    if not devices:
        print("No devices found on any protocol.")
    
    for d in devices:
        print(d)

    print("\n--- Auto Connecting ---")
    # You can pass hints to narrow down the search, e.g., hints=['uart']
    device = Device.auto_connect(suppress_errors=True)
    
    if device:
        print(f"Successfully auto-connected to {device}")
        try:
            # Example: writing some data (ensure the data format is suitable for the connected protocol)
            device.write(b"Hello Hardware!\n")
            print("Wrote data to device.")
            
            # Start background monitoring
            print("Starting background monitoring...")
            device.monitor(callback)
            
            time.sleep(3)
            
            print("Stopping monitor...")
            device.stop_monitoring()
        finally:
            device.disconnect()
            print("Disconnected.")
    else:
        print("Could not auto-connect to any device.")

if __name__ == "__main__":
    main()
