# 1. Install Dependencies
pkg update -y && pkg install python termux-api jq -y
pip install colorama

# 2. Build the Valkyrie Engine
cat << 'EOF' > project_valkyrie.py
import os
import sys
import time
import json
import math
import subprocess
from datetime import datetime
from colorama import Fore, Back, Style, init

init(autoreset=True)

class ValkyrieSentinel:
    def __init__(self):
        self.baseline_muT = None
        self.calibration_cycles = 10
        self.current_cycles = 0
        self.history = []
        
    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def get_magnetic_reading(self):
        """
        Interrogates the physical magnetometer of the device.
        Earth's baseline magnetic field is typically between 25 and 65 microteslas (uT).
        """
        try:
            # Call Termux API for a single sensor read
            cmd = "termux-sensor -s 'Magnetic Field' -n 1"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            data = json.loads(result.stdout)
            
            # Extract the X, Y, Z vector values
            if "Magnetic Field" in data:
                values = data["Magnetic Field"]["values"]
                x, y, z = values[0], values[1], values[2]
                
                # Calculate the 3D magnitude of the magnetic field vector
                # magnitude = sqrt(x^2 + y^2 + z^2)
                magnitude = math.sqrt((x**2) + (y**2) + (z**2))
                return round(magnitude, 2), x, y, z
            return None, 0, 0, 0
        except Exception:
            return None, 0, 0, 0

    def calibrate(self):
        print(f"{Fore.CYAN}[*] CALIBRATING PHYSICAL ENVIRONMENT SENSORS...")
        readings = []
        for i in range(self.calibration_cycles):
            mag, _, _, _ = self.get_magnetic_reading()
            if mag:
                readings.append(mag)
                print(f"{Fore.WHITE}    -> Reading {i+1}/10: {mag} µT")
            time.sleep(0.5)
            
        if readings:
            self.baseline_muT = sum(readings) / len(readings)
            print(f"{Fore.GREEN}[+] CALIBRATION COMPLETE. Baseline Set: {round(self.baseline_muT, 2)} µT")
            time.sleep(2)
        else:
            print(f"{Fore.RED}[!] SENSOR FAULT. Ensure Termux:API is installed and sensors are permitted.")
            sys.exit()

    def dashboard(self):
        self.calibrate()
        
        while True:
            self.clear()
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            mag_val, x, y, z = self.get_magnetic_reading()
            
            if not mag_val:
                print(f"{Fore.RED}SENSOR CONNECTION LOST.")
                time.sleep(1)
                continue

            # Calculate Delta (Deviation from baseline)
            delta = abs(mag_val - self.baseline_muT)
            
            # LOGIC ENGINE: Assess Threat Level
            color = Fore.GREEN
            status = "ENVIRONMENT SECURE"
            threat_level = "LOW"
            
            if delta > 50.0:
                color = Fore.RED + Style.BRIGHT
                status = "CRITICAL ANOMALY: PROXIMITY BREACH"
                threat_level = "SEVERE"
                # Here is where APEX would trigger a hardware shutdown or wipe
            elif delta > 15.0:
                color = Fore.YELLOW
                status = "ELEVATED ELECTROMAGNETIC NOISE"
                threat_level = "MODERATE"

            print(f"{color}{'='*80}")
            print(f"{Fore.WHITE}{Style.BRIGHT}   P R O J E C T   V A L K Y R I E   |   PHYSICAL SIDE-CHANNEL SENTINEL")
            print(f"{color}{'='*80}")
            print(f"{Fore.WHITE}   SYSTEM CLOCK: {timestamp}  |  SENSOR: 3-Axis Magnetometer")
            print(f"{color}{'='*80}\n")
            
            print(f"{Fore.CYAN}   [ PHYSICAL TELEMETRY ]")
            print(f"{Fore.WHITE}   Baseline Anchor: {self.baseline_muT:.2f} µT")
            print(f"{Fore.WHITE}   Live Reading:    {color}{mag_val:.2f} µT {Fore.WHITE}(Delta: {delta:.2f} µT)")
            print(f"")
            print(f"{Fore.BLUE}   [ VECTOR ANALYSIS ]")
            print(f"{Fore.WHITE}   X-Axis (Pitch):  {x:.2f}")
            print(f"{Fore.WHITE}   Y-Axis (Roll):   {y:.2f}")
            print(f"{Fore.WHITE}   Z-Axis (Yaw):    {z:.2f}")
            print(f"")
            
            print(f"{color}   [ THREAT ASSESSMENT: {threat_level} ]")
            print(f"{color}   {status}")
            
            if threat_level == "SEVERE":
                print(f"\n{Back.RED}{Fore.WHITE}{Style.BRIGHT} !!! UNAUTHORIZED ELECTRONICS OR MAGNETIC TAMPERING DETECTED !!! ")
            
            print(f"\n{Fore.BLUE}{'='*80}")
            print(f"{Fore.WHITE}   Scanning local physical space... (Ctrl+C to Terminate)")
            
            # Fast refresh rate to catch momentary spikes
            time.sleep(0.5)

if __name__ == "__main__":
    try:
        app = ValkyrieSentinel()
        app.dashboard()
    except KeyboardInterrupt:
        sys.exit()
EOF

# 3. Deploy to Security Infrastructure
mv project_valkyrie.py SYSTEMS_MASTER_HUB/04_Security_Division/Active_Defense/
python SYSTEMS_MASTER_HUB/04_Security_Division/Active_Defense/project_valkyrie.py