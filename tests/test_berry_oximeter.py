"""
Test cases for Berry Oximeter library
These tests focus on unit testing without requiring actual hardware
"""

from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, mock_open

import pytest

from berry_oximeter import (
    BerryOximeter,
    OximeterReading,
    ConnectionError,
    NoDataError,
)
from berry_oximeter.parser import BCIProtocolParser


class TestOximeterReading:
    """Test OximeterReading model"""

    def test_valid_reading(self):
        """Test a valid reading with all data"""
        reading = OximeterReading(
            timestamp=datetime.now(),
            spo2=98,
            pulse_rate=72,
            pleth=50,
            signal_strength=7,
        )

        assert reading.is_valid is True
        assert reading.status == "reading"
        assert reading.spo2 == 98
        assert reading.pulse_rate == 72

    def test_invalid_reading_no_spo2(self):
        """Test reading with missing SpO2"""
        reading = OximeterReading(
            timestamp=datetime.now(), spo2=None, pulse_rate=72, signal_strength=5
        )

        assert reading.is_valid is False
        assert reading.status == "invalid"

    def test_invalid_reading_no_pulse(self):
        """Test reading with missing pulse rate"""
        reading = OximeterReading(
            timestamp=datetime.now(), spo2=98, pulse_rate=None, signal_strength=5
        )

        assert reading.is_valid is False
        assert reading.status == "invalid"

    def test_status_priority(self):
        """Test that status reflects the most important condition"""
        # Probe unplugged takes priority
        reading = OximeterReading(
            timestamp=datetime.now(),
            probe_unplugged=True,
            no_finger=True,
            no_signal=True,
        )
        assert reading.status == "probe_unplugged"

        # No signal is the next priority
        reading = OximeterReading(
            timestamp=datetime.now(), no_signal=True, no_finger=True
        )
        assert reading.status == "no_signal"

        # No finger
        reading = OximeterReading(timestamp=datetime.now(), no_finger=True)
        assert reading.status == "no_finger"

        # Searching
        reading = OximeterReading(timestamp=datetime.now(), pulse_searching=True)
        assert reading.status == "searching"

    def test_to_dict(self):
        """Test conversion to dictionary"""
        timestamp = datetime.now()
        reading = OximeterReading(
            timestamp=timestamp,
            spo2=97,
            pulse_rate=65,
            pleth=45,
            signal_strength=6,
            pulse_beep=True,
        )

        data = reading.to_dict()
        assert data["timestamp"] == timestamp
        assert data["spo2"] == 97
        assert data["pulse_rate"] == 65
        assert data["pleth"] == 45
        assert data["signal_strength"] == 6
        assert data["is_valid"] is True
        assert data["status"] == "reading"
        assert data["pulse_beep"] is True


class TestBCIProtocolParser:
    """Test BCI protocol parser"""

    def test_valid_packet_parsing(self):
        """Test parsing a valid 5-byte packet"""
        parser = BCIProtocolParser()

        # Create a valid packet
        # Byte 1: sync bit (1) + signal strength (0x07)
        # Byte 2: pleth value (0x32)
        # Byte 3: bargraph (0x05) + pulse rate bit 7 (0)
        # Byte 4: pulse rate bits 0-6 (72)
        # Byte 5: SpO2 (98)
        packet = bytes([0x87, 0x32, 0x05, 72, 98])

        readings = parser.add_data(packet)

        assert len(readings) == 1
        reading = readings[0]
        assert reading.signal_strength == 7
        assert reading.pleth == 50  # 0x32
        assert reading.pulse_rate == 72
        assert reading.spo2 == 98

    def test_invalid_sync_bits(self):
        """Test that packets with wrong sync bits are rejected"""
        parser = BCIProtocolParser()

        # Invalid: first byte should have bit 7 = 1
        packet = bytes([0x07, 0x32, 0x05, 72, 98])
        readings = parser.add_data(packet)
        assert len(readings) == 0

        # Invalid: other bytes should have bit 7 = 0
        packet = bytes([0x87, 0xB2, 0x05, 72, 98])
        readings = parser.add_data(packet)
        assert len(readings) == 0

    def test_partial_packet_buffering(self):
        """Test that partial packets are buffered correctly"""
        parser = BCIProtocolParser()

        # Send first 3 bytes
        readings = parser.add_data(bytes([0x87, 0x32, 0x05]))
        assert len(readings) == 0

        # Send the remaining 2 bytes
        readings = parser.add_data(bytes([72, 98]))
        assert len(readings) == 1
        assert readings[0].spo2 == 98

    def test_multiple_packets(self):
        """Test parsing multiple packets in one data chunk"""
        parser = BCIProtocolParser()

        packet1 = bytes([0x87, 0x32, 0x05, 72, 98])
        packet2 = bytes([0x88, 0x28, 0x04, 75, 97])

        readings = parser.add_data(packet1 + packet2)

        assert len(readings) == 2
        assert readings[0].spo2 == 98
        assert readings[0].pulse_rate == 72
        assert readings[1].spo2 == 97
        assert readings[1].pulse_rate == 75

    # FIXME: Uncomment when handling invalid values is implemented
    # def test_invalid_values_handling(self):
    #     """Test handling of invalid sensor values"""
    #     parser = BCIProtocolParser()
    #
    #     # 0xFF pulse rate and 0x7F SpO2 are invalid
    #     packet = bytes([0x87, 0x00, 0x45, 0xFF, 0x7F])
    #
    #     readings = parser.add_data(packet)
    #     assert len(readings) == 1
    #     reading = readings[0]
    #     assert reading.pleth is None  # 0x00 is invalid
    #     assert reading.pulse_rate is None  # 0xFF is invalid
    #     assert reading.spo2 is None  # 0x7F is invalid

    def test_sync_byte_recovery(self):
        """Test recovery when garbage data is received"""
        parser = BCIProtocolParser()

        # Garbage + valid packet
        garbage = bytes([0x01, 0x02, 0x03])
        valid_packet = bytes([0x87, 0x32, 0x05, 72, 98])

        readings = parser.add_data(garbage + valid_packet)

        assert len(readings) == 1
        assert readings[0].spo2 == 98


class TestBerryOximeter:
    """Test BerryOximeter main class"""

    # FIXME: Uncomment when device discovery is implemented
    # @patch('berry_oximeter.oximeter.BleakScanner')
    # @patch('berry_oximeter.oximeter.BleakClient')
    # def test_connect_device_not_found(self, mock_client, mock_scanner):
    #     """Test connection when the device is not found"""
    #     # Mock no devices found
    #     mock_scanner.discover = AsyncMock(return_value=[])
    #
    #     oximeter = BerryOximeter()
    #
    #     with pytest.raises(DeviceNotFoundError):
    #         oximeter.connect()

    @patch("berry_oximeter.oximeter.BleakScanner")
    @patch("berry_oximeter.oximeter.BleakClient")
    def test_connect_success(self, mock_client_class, mock_scanner):
        """Test successful connection"""
        # Mock device discovery
        mock_device = Mock()
        mock_device.name = "BerryMed"
        mock_device.address = "AA:BB:CC:DD:EE:FF"
        mock_scanner.discover = AsyncMock(return_value=[mock_device])

        # Mock client
        mock_client = AsyncMock()
        mock_client.is_connected = True
        mock_client.connect = AsyncMock()
        mock_client.start_notify = AsyncMock()
        mock_client_class.return_value = mock_client

        oximeter = BerryOximeter()

        # This should not raise an exception
        oximeter.connect()

        # Give thread time to start
        import time

        time.sleep(0.5)

        assert oximeter.is_connected is True

        # Cleanup
        oximeter.disconnect()

    def test_streaming_not_connected(self):
        """Test that streaming fails when not connected"""
        oximeter = BerryOximeter()

        with pytest.raises(ConnectionError):
            oximeter.start_streaming(lambda x: None)

    def test_get_reading_not_connected(self):
        """Test that get_reading fails when not connected"""
        oximeter = BerryOximeter()

        with pytest.raises(ConnectionError):
            oximeter.get_reading()

    def test_get_readings_not_connected(self):
        """Test that get_readings fails when not connected"""
        oximeter = BerryOximeter()

        with pytest.raises(ConnectionError):
            oximeter.get_readings(10)

    @patch("berry_oximeter.oximeter.BleakScanner")
    @patch("berry_oximeter.oximeter.BleakClient")
    def test_streaming_callback(self, mock_client_class, mock_scanner):
        """Test streaming with callback"""
        # Setup mocks for connection
        mock_device = Mock()
        mock_device.name = "BerryMed"
        mock_device.address = "AA:BB:CC:DD:EE:FF"
        mock_scanner.discover = AsyncMock(return_value=[mock_device])

        mock_client = AsyncMock()
        mock_client.is_connected = True
        mock_client.connect = AsyncMock()
        mock_client.start_notify = AsyncMock()
        mock_client_class.return_value = mock_client

        oximeter = BerryOximeter()
        oximeter.connect()

        # Give thread time to start
        import time

        time.sleep(0.5)

        # Setup callback
        received_readings = []

        def callback(reading):
            received_readings.append(reading)

        oximeter.start_streaming(callback)

        # Simulate data reception
        test_packet = bytes([0x87, 0x32, 0x05, 72, 98])
        oximeter._handle_data(None, test_packet)

        assert len(received_readings) == 1
        assert received_readings[0].spo2 == 98
        assert received_readings[0].pulse_rate == 72

        oximeter.stop_streaming()
        oximeter.disconnect()

    @patch("berry_oximeter.oximeter.open", new_callable=mock_open)
    def test_csv_logging(self, mock_file):
        """Test CSV logging functionality"""
        oximeter = BerryOximeter()

        # Start logging
        filename = oximeter.start_logging("test.csv")
        assert filename == "test.csv"

        # Verify file was opened and headers written
        mock_file.assert_called_once_with("test.csv", "w", newline="")

        # Get the mock writer
        handle = mock_file()

        # Stop logging
        stopped_filename = oximeter.stop_logging()
        assert stopped_filename == "test.csv"

        # Verify file was closed
        handle.close.assert_called_once()

    def test_filter_by_signal_strength(self):
        """Test filtering readings by signal strength"""
        oximeter = BerryOximeter()
        oximeter.set_filter(min_signal_strength=5)

        # Create mock client to avoid connection
        oximeter._client = Mock()
        oximeter._client.is_connected = True

        # Setup callback to capture readings
        received_readings = []
        oximeter.start_streaming(lambda r: received_readings.append(r))

        # Send a packet with low signal strength (3)
        low_signal_packet = bytes([0x83, 0x32, 0x05, 72, 98])
        oximeter._handle_data(None, low_signal_packet)

        # Send a packet with high signal strength (7)
        high_signal_packet = bytes([0x87, 0x32, 0x05, 72, 98])
        oximeter._handle_data(None, high_signal_packet)

        # Only high signal reading should pass filter
        assert len(received_readings) == 1
        assert received_readings[0].signal_strength == 7

    def test_context_manager(self):
        """Test context manager functionality"""
        with (
            patch("berry_oximeter.oximeter.BleakScanner") as mock_scanner,
            patch("berry_oximeter.oximeter.BleakClient") as mock_client_class,
        ):
            # Setup mocks
            mock_device = Mock()
            mock_device.name = "BerryMed"
            mock_device.address = "AA:BB:CC:DD:EE:FF"
            mock_scanner.discover = AsyncMock(return_value=[mock_device])

            mock_client = AsyncMock()
            mock_client.is_connected = True
            mock_client.connect = AsyncMock()
            mock_client.start_notify = AsyncMock()
            mock_client.disconnect = AsyncMock()
            mock_client_class.return_value = mock_client

            # Use context manager
            with BerryOximeter() as oximeter:
                oximeter.connect()
                assert oximeter.is_connected is True

            # Should be disconnected after exit
            # Note: actual disconnection happens in thread, so we check the method was called
            assert oximeter._stop_event.is_set()

    def test_auto_filename_generation(self):
        """Test automatic filename generation for logging"""
        with (
            patch("berry_oximeter.oximeter.open", new_callable=mock_open),
            patch("os.makedirs") as mock_makedirs,
        ):
            oximeter = BerryOximeter()
            filename = oximeter.start_logging()

            # Check that data directory is created
            mock_makedirs.assert_called_once_with("data", exist_ok=True)

            # Check filename format
            assert filename.startswith("data/oximeter_data_")
            assert filename.endswith(".csv")

            oximeter.stop_logging()

    def test_console_logging_output(self, capsys):
        """Test console logging output format"""
        oximeter = BerryOximeter()
        oximeter.log_to_console(True)

        # Create a test reading
        reading = OximeterReading(
            timestamp=datetime.now(),
            spo2=98,
            pulse_rate=72,
            pleth=50,
            signal_strength=7,
            pulse_beep=True,
        )

        # Log to console
        oximeter._log_to_console(reading)

        # Check output
        captured = capsys.readouterr()
        assert "SpO2: 98%" in captured.out
        assert "Pulse: 72 BPM" in captured.out
        assert "Pleth:  50" in captured.out
        assert "Signal: 7/8" in captured.out
        assert "♥" in captured.out

    @patch("berry_oximeter.oximeter.BleakScanner")
    @patch("berry_oximeter.oximeter.BleakClient")
    def test_get_reading_timeout(self, mock_client_class, mock_scanner):
        """Test get_reading timeout behavior"""
        # Setup connection mocks
        mock_device = Mock()
        mock_device.name = "BerryMed"
        mock_device.address = "AA:BB:CC:DD:EE:FF"
        mock_scanner.discover = AsyncMock(return_value=[mock_device])

        mock_client = AsyncMock()
        mock_client.is_connected = True
        mock_client.connect = AsyncMock()
        mock_client.start_notify = AsyncMock()
        mock_client_class.return_value = mock_client

        oximeter = BerryOximeter()
        oximeter.connect()

        # Don't send any data, should time out
        with pytest.raises(NoDataError) as exc_info:
            oximeter.get_reading(timeout=0.5)

        assert "No reading received within 0.5 seconds" in str(exc_info.value)

        oximeter.disconnect()


# Integration test example (requires mocking the entire BLE stack)
class TestIntegration:
    """Integration tests for the complete flow"""

    @patch("berry_oximeter.oximeter.BleakScanner")
    @patch("berry_oximeter.oximeter.BleakClient")
    def test_complete_data_collection_flow(self, mock_client_class, mock_scanner):
        """Test complete flow from connection to data collection"""
        # Setup mocks
        mock_device = Mock()
        mock_device.name = "BerryMed"
        mock_device.address = "AA:BB:CC:DD:EE:FF"
        mock_scanner.discover = AsyncMock(return_value=[mock_device])

        mock_client = AsyncMock()
        mock_client.is_connected = True
        mock_client.connect = AsyncMock()
        mock_client.start_notify = AsyncMock()
        mock_client.disconnect = AsyncMock()
        mock_client_class.return_value = mock_client

        # Run test
        oximeter = BerryOximeter()
        oximeter.connect()

        # Simulate some data packets
        import time

        time.sleep(0.5)  # Let connection establish

        packets = [
            bytes([0x87, 0x32, 0x05, 72, 98]),  # Normal reading
            bytes([0x84, 0x00, 0x15, 0xFF, 0x7F]),  # Invalid reading
            bytes([0x88, 0x28, 0x04, 75, 97]),  # Another normal reading
        ]

        for packet in packets:
            oximeter._handle_data(None, packet)
            time.sleep(0.1)

        # Check we can get the latest reading
        reading = oximeter.get_reading()
        assert reading is not None

        # Disconnect
        oximeter.disconnect()
        assert oximeter._stop_event.is_set()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
