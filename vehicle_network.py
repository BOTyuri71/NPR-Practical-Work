import threading
import socket
import struct
import vehicle
import time

MCAST_GROUP = 'FF02::1'
MCAST_PORT = 10000
MCAST_PORT2 = 8080

v = vehicle.Vehicle(5,17,34)
v.nextVel(20)

def vehicle_multicast_sender(message):

    # Create ipv6 datagram socket
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 32)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, 0)
    
    # Allow own messages to be sent back (for local testing)
    #sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, True)
    v.state_pdu_string()
    sock.sendto(str(v.message).encode('utf-8'), (MCAST_GROUP, MCAST_PORT))

def vehicle_multicast_receiver():
     # Initialise socket for IPv6 datagrams
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Allows address to be reused
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Binds to all interfaces on the given port
    sock.bind(('', MCAST_PORT2))

    # Allow messages from this socket to loop back for development
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, True)

    # Construct message for joining multicast group
    mreq = struct.pack("16s15s".encode('utf-8'), socket.inet_pton(socket.AF_INET6, MCAST_GROUP), (chr(0) * 16).encode('utf-8'))
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)

    data, addr = sock.recvfrom(1024)
    print(data.decode())

while(True):
    s = threading.Thread(target=vehicle_multicast_sender(v.message), args=(1,))
    s.start()
    time.sleep(5)