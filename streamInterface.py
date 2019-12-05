import threading
from serial import Serial
from time import sleep
class StreamThread(threading.Thread):
    data_lock = threading.Lock()
    data = bytearray()
    stop_thread = True
    close_thread = False
    stream_rest = 0.01 # default 100ms
    def __init__(self):
        super().__init__()
        self.stream_type = None

    def run(self):
        while not StreamThread.close_thread:
            if not StreamThread.stop_thread:
                #print("Stream running")
                if self.stream_type == "FileStream":
                    self.startFileStream()

                elif self.stream_type == "SerialStream":
                    self.startSerialStream()

                elif self.stream_type == "HTTPStream":
                    pass
            #print("Stream paused")
            sleep(1)
            
        return

    def startFileStream(self):
        with open(self.stream_file_path,"rb") as f:
            print("Reading from: {}".format(self.stream_file_path))
            with StreamThread.data_lock:
                StreamThread.data.extend(f.read())
            StreamThread.stop_thread = True


    def startSerialStream(self):
        with Serial(**self.stream_serial_setup) as ser:
            while(not StreamThread.stop_thread):    
                temp_data = ser.read()
                if len(temp_data) > 0:
                    #print(temp_data)
                    with StreamThread.data_lock:
                        StreamThread.data.extend(temp_data)
                # rest the thread to free resources
                #sleep(StreamThread.stream_rest) 

    def startHTTPStream(self):
        pass