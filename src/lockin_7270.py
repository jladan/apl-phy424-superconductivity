""" Lockin Amplifier Module

This module implements a class for communications with the lock-in amplifier (AMETEK 7270)

Usage
=====

A connection is established when the `LockIn7270` object is created. A
reasonable set of defaults is established at that point.
- single, internal reference mode
- A-B differential (reads voltage between pins of A and B connectors)
- Floating ground (for when a single-connector is used)
- Automatic sensitivity

The majority of measuremnts should be made using the "Front Panel" methods:
`get_x()`, `get_y()`, etc. If faster sampling is required, then the Lockin's
curve buffer can be used.

For a single measurement,
```
lockin = LockIn7270()
mag = lockin.get_magnitude()
# At this point, magnitude should be a float matching the front panel measurement in Volts.
```

For repeated measurements at approximately 1s intervals,
```
import time
import numpy as np

from lockin_7270 import LockIn7270

lockin = LockIn7270()

duration = 60 # Roughly 1 minute
times, magnitudes = [], []
start_time = time.time()
for sample in range(60):
    magnitudes.push(lockin.get_magnitude())
    times.push(time.time() - start_time)
    time.sleep(1)

# Cast to an array for later use
times = np.array(times)
magnitudes = np.array(magnitudes)
```

Note that `time.sleep()` is not precise, and `lockin.get_magnitude()` takes
additional time for queries, so it is not possible to precisely control time of
measurements this way. To account for that, we measure the actual time of the
measurement using `time.time()`.

For curve measurements, refer to the `LockIn7270.run()` method.

```
import time
from lockin_7270 import LockIn7270

lockin = LockIn7270()

sample_rate = 10000 # sample rate for the lockin's internal curve buffer
buffer_length = 10000000 # number of samples to retrieve from the curve buffer
lockin.curve_setup(sample_rate, buffer_length)
events[0].set()
lockin.send("TD") # Must be sent to begin sampling
# The following sleep command may or may not be necessary
time.sleep(buffer_length * sample_rate / 1e6 + 1)
self.read_all_curves()

# The curve data is now stored in lockin.data
```
"""


import time
import numpy as np
import array
import usb.core

###############################################################################
# Lock in class
###############################################################################
SETUP_CMDS = {
    "REMODE": 0, "VMODE": 3, "IE": 0,
    "DCCOUPLE": 0, "FLOAT": 1, "TC": 12,
    "FET": 0}

"""
Some commands and their meanings. For a comprehensive list of commands see the
AMETEK 7270 manual.
 "REFMODE 0" single reference mode
 "IE 0" internal reference
 "VMODE 3" A-B differential mode
 "DCCOUPLE 0" AC coupling
 "FLOAT 1" floating ground
 "AUTOMATIC 1" automatic AC gain setting
 "ASM" auto sensitivity mode
 "TC 12" 100 ms time constant
 "FET 0" bipolar device
 """

SENSITIVITY = {1: 2e-9, 2: 5e-9, 3: 10e-9,
               4: 20e-9, 5: 50e-9, 6: 100e-9,
               7: 200e-9, 8: 500e-9, 9: 1e-6,
               10: 2e-6, 11: 5e-6, 12: 10e-6,
               13: 20e-6, 14: 50e-6, 15: 100e-6,
               16: 200e-6, 17: 500e-6, 18:1e-3,
               19: 2e-3, 20: 5e-3, 21: 10e-3,
               22: 20e-3, 23: 50e-3, 24: 100e-3,
               25: 200e-3, 26: 500e-3, 27: 1}

class LockIn7270:
    """ Instance of an Ametek 7270 lock in amplifier


        Public Methods
        --------------
        query(..)       - write and read commands to device, ignoring errors
        query_safe(..)  - write and read commands to device
        send(..)        - write a command to the device
        send_list(..)   - write a list of commands to the device
        setup(..)       - update device settings

        DAQ Methods
        -----------
        get_x()         - query the 'X' value
        get_y()         - query the 'Y' value
        get_magnitude() - query the 'MAG' (magnitude) value
        get_phase()     - query the 'PHA' (phase) value

        Curve (fast sampling) Methods
        -----------------------------
        curve_setup(..) - update device settings for new curve measurement
        read_curve(..)  - read curve data for a single attribute into data buffer
        read_all_curves - read all curves into data buffer
        run(..)         - complete curve measurements
 
        Public Attributes
        ----------------
        dev - lock in device.
        data - dictionary of stored data measurements.
        ep_in/_out - location of in and out usb endpoints respectively.

    """
    ID_VENDOR = 2605
    ID_PRODUCT = 27
    EP_WRITE = 1
    def __init__(self, cmds=SETUP_CMDS):
        """ Initialize class.
         
            Paramaters
            ----------
            cmds : dict {str : int}
                Dictionary containing system parameters the lock in amplifier
                should be ran at. key: command name (str), value: command value
                (int). 
                Default -> 
                    "REMODE": 0, "VMODE": 3, "IE": 0,
                    "DCCOUPLE": 0, "FLOAT": 1, "TC": 12, "FET": 0.
                    See lock in manual for more details. 
        """
        # find the device and set the configuration
        self.dev = usb.core.find(idVendor=self.ID_VENDOR, idProduct=self.ID_PRODUCT)
        self.dev.set_configuration()
        # store the lockin set-up commands for a future call to .set_up()
        self.paramaters = cmds
        # in and out endpoints respectively
        self.ep_in = self.dev[0].interfaces()[0].endpoints()[1]  # bulk in
        self.ep_out = self.dev[0].interfaces()[0].endpoints()[0]  # bulk out
        # Initialize data storage for reading curves
        self.data = {0: [], 1: [], 3: [], 4: [], 5: []}  

    def set_up(self):
        """ Write settings based on the parameter attribute. """
        for cmd, value in self.paramaters.items():
            self.send("{} {}".format(cmd, value))
        self.send("AS") # autosensitivity mode

    # Basic send and receive methods {{{
    def send(self, cmd):
        """ Sends a command to the lockin device """
        self.dev.write(self.EP_WRITE, cmd)

    def send_list(self, cmdlist):
        """ Sends a list of commands to the lockin device. """
        for cmd in cmdlist:
            self.send(cmd)

    def receive(self):
        """ Reads data from the lockin device. 

            returns
            -------
            output : bytes
        """
        output = self.dev.read(
                self.ep_in.bEndpointAddress, 
                self.ep_in.wMaxPacketSize)
        return output

    # }}}

    # General Query Methods {{{
    def query(self, cmd, silent=True):
        """ Write and read a command to the lock in instrument, ignoring errors.
            
            Paramaters
            ----------
            cmd : str
                The command.
            silent : bool
                Print the response to console if silent=False

            Returns
            -------
            response : str
                The response from the device as a UTF-8 string.
        """
        response = ''
        try:
            response = self.query_safe(cmd)
        except:
            pass
        if not silent:
            print(response)
        return response

    def query_safe(self, cmd):
        """ Write and read a command to the lock in instrument, passing errors through.
            
            Paramaters
            ----------
            cmd : str
                The command.

            Returns
            -------
            response : str
                The response from the device as a UTF-8 string.
        """
        self.dev.write(1, cmd)
        output = self.receive()
        result = output.tobytes().decode('utf-8')
        return result

    # }}}

    # Front-panel measurements {{{

    def get_x(self):
        """ Read the X value from the front panel as a float """
        return self._get_float('X.')

    def get_y(self):
        """ Read the Y value from the front panel as a float """
        return self._get_float('Y.')

    def get_magnitude(self):
        """ Read the magnitude value from the front panel as a float """
        return self._get_float('MAG.')

    def get_phase(self):
        """ Read the phase value from the front panel as a float """
        return self._get_float('PHA.')

    def _get_float(self, cmd):
        value_str = self.query_safe(cmd)
        return float(value_str)

    #}}}

    # Curve reading methods {{{
    def curve_setup(self, sample_rate=10000, len_=100000):
        """ Initialize curve collection settings of the device.

            Paramaters
            ----------
            sample_rate : int
                Time steps between measurements in microseconds (minimum: 1 - in fast
                mode; 1000 standard mode)
            len_ : int
                Number of measuremnts to store (max = 100,000)
        """
        self.dev.write(1, "AS") # autosensitivity mode`
        self.query("NC", True)  # clear curve buffer
        self.query("CMODE 0", True)  # set curve aquistion to fast mode
        self.query("CBD 59", True)  # store X,Y, phase, sensitivity, Noise
        self.query("LEN {}".format(len_), True)
        # max len value is 100,000
        self.query("STR {}".format(sample_rate), True)  # store data every 10 ms [in micro-s]
        # 10 Hz * 1000000 = 100
        self.query("REFP 0", True)  # set phase to 0

    def read_curve(self, bit_):
        """ Read and save curve data for the specified <bit_> value. 
            
            Read curve data, convert data to floating point numbers, and store
            results in data attribute at corresponding location.
            
            Paramaters
            ----------
            bit_ : int
                Integer corresponding to which curve to aquire.
                0 - X values
                1 - Y values
                3 - Phase values
                4 - Sensitivity
                5 - Noise

            To convert the X, Y, and Noise values to floating points you must
            multiply it by the sensitivity reading. The sensitivity reading
            output is an int corresponding to a sensitivity value; this is
            hardcoded in the dictionary SENSITIVITY above. Use the dictionary to
            get the correct sensitivity values before multiplication. 
        """
        output = array.array('B')
        self.dev.write(1, "DCB {}".format(bit_))
        while True:
            try:
                r = self.dev.read(self.ep_in.bEndpointAddress, self.ep_in.wMaxPacketSize)
                output.extend(r)
            except:
                break

        data = []
        # the len(output)-3 converts all the bytes except the null byte which
        # takes up the last 3 positions of the output array 
        for i in range(0, len(output)-3, 2):
            byte_str = output[i:i+2].tobytes()
            # see page 6-31 under DCB command for details on the bytes outputted
            value = int.from_bytes(byte_str, byteorder="big", signed=True)
            data.append(value)
        self.data[bit_].extend(data)

    def read_all_curves(self):
        """ Save all curves stored in device buffer to computer.
        """
        try:
            r = self.dev.read(self.ep_in.bEndpointAddress, self.ep_in.wMaxPacketSize)
        except:
            pass

        for i in self.data.keys():
            self.read_curve(i)

    # }}}

    def run(self, curr_fin_voltage,
            events, lock, barrier, 
            sample_rate=10000, len_=1000000):
        """ Run curve aquistion (deprecated).

            This was intended to run in a thread, but was replaced with the
            simpler front-panel measurements.
            
            Parameters
            ----------
            curr_fin_voltage : (int, int)
                (current, final) voltages of the aquistion run. <current> is the
                current voltage reading of the transdiode of the sample and
                <final>, is the final voltage reading on the sample transdiode at
                which to stop the aquistion.
            events : List[threading.Event()]
                List of 3 event objects that control the syncronization of data
                device measurement with the osciliscope.
            lock : threading.Lock() 
                Lock object to prevent LockIn7270 and Osciliscope objects from
                reading/writing the <curr_fin_voltage> at the same time.
            sample_rate : int
                Time steps between measurements in microseconds (minimum: 1 - in fast
                mode; 1000 standard mode)
            len_ : int
                Number of measuremnts to store (max = 100,000)
        """
        print("Lock in running.")
        with lock:
            curr = curr_fin_voltage[0]
            fin = curr_fin_voltage[1]
        while curr > fin:
            self.curve_setup(sample_rate, len_)
            events[0].set()
            self.query("TD", True)
            time.sleep(len_ * sample_rate / 1e6 + 1)
            self.read_all_curves()
            events[1].set()
            events[1].clear()
            barrier.wait()
            with lock:
                curr = curr_fin_voltage[0]

# @LockIn7270
# def AS(value):
#     for bit_, sen in SENSITIVITY:
#         if 0.4 > value / sen  and value > sen > 0.8:
#             return bit_
#     return 27
