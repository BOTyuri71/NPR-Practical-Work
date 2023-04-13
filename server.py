import socket
import struct
import threading

UDP_IP = "::" # = 0.0.0.0 u IPv4
UDP_PORT = 5005

def server_communication():
    sock = socket.socket(socket.AF_INET6, # Internet
						socket.SOCK_DGRAM) # UDP
    sock.bind((UDP_IP, UDP_PORT))

    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    print("received message:", data)

while True:
    r = threading.Thread(target=server_communication(), args=(1,))

    r.start()
