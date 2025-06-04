"""
Data models for the Berry Oximeter library
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class OximeterReading:
    """Represents a single reading from the pulse oximeter"""

    timestamp: datetime
    spo2: Optional[int] = None
    pulse_rate: Optional[int] = None
    pleth: Optional[int] = None
    signal_strength: int = 0

    # Status flags
    no_signal: bool = False
    probe_unplugged: bool = False
    no_finger: bool = False
    pulse_searching: bool = False
    pulse_beep: bool = False

    @property
    def is_valid(self) -> bool:
        """Check if the reading has valid SpO2 and pulse data"""
        return self.spo2 is not None and self.pulse_rate is not None

    @property
    def status(self) -> str:
        """Human-readable status of the reading"""
        if self.probe_unplugged:
            return "probe_unplugged"
        elif self.no_signal:
            return "no_signal"
        elif self.no_finger:
            return "no_finger"
        elif self.pulse_searching:
            return "searching"
        elif self.is_valid:
            return "reading"
        else:
            return "invalid"

    def to_dict(self) -> dict:
        """Convert reading to dictionary"""
        return {
            "timestamp": self.timestamp,
            "spo2": self.spo2,
            "pulse_rate": self.pulse_rate,
            "pleth": self.pleth,
            "signal_strength": self.signal_strength,
            "is_valid": self.is_valid,
            "status": self.status,
            "no_signal": self.no_signal,
            "probe_unplugged": self.probe_unplugged,
            "no_finger": self.no_finger,
            "pulse_searching": self.pulse_searching,
            "pulse_beep": self.pulse_beep,
        }
