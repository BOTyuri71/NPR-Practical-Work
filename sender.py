import threading
import socket
import struct

MCAST_GROUP = 'FF02::1'
MCAST_PORT = 8080
IFN = 'eno1'


def sender(message):

    # Create ipv6 datagram socket
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    
    # Allow own messages to be sent back (for local testing)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, True)
    sock.sendto(message.encode('utf-8'), (MCAST_GROUP, MCAST_PORT))


s = threading.Thread(target=sender('here'), args=(1,))

s.start()
