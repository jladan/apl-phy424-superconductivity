""" Data acquisition example

The following script demonstrates a simple loop to read the magnitude of the
lockin-amplifier, and temperatures from the SIM922 thermodiode monitor.

There are some practical flaws, which should be fixed before using it in an
actual experiment:
    - The data is only saved after all measurements are taken, meaning all data
      will be lost if an error occurs or the script is aborted
    - The data file given by `filename` is always overwritten, so you are
      likely to erase useful data.
"""
import time
import numpy as np

# These modules must be in the same directory as this script
from lockin_7270 import LockIn7270
from sim922 import SIM922

lockin = LockIn7270()
thermo = SIM922()

# NOTE:
#  Because the delay between measurements is done with `time.sleep()` below,
#  the sampling period is not controlled precisely.
sample_period = 1 # seconds
duration = 60 # Roughly 1 minute
filename = "measurements.txt"

n_samples = duration // sample_period

times, magnitudes, temps, tvolts = [], [], [], []
start_time = time.time()
for _ in range(n_samples):
    magnitudes.push(lockin.get_magnitude())
    temps.push(thermo.get_T())
    tvolts.push(thermo.get_V())
    times.push(time.time() - start_time)
    time.sleep(sample_period)

# Convert to array with columns
measurements = np.stack([times, magnitudes, temps, tvolts], axis=1)
np.savetxt(filename, measurements, header="time (s), mag (V), T (K), T_volt (V)")
