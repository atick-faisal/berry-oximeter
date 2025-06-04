"""
Basic usage examples for the Berry Oximeter library
"""

from berry_oximeter import BerryOximeter, DeviceNotFoundError
import time


def simple_monitoring():
    """Example 1: Simple real-time monitoring"""
    print("Example 1: Simple monitoring")
    print("-" * 40)

    # Create oximeter instance
    oximeter = BerryOximeter()

    try:
        # Connect to the first available device
        oximeter.connect()
        print("Connected!")

        # Enable console logging
        oximeter.log_to_console(True)

        # Monitor for 30 seconds
        print("Monitoring for 30 seconds...")
        time.sleep(30)

    except DeviceNotFoundError as e:
        print(f"Error: {e}")
    finally:
        oximeter.disconnect()
        print("Disconnected")


def callback_example():
    """Example 2: Using callbacks for custom processing"""
    print("\nExample 2: Callback-based monitoring")
    print("-" * 40)

    def my_callback(reading):
        if reading.is_valid:
            print(
                f"Valid reading - SpO2: {reading.spo2}%, Pulse: {reading.pulse_rate} BPM"
            )
        else:
            print(f"Status: {reading.status}")

    oximeter = BerryOximeter()

    try:
        oximeter.connect()
        oximeter.start_streaming(my_callback)

        print("Streaming data for 20 seconds...")
        time.sleep(20)

        oximeter.stop_streaming()

    except Exception as e:
        print(f"Error: {e}")
    finally:
        oximeter.disconnect()


def data_collection_example():
    """Example 3: Collect data for analysis"""
    print("\nExample 3: Data collection")
    print("-" * 40)

    oximeter = BerryOximeter()

    try:
        oximeter.connect()

        print("Collecting data for 60 seconds...")
        readings = oximeter.get_readings(duration_seconds=60)

        # Analyze collected data
        valid_readings = [r for r in readings if r.is_valid]

        if valid_readings:
            avg_spo2 = sum(r.spo2 for r in valid_readings) / len(valid_readings)
            avg_pulse = sum(r.pulse_rate for r in valid_readings) / len(valid_readings)

            print(f"\nCollected {len(readings)} total readings")
            print(f"Valid readings: {len(valid_readings)}")
            print(f"Average SpO2: {avg_spo2:.1f}%")
            print(f"Average Pulse: {avg_pulse:.1f} BPM")
        else:
            print("No valid readings collected")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        oximeter.disconnect()


def logging_example():
    """Example 4: Log data to file"""
    print("\nExample 4: File logging")
    print("-" * 40)

    oximeter = BerryOximeter()

    try:
        oximeter.connect()

        # Start logging
        filename = oximeter.start_logging("patient_001.csv")
        print(f"Logging to: {filename}")

        # Also show on console
        oximeter.log_to_console(True)

        print("Logging for 30 seconds...")
        time.sleep(30)

        # Stop logging
        oximeter.stop_logging()
        print(f"Data saved to: {filename}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        oximeter.disconnect()


def filtered_monitoring():
    """Example 5: Filtered monitoring"""
    print("\nExample 5: Filtered monitoring")
    print("-" * 40)

    oximeter = BerryOximeter()

    try:
        oximeter.connect()

        # Only accept readings with good signal strength
        oximeter.set_filter(min_signal_strength=5)

        def quality_callback(reading):
            print(
                f"High quality reading - SpO2: {reading.spo2}%, "
                f"Signal: {reading.signal_strength}/8"
            )

        oximeter.start_streaming(quality_callback)

        print("Monitoring high-quality readings for 30 seconds...")
        time.sleep(30)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        oximeter.disconnect()


def context_manager_example():
    """Example 6: Using context manager for automatic cleanup"""
    print("\nExample 6: Context manager usage")
    print("-" * 40)

    try:
        with BerryOximeter() as oximeter:
            oximeter.connect()
            oximeter.log_to_console(True)

            print("Monitoring for 20 seconds...")
            time.sleep(20)

        print("Automatically disconnected!")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("Berry Oximeter Library Examples")
    print("=" * 40)
    print("Choose an example to run:")
    print("1. Simple monitoring")
    print("2. Callback-based monitoring")
    print("3. Data collection and analysis")
    print("4. File logging")
    print("5. Filtered monitoring")
    print("6. Context manager usage")

    choice = input("\nEnter choice (1-6): ")

    examples = {
        "1": simple_monitoring,
        "2": callback_example,
        "3": data_collection_example,
        "4": logging_example,
        "5": filtered_monitoring,
        "6": context_manager_example,
    }

    if choice in examples:
        examples[choice]()
    else:
        print("Invalid choice!")
