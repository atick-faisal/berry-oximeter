"""
Main BerryOximeter class implementation
"""

import asyncio
import csv
import os
from datetime import datetime
from typing import Optional, Callable, List
from uuid import UUID

from bleak import BleakClient, BleakScanner

from .exceptions import DeviceNotFoundError, ConnectionError, NoDataError
from .models import OximeterReading
from .parser import BCIProtocolParser

# UUIDs for the Berry oximeter
DATA_SERVICE_UUID = UUID("49535343-fe7d-4ae5-8fa9-9fafd205e455")
RECEIVE_CHARACTERISTIC = UUID("49535343-1E4D-4BD9-BA61-23C647249616")

# Device name to search for
DEVICE_NAME = "BerryMed"


class BerryOximeter:
    """Simple interface for Berry pulse oximeter data collection"""

    def __init__(self):
        self._client: Optional[BleakClient] = None
        self._device_address: Optional[str] = None
        self._parser = BCIProtocolParser()
        self._streaming_callback: Optional[Callable] = None
        self._latest_reading: Optional[OximeterReading] = None
        self._collected_readings: List[OximeterReading] = []
        self._is_collecting = False

        # Logging
        self._csv_file = None
        self._csv_writer = None
        self._csv_filename: Optional[str] = None
        self._console_logging = False

        # Filtering
        self._min_signal_strength: Optional[int] = None

        # Event loop handling
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._connection_task: Optional[asyncio.Task] = None

    @property
    def is_connected(self) -> bool:
        """Check if connected to a device"""
        return self._client is not None and self._client.is_connected

    def connect(self, device_address: Optional[str] = None, timeout: float = 10.0):
        """
        Connect to Berry oximeter

        Args:
            device_address: Optional specific device address. If None, finds first available.
            timeout: Connection timeout in seconds
        """
        asyncio.run(self._connect_async(device_address, timeout))

    async def _connect_async(self, device_address: Optional[str], timeout: float):
        """Async connection implementation"""
        if self.is_connected:
            return

        # Find the device if no address provided
        if device_address is None:
            print(f"Searching for {DEVICE_NAME}...")
            devices = await BleakScanner.discover(timeout=timeout)

            device = None
            for d in devices:
                if d.name == DEVICE_NAME:
                    device = d
                    device_address = d.address
                    break

            if device is None:
                available = [f"{d.name} ({d.address})" for d in devices if d.name]
                raise DeviceNotFoundError(
                    f"No {DEVICE_NAME} device found. "
                    f"Available devices: {', '.join(available) if available else 'None'}"
                )

        # Connect to device
        try:
            self._client = BleakClient(device_address)
            await self._client.connect(timeout=timeout)
            self._device_address = device_address

            # Start notifications
            await self._client.start_notify(RECEIVE_CHARACTERISTIC, self._handle_data)

        except Exception as e:
            self._client = None
            raise ConnectionError(f"Failed to connect to device: {e}")

    def disconnect(self):
        """Disconnect from the device"""
        if self._client:
            asyncio.run(self._disconnect_async())

    async def _disconnect_async(self):
        """Async disconnection implementation"""
        if self._client and self._client.is_connected:
            await self._client.stop_notify(RECEIVE_CHARACTERISTIC)
            await self._client.disconnect()
        self._client = None
        self._device_address = None

    def start_streaming(self, callback: Callable[[OximeterReading], None]):
        """
        Start streaming data to a callback function

        Args:
            callback: Function called with each new reading
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to device")

        self._streaming_callback = callback

    def stop_streaming(self):
        """Stop streaming data"""
        self._streaming_callback = None

    def get_reading(self, timeout: float = 5.0) -> OximeterReading:
        """
        Get the latest reading

        Args:
            timeout: Maximum time to wait for a reading

        Returns:
            Latest OximeterReading

        Raises:
            NoDataError: If no reading received within timeout
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to device")

        return asyncio.run(self._get_reading_async(timeout))

    async def _get_reading_async(self, timeout: float) -> OximeterReading:
        """Async implementation of get_reading"""
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            if self._latest_reading is not None:
                return self._latest_reading
            await asyncio.sleep(0.1)

        raise NoDataError(f"No reading received within {timeout} seconds")

    def get_readings(self, duration_seconds: float) -> List[OximeterReading]:
        """
        Collect readings for a specified duration

        Args:
            duration_seconds: How long to collect data

        Returns:
            List of OximeterReading objects
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to device")

        return asyncio.run(self._get_readings_async(duration_seconds))

    async def _get_readings_async(
        self, duration_seconds: float
    ) -> List[OximeterReading]:
        """Async implementation of get_readings"""
        self._collected_readings = []
        self._is_collecting = True

        await asyncio.sleep(duration_seconds)

        self._is_collecting = False
        return self._collected_readings.copy()

    def start_logging(self, filename: Optional[str] = None) -> str:
        """
        Start logging data to CSV file

        Args:
            filename: Optional filename. If None, auto-generates with timestamp.

        Returns:
            The filename being used
        """
        if filename is None:
            os.makedirs("data", exist_ok=True)
            filename = os.path.join(
                "data", f"oximeter_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )

        self._csv_filename = filename
        self._csv_file = open(filename, "w", newline="")
        self._csv_writer = csv.writer(self._csv_file)

        # Write headers
        self._csv_writer.writerow(
            [
                "timestamp",
                "spo2",
                "pulse_rate",
                "pleth",
                "signal_strength",
                "status",
                "pulse_beep",
            ]
        )
        self._csv_file.flush()

        return filename

    def stop_logging(self) -> Optional[str]:
        """
        Stop logging and close file

        Returns:
            The filename that was being logged to
        """
        if self._csv_file:
            self._csv_file.close()
            self._csv_file = None
            self._csv_writer = None

        filename = self._csv_filename
        self._csv_filename = None
        return filename

    def log_to_console(self, enabled: bool = True):
        """Enable or disable console logging"""
        self._console_logging = enabled

    def set_filter(self, min_signal_strength: Optional[int] = None):
        """
        Set filtering options

        Args:
            min_signal_strength: Minimum signal strength (0-8) to accept readings
        """
        self._min_signal_strength = min_signal_strength

    def _handle_data(self, _, data: bytes):
        """Handle incoming BLE data"""
        readings = self._parser.add_data(data)

        for reading in readings:
            # Apply filters
            if self._min_signal_strength is not None:
                if reading.signal_strength < self._min_signal_strength:
                    continue

            # Update latest reading
            self._latest_reading = reading

            # Collect if needed
            if self._is_collecting:
                self._collected_readings.append(reading)

            # Stream to callback
            if self._streaming_callback:
                self._streaming_callback(reading)

            # Log to console
            if self._console_logging:
                self._log_to_console(reading)

            # Log to CSV
            if self._csv_writer:
                self._log_to_csv(reading)

    @staticmethod
    def _log_to_console(reading: OximeterReading):
        """Log reading to console"""
        timestamp_str = reading.timestamp.strftime("%H:%M:%S.%f")[:-3]

        print(f"\r[{timestamp_str}] ", end="")

        if reading.spo2 is not None:
            print(f"SpO2: {reading.spo2}% ", end="")
        else:
            print("SpO2: --- ", end="")

        if reading.pulse_rate is not None:
            print(f"Pulse: {reading.pulse_rate} BPM ", end="")
        else:
            print("Pulse: --- BPM ", end="")

        if reading.pleth is not None:
            print(f"Pleth: {reading.pleth:3d} ", end="")

        print(f"Signal: {reading.signal_strength}/8 ", end="")

        # Status
        if reading.status != "reading":
            print(f"[{reading.status.upper()}] ", end="")

        if reading.pulse_beep:
            print("♥ ", end="")

        print("", flush=True)

    def _log_to_csv(self, reading: OximeterReading):
        """Log reading to CSV file"""
        if self._csv_writer:
            self._csv_writer.writerow(
                [
                    reading.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                    reading.spo2 if reading.spo2 is not None else "",
                    reading.pulse_rate if reading.pulse_rate is not None else "",
                    reading.pleth if reading.pleth is not None else "",
                    reading.signal_strength,
                    reading.status,
                    reading.pulse_beep,
                ]
            )
            self._csv_file.flush()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup"""
        self.stop_streaming()
        self.stop_logging()
        self.disconnect()
