"""
Custom exceptions for the Berry Oximeter library
"""


class BerryOximeterError(Exception):
    """Base exception for all Berry Oximeter errors"""

    pass


class DeviceNotFoundError(BerryOximeterError):
    """Raised when the Berry oximeter device cannot be found"""

    pass


class ConnectionError(BerryOximeterError):
    """Raised when connection to the device fails"""

    pass


class NoDataError(BerryOximeterError):
    """Raised when no data is received from the device"""

    pass
