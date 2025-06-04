# Berry Oximeter 🫀

![Banner](https://raw.githubusercontent.com/atick-faisal/berry-oximeter/main/docs/assets/banner.png)

[![PyPI version](https://img.shields.io/badge/pypi-berry-oximeter.svg?colorA=363a4f&colorB=b7bdf8&style=for-the-badge)](https://badge.fury.io/py/berry-oximeter)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?colorA=363a4f&colorB=f5a97f&style=for-the-badge)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?colorA=363a4f&colorB=b7bdf8&style=for-the-badge)](https://opensource.org/licenses/MIT)

A simple Python library for real-time data collection from BerryMed pulse oximeters via Bluetooth
LE. Get heart rate, SpO2, and perfusion index readings with just a few lines of code!


> [!WARNING]
> This library is for educational and research purposes only. It is not intended for medical diagnosis
  or treatment. Always consult with a qualified healthcare provider for medical advice.

## Features ✨

- 🔌 **Auto-discovery** - Automatically finds and connects to your BerryMed device
- 📊 **Real-time streaming** - Get live readings with customizable callbacks
- 📈 **Data collection** - Collect readings over time for analysis
- 💾 **CSV logging** - Built-in data logging to CSV files
- 🎯 **Signal filtering** - Filter readings by signal quality
- 🐍 **Pythonic API** - Simple, intuitive interface
- 🧪 **Type hints** - Full type hint support for better IDE experience

## Installation 📦

Install via pip:

```bash
pip install berry-oximeter
```

Or using [uv](https://github.com/astral-sh/uv):

```bash
uv add berry-oximeter
```

## Quick Start 🚀

### Basic Usage

```python
from berry_oximeter import BerryOximeter

# Create instance and connect
oximeter = BerryOximeter()
oximeter.connect()

# Enable console output
oximeter.log_to_console(True)

# Let it run for 30 seconds
import time

time.sleep(30)

# Disconnect
oximeter.disconnect()
```

### Callback-based Streaming

```python
def handle_reading(reading):
    if reading.is_valid:
        print(f"♥ SpO2: {reading.spo2}%, Pulse: {reading.pulse_rate} BPM")
    else:
        print(f"Status: {reading.status}")


oximeter = BerryOximeter()
oximeter.connect()
oximeter.start_streaming(handle_reading)

# Stream for 60 seconds
time.sleep(60)

oximeter.stop_streaming()
oximeter.disconnect()
```

### Data Collection & Analysis

```python
# Collect 60 seconds of data
oximeter = BerryOximeter()
oximeter.connect()

readings = oximeter.get_readings(duration_seconds=60)

# Analyze the data
valid_readings = [r for r in readings if r.is_valid]
avg_spo2 = sum(r.spo2 for r in valid_readings) / len(valid_readings)
avg_pulse = sum(r.pulse_rate for r in valid_readings) / len(valid_readings)

print(f"Average SpO2: {avg_spo2:.1f}%")
print(f"Average Pulse: {avg_pulse:.1f} BPM")

oximeter.disconnect()
```

### CSV Logging

```python
oximeter = BerryOximeter()
oximeter.connect()

# Start logging (auto-generates filename with timestamp)
filename = oximeter.start_logging()
print(f"Logging to: {filename}")

# Or specify your own filename
# oximeter.start_logging("patient_123.csv")

# Collect data
oximeter.log_to_console(True)
time.sleep(300)  # 5 minutes

# Stop logging
oximeter.stop_logging()
oximeter.disconnect()
```

### Context Manager (Auto-cleanup)

```python
with BerryOximeter() as oximeter:
    oximeter.connect()
    oximeter.log_to_console(True)
    time.sleep(30)
    # Automatically disconnects when done
```

## API Reference 📚

### BerryOximeter Class

The main interface for interacting with the pulse oximeter.

#### Connection Methods

- `connect(device_address=None, timeout=10.0)` - Connect to device
- `disconnect()` - Disconnect from device
- `is_connected` - Property to check connection status

#### Data Access Methods

- `start_streaming(callback)` - Start streaming with callback function
- `stop_streaming()` - Stop streaming
- `get_reading(timeout=5.0)` - Get a single reading
- `get_readings(duration_seconds)` - Collect readings for specified duration

#### Logging Methods

- `start_logging(filename=None)` - Start CSV logging
- `stop_logging()` - Stop logging and return filename
- `log_to_console(enabled=True)` - Enable/disable console output

#### Configuration

- `set_filter(min_signal_strength=None)` - Filter by signal quality (0-8)

### OximeterReading Object

Each reading contains:

- `timestamp` - When the reading was taken
- `spo2` - Oxygen saturation (%) or None
- `pulse_rate` - Heart rate (BPM) or None
- `pleth` - Plethysmograph value or None
- `signal_strength` - Signal quality (0-8)
- `is_valid` - True if SpO2 and pulse are valid
- `status` - Human-readable status ("reading", "no_finger", "searching", etc.)

### Exceptions

- `DeviceNotFoundError` - No BerryMed device found
- `ConnectionError` - Failed to connect to device
- `NoDataError` - No data received within timeout

## Advanced Usage 🔧

### Filtering Low-Quality Signals

```python
# Only accept readings with signal strength >= 5
oximeter.set_filter(min_signal_strength=5)


def quality_callback(reading):
    print(f"High quality: SpO2 {reading.spo2}%, Signal: {reading.signal_strength}/8")


oximeter.start_streaming(quality_callback)
```

### Custom Logging

```python
import csv


def custom_logger(reading):
    if reading.is_valid:
        with open('custom_log.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                reading.timestamp,
                reading.spo2,
                reading.pulse_rate,
                reading.pleth,
                reading.signal_strength
            ])


oximeter.start_streaming(custom_logger)
```

### Async Integration

Since the library runs BLE operations in a separate thread, it works well with async code:

```python
import asyncio


async def monitor_patient(patient_id, duration):
    oximeter = BerryOximeter()
    oximeter.connect()
    oximeter.start_logging(f"patient_{patient_id}.csv")

    await asyncio.sleep(duration)

    oximeter.stop_logging()
    oximeter.disconnect()


# Run multiple monitors concurrently
async def main():
    await asyncio.gather(
        monitor_patient("001", 300),
        monitor_patient("002", 300)
    )
```

## Troubleshooting 🔍

### Device Not Found

- Make sure your BerryMed oximeter is turned on
- Check that Bluetooth is enabled on your computer
- The device name should be "BerryMed" - if yours is different, you'll need to modify the code
- On Linux, you may need to run with `sudo` or add your user to the `bluetooth` group

### Connection Issues

- Ensure the device isn't already connected to another application
- Try moving closer to the device
- Some devices may need to be in pairing mode

### No Readings

- Make sure your finger is properly inserted
- Keep your hand still - movement affects readings
- Warm up cold fingers first
- Check the signal strength indicator

## Supported Devices 📱

This library is tested with:

- BerryMed BM1000C
- Other BerryMed pulse oximeters using
  the [BCI protocol](https://raw.githubusercontent.com/atick-faisal/berry-oximeter/main/docs/assets/BCI_protocol_v_1.2.pdf)

The library should work with any Berry device that:

- Advertises as "BerryMed" over Bluetooth LE
- Uses the standard BCI protocol (5-byte packets)

## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open
an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Acknowledgments 🙏

- Thanks to the [Bleak](https://github.com/hbldh/bleak) project for the excellent BLE library
- Inspired by the need for simple, reliable pulse oximeter data collection in research settings
- 

<p align="center"><img src="https://raw.githubusercontent.com/catppuccin/catppuccin/main/assets/footers/gray0_ctp_on_line.svg?sanitize=true" /></p>
<p align="center"><a href="https://sites.google.com/view/mchowdhury" target="_blank">Qatar University Machine Learning Group</a>
<p align="center"><a href="https://github.com/atick-faisal/berry-oximeter/blob/main/LICENSE"><img src="https://img.shields.io/github/license/atick-faisal/berry-oximeter?style=for-the-badge&colorA=363a4f&colorB=b7bdf8"/></a></p>