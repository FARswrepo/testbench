from streamInterface import StreamThread

def list_available_parsers():
    parsers = [func for func in dir(Parser) if callable(getattr(Parser, func)) and func.startswith("_protocol_")]
    return parsers

class Parser():
    """This Class serves as the interface to all 
    custom protocols. You can add your own protocol
    as a function with the nameing convention 
    _protocol_XXX(self)"""
    seeker_position = 0
    packet = bytearray()

    def __init__(self):
        pass

    def _protocol_RQOBS(self):
        meta_data = (('Time','ms'),('Channel_1','Volt'),('Channel_2','Volt'))      # a tupel containing meta data for the time series
        packet_strings = [] # a list of strings representing each decoded package
        time_series = [[[],[]],[[],[]]]    # a list containing lists of time series 
        
        
        with StreamThread.data_lock:
            # take only 10000 byte at once
            end = min(Parser.seeker_position + 10000, len(StreamThread.data))
            for index in range(Parser.seeker_position,end):
                byte = StreamThread.data[index]
                #print("Parser found: {}".format(byte))
                if byte == ord(b'\n'):
                    packet_decoded = Parser.packet.decode('ascii')
                    packet_strings.append(packet_decoded)
                    #print("Packet:{}".format(Parser.packet))
                    Parser.packet.clear()
                    if packet_decoded.startswith("$RQOBS"):
                        split_packet = packet_decoded.split(',')
                        time_series[0][0].append(float(split_packet[1]))
                        time_series[1][0].append(float(split_packet[1]))
                        time_series[0][1].append(float(split_packet[2]))
                        time_series[1][1].append(float(split_packet[3]))       
                else:
                    Parser.packet.append(StreamThread.data[index])
                Parser.seeker_position += 1

        return packet_strings,time_series # this shall be the standard return tupel for all protocol functions
            
