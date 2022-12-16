import serial


class SIM922(serial.Serial):
    """ Class for communicating to the SIM922 diode temperature monitor

    When the class is constructed, communication is started with the SIM922 module 
    in the SIM900 mainframe through the specified serial port.

    Common methods:
        .get_T() : retrieve the temperature in K (as calculated from the calibration curve)
        .get_V() : retrieve the voltage in mV
        .send(command) : send the command string to the module (strings are sanitized)
        .send_receive(query) : send the query and return the result as a bytestring
    """
    
    def __init__(self, port='COM4', module_no=4, term_string='xxyyzz', baud=57600, timeout=0.5):
        super().__init__(port, baud, timeout=timeout)
        self.term_string=term_string
        self._connect_to_module(module_no)

    def _connect_to_module(self, module_no):
        """ Connect to the module <module_no> to pass-through commands
        """
        self.send(f'conn {module_no}, "{self.term_string}"')
    
    def _disconnect_module(self):
        """ Send the connection termination string to return to SIM900 communication
        """
        self.send(self.term_string)

    def get_T(self):
        return float(self.send_receive('tval? 1'))

    def get_V(self):
        return float(self.send_receive('volt? 1'))
        
    def send(self, command):
        self.write(self.sanitize(command))
        
    def send_receive(self, command):
        self.reset_input_buffer()
        self.send(command)
        # Serial.readline() waits for a line of input (with a timeout)
        return self.readline()
    
    def send_list(self, command_list):
            """ sends a list of commands, without waiting for a reply
            """
            return [self.send(c) for c in command_list]

    def send_receive_list(self, command_list):
        """ sends a list of commands and waits for a reply for each one
        """
        return [self.send_receive(c) for c in command_list]

    def sanitize(self, command):
        """ Converts to bytes and puts a carriage return (\\r) at the end
        """
        if isinstance(command, str):
            command = command.encode('ascii')
        # Force one <CR> at end of command
        command = command.strip() + b'\r\n'
        return command
