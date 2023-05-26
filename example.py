import time
import numpy as np

# These modules must be in the same directory as this script
from lockin_7270 import LockIn7270
from sim922 import SIM922

lockin = LockIn7270()
thermo = SIM922()

duration = 60 # Roughly 1 minute

times, magnitudes, temps, tvolts = [], [], [], []
start_time = time.time()
for sample in range(60):
    magnitudes.push(lockin.get_magnitude())
    temps.push(thermo.get_T())
    tvolts.push(thermo.get_V())
    times.push(time.time() - start_time)
    time.sleep(1)

# Convert to array with columns
measurements = np.stack([times, magnitudes, temps, tvolts], axis=1)
np.savetxt('measurements.txt', measurements, header="time (s), mag (V), T (K), T_volt (V)")
