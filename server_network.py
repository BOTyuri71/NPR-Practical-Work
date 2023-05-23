import time
import threading
import socket
import struct
import server
import time


UDP_IP = "::1" # = 0.0.0.0 u IPv4
UDP_PORT = 5005

s = server.Server(50)
        

def server_communication():
    sock = socket.socket(socket.AF_INET6, # Internet
						socket.SOCK_DGRAM) # UDP
    sock.bind((UDP_IP, UDP_PORT))

    while True:
        data, addr = sock.recvfrom(1024)
        print(str(data.decode()))
        s.logs.append(data.decode()) # buffer size is 1024 bytes
        s.packet_filter(data.decode())


r = threading.Thread(target=server_communication())
r.daemon = True
r.start()