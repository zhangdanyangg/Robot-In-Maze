from Queue import Queue
import threading
import serial
import json
import time
import sys
from signal import *
from utils.decorators import *
from settings import *

__author__ = 'Danyang'
FUNCTION = 0
SENSOR = 1

class SerialCommander(object):

    def __init__(self, production=True):
        self.ready=False
        self.ser = None

        if production:
            self._init_serial()

        self.commands = Queue() # synchronized, queue of [function_code, parameter]

        # stop n wait
        self.outstanding_command_pair = None
        self.ack = False

    def disconnect(self, *args):
        print "closing serial"
        if self.ser.isOpen():
            self.ser.close()
            sys.exit(1)


    def _init_serial(self, port="/dev/ttyACM0", data_rate=9600):
        # Serial port: /dev/ttyACM0
        # The Raspberry Pi may not provide enough power to drive an Arduino, so you might need external power.
        self.ser = serial.Serial()
        self.ser.port = port
        self.ser.baudrate = data_rate
        self.ser.timeout = 1


        self.disconnect()
        self.ser.open()


    def _convert_to_machine_code(self, function_code, parameter):
        """
        Convert function code and parameter to the Arduino readable code
        :param function_code: int
        :param parameter: double
        :return: machine code string
        """
        function_code_str = '0000000' + str(function_code)
        function_code_str = function_code_str[-2:]
        parameter_str = '0000000' + str(int(parameter * 100))
        parameter_str = parameter_str[-5:]
        return function_code_str + parameter_str

    def _parse_function_status(self, receive_data_dict):
        """
        parse {"function": 0, "status": 200}
        :param receive_data_dict:
        :return:
        """
        function_code = receive_data_dict["function"]
        status_code = receive_data_dict["status"]

        return FUNCTION, {int(function_code): status_code}

    def _parse_sensor_readings(self, receive_data_dict):
        """
        parse {"sensors":[{"sensor":0,"value":100},{"sensor":1,"value":30},{"sensor":2,"value":30}]}
        :param receive_data_dict:
        :return:
        """
        sensor_lst = receive_data_dict["sensors"]
        reading_dic =  {}
        for element in sensor_lst:
            reading_dic[element["sensor"]] = element["value"]

        return SENSOR, reading_dic


    def write(self, function_code, parameter):
        """
        write to the serial
        :param function_code: int
        :param parameter: double
        """
        # if self.ready==True:
        self.ser.write(self._convert_to_machine_code(function_code, parameter))

    def read(self):
        """
        read from the serial
        :return: parsed json
        """
        receive_data = ""
        while True: # keep fetching until found json
            data = self.ser.readline() # waits for the arduino to send a serial and will not continue unless it fetches a serial

            if "{" in data: # only check for starting "{"
                receive_data = data[data.find("{"): ]
                break
            else:
                # debug_print("waiting to read")
                continue

        debug_print("received serial data: "+receive_data)
        receive_data_dict = json.loads(receive_data)
        if "sensors" in receive_data_dict:
            return self._parse_sensor_readings(receive_data_dict)
        elif "function" in receive_data_dict:
            return self._parse_function_status(receive_data_dict)
        else:
            return None, None

    @Deprecated
    def is_ready(self):
        """
        Ready when receiving {"function": 99, "status": 200}
        :return:
        """
        indicator, dic = self.read()
        if indicator!=FUNCTION:
            return

        if dic.get(99, None)==200:
            print "robot ready"
            self.ready = True

    def command_pop_n_exe(self):
        if not self.commands.empty():
            self.ack = False
            command_pair = self.commands.get()
            self.write(command_pair[0], command_pair[1])
            self.outstanding_command_pair = command_pair
            debug_print("Executing command"+str(command_pair))

    def command_put(self, function, parameter):
        self.commands.put([function, parameter])

    def is_command_acknowledged(self):
        print "waiting for ack"
        indicator, dic = self.read()


        # sensor data
        if indicator==SENSOR:
            print dic 
            return False

        # ack
        if dic.get(self.outstanding_command_pair[0], None)==200: # use the function_code to get the status
            self.ack = True
            self.outstanding_command_pair = None

        return self.ack

class SerialThread(threading.Thread):
    @Override(threading.Thread)
    def __init__(self, name, serialCommander = SerialCommander(), production=False):
        super(SerialThread, self).__init__()
        self.commander = serialCommander
        self.name = name
        self.production = production
        # clean up
        for sig in (SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM):
            signal(sig, self.commander.disconnect)


    @Override(threading.Thread)
    def run(self):
        print "Starting " + self.name
        while True:
            # while not self.commander.ready:
            #     self.commander.is_ready()
            #     time.sleep(5)

            if self.commander.commands.empty():
                debug_print("Waiting for enqueuing command")
                if self.production:
                    self.commander.command_put(0, 10)
                else:
                    function_code = int(raw_input("function code: "))
                    parameter = float(raw_input("parameter: "))
                    self.commander.command_put(function_code, parameter)
            else:
                self.commander.command_pop_n_exe()
                while not self.commander.is_command_acknowledged():
                    pass
        print "Exiting " + self.name


