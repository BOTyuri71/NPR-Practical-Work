import threading
import socket
import struct
import vehicle
import time

MCAST_GROUP = 'FF02::1'
MCAST_PORT = 10000

v = vehicle.Vehicle(4,56,45)
v.nextVel(20)

def vehicle_multicast(message):

    # Create ipv6 datagram socket
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 1)
    
    # Allow own messages to be sent back (for local testing)
    #sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, True)
    v.state_pdu_string()
    sock.sendto(str(v.message).encode('utf-8'), (MCAST_GROUP, MCAST_PORT))
    
while(True):
    s = threading.Thread(target=vehicle_multicast(v.message), args=(1,))
    s.start()
    time.sleep(5)