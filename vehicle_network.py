import threading
import socket
import struct
import vehicle
import time

MCAST_GROUP = 'FF02::1'
MCAST_PORT = 10000
IFN = 'eno1'

v = vehicle.Vehicle(5,17,34)
v.nextVel(20)

def sender(message):

    # Create ipv6 datagram socket
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 32)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, 0)
    
    # Allow own messages to be sent back (for local testing)
    #sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, True)
    v.state_pdu_string()
    sock.sendto(str(v.message).encode('utf-8'), (MCAST_GROUP, MCAST_PORT))


while(True):
    s = threading.Thread(target=sender(v.message), args=(1,))
    s.start()
    time.sleep(5)