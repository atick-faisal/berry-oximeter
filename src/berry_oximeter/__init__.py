"""
Berry Pulse Oximeter Library
A simple Python library for collecting data from BerryMed pulse oximeters via Bluetooth LE
"""

from .oximeter import BerryOximeter
from .exceptions import DeviceNotFoundError, ConnectionError, NoDataError
from .models import OximeterReading


__version__ = "0.0.3"
__app_name__ = "berry-oximeter"
__all__ = [
    "BerryOximeter",
    "OximeterReading",
    "DeviceNotFoundError",
    "ConnectionError",
    "NoDataError",
]


def hello() -> str:
    return "Hello from berry-oximeter!"
