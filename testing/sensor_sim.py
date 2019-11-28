import os, serial, pty
import math, time
print("This program simulates a data stream via serial ports")


# create a pseudo terminal
master, slave = pty.openpty()
# retrieve the name for the port
s_port = os.ttyname(slave)
# print port so the user can enter it in testbench
print("You can connect to this data stream via: {0}".format(s_port))


# example of a data sending loop
x = []
y = []
while(1):
    # create some data
    t = time.perf_counter()
    x.append(t)
    y.append(math.sin(t))
    # wait a second
    time.sleep(1)
    #print("new data: x = {0}, y = {1}".format(x[-1],y[-1]))
    # write to master here
    os.write(master,str.encode("REQ:{0},{1}\r\n".format(x[-1],y[-1])))