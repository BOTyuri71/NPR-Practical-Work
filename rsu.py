import socket
import struct
import threading
import time

MCAST_GROUP = 'FF02::1'
MCAST_PORT = 10000

UDP_IP = "2001:0690:2280:0820::10"  #server_core
#UDP_IP = "::1" #localhost
UDP_PORT = 5005

def server_communication(message):
    sock = socket.socket(socket.AF_INET6, # Internet
					socket.SOCK_DGRAM) # UDP
    sock.sendto(message.encode('utf-8'), (UDP_IP, UDP_PORT))

def rsu_multicast_receiver():
    # Initialise socket for IPv6 datagrams
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Allows address to be reused
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Binds to all interfaces on the given port
    sock.bind(('', MCAST_PORT))

    # Allow messages from this socket to loop back for development
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, True)

    # Construct message for joining multicast group
    face_name = 'eth2'
    face_index = socket.if_nametoindex(face_name)
    mreq = struct.pack("16s15s".encode('utf-8'),socket.inet_pton(socket.AF_INET6, MCAST_GROUP), (chr(0) *16).encode('utf-8'))
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)
     
    data, addr = sock.recvfrom(1024)
    print(data.decode())
    server_communication(data.decode())   

while(True):
    r = threading.Thread(target=rsu_multicast_receiver(), args=(1,))
    r.start()
