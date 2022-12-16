import serial


class SIM922(serial.Serial):
    def __init__(self, port='COM4', baud=57600, timeout=0.5):
        super().__init__(port, baud, timeout=timeout)

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
