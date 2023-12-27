import subprocess

def read_pressure():
    # Run the command and capture the output
    result = subprocess.run(["read_bme280", "--pressure"], capture_output=True, text=True)

    # Check if the command was successful (return code 0)
    if result.returncode == 0:
        # Extract and return the pressure value
        pressure = result.stdout.strip()
        return float(pressure[:-4])
    else:
        # Handle the case when the command fails
        print(f"Error: Unable to read pressure. Exit code: {result.returncode}")
        return None

# Read pressure value
pressure_value = read_pressure()

if pressure_value is not None:
    print(f"Pressure: {pressure_value} hPa")
else:
    print("Failed to read pressure.")
