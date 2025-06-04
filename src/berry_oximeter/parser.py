"""
BCI protocol parser for Berry Oximeter data packets
"""

from datetime import datetime
from typing import Optional, List
from .models import OximeterReading


class BCIProtocolParser:
    """Parser for BCI protocol packets from Berry pulse oximeter"""

    def __init__(self):
        self.packet_buffer = []

    def add_data(self, data: bytes) -> List[OximeterReading]:
        """
        Add new data to buffer and parse any complete packets

        Args:
            data: Raw bytes received from the device

        Returns:
            List of parsed OximeterReading objects
        """
        self.packet_buffer.extend(data)
        readings = []

        while len(self.packet_buffer) >= 5:
            # Find sync byte (bit 7 = 1)
            sync_index = self._find_sync_byte()

            if sync_index == -1:
                # No valid packet found, keep last 4 bytes
                self.packet_buffer = self.packet_buffer[-4:]
                break

            # Extract and parse packet
            packet = self.packet_buffer[sync_index : sync_index + 5]
            reading = self._parse_packet(packet)

            if reading:
                readings.append(reading)

            # Remove processed bytes
            self.packet_buffer = self.packet_buffer[sync_index + 5 :]

        return readings

    def _find_sync_byte(self) -> int:
        """Find the start of a valid packet"""
        for i in range(len(self.packet_buffer) - 4):
            # Check if byte has sync bit set (bit 7 = 1)
            if self.packet_buffer[i] & 0x80:
                # Check if the next 4 bytes have sync bit clear (bit 7 = 0)
                if all((self.packet_buffer[i + j] & 0x80) == 0 for j in range(1, 5)):
                    return i
        return -1

    @staticmethod
    def _parse_packet(data: bytes) -> Optional[OximeterReading]:
        """Parse a 5-byte BCI protocol packet"""
        if len(data) < 5:
            return None

        # Validate sync bits
        if not (data[0] & 0x80):  # First byte bit 7 should be 1
            return None
        for i in range(1, 5):
            if data[i] & 0x80:  # Other bytes bit 7 should be 0
                return None

        # Parse byte 1
        signal_strength = data[0] & 0x0F  # Bits 0-3
        no_signal = bool((data[0] >> 4) & 0x01)  # Bit 4
        probe_unplugged = bool((data[0] >> 5) & 0x01)  # Bit 5
        pulse_beep = bool((data[0] >> 6) & 0x01)  # Bit 6

        # Parse byte 2
        pleth = data[1] & 0x7F  # Bits 0-6

        # Parse byte 3
        # bargraph = data[2] & 0x0F # Bits 0-3 (not used in our model)
        no_finger = bool((data[2] >> 4) & 0x01)  # Bit 4
        pulse_searching = bool((data[2] >> 5) & 0x01)  # Bit 5
        pulse_rate_bit7 = (data[2] >> 6) & 0x01  # Bit 6

        # Parse byte 4
        pulse_rate_bits0_6 = data[3] & 0x7F  # Bits 0-6
        pulse_rate = (pulse_rate_bit7 << 7) | pulse_rate_bits0_6

        # Parse byte 5
        spo2 = data[4] & 0x7F  # Bits 0-6

        # Handle invalid values
        if pleth == 0:
            pleth = None
        if pulse_rate == 0xFF:
            pulse_rate = None
        if spo2 == 0x7F:
            spo2 = None

        return OximeterReading(
            timestamp=datetime.now(),
            spo2=spo2,
            pulse_rate=pulse_rate,
            pleth=pleth,
            signal_strength=signal_strength,
            no_signal=no_signal,
            probe_unplugged=probe_unplugged,
            no_finger=no_finger,
            pulse_searching=pulse_searching,
            pulse_beep=pulse_beep,
        )
