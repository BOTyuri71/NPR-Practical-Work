import threading
import socket
import struct

MCAST_GROUP = 'FF02::1'
MCAST_PORT = 10000
IFN = "eno1"


def sender(message):

    sock = socket.socket(
        socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(41,
                    socket.IPV6_MULTICAST_HOPS, 32)

    # For Python 3, change next line to 'sock.sendto(b"robot", ...' to avoid the
    # "bytes-like object is required" msg (https://stackoverflow.com/a/42612820)
    sock.sendto(message.encode(), (MCAST_GROUP, MCAST_PORT))


def receiver():
    # Create socket
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    # Set multicast interface
    ifi = socket.if_nametoindex(IFN)
    ifis = struct.pack("I", ifi)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, ifis)

    # Set multicast group to join
    group = socket.inet_pton(socket.AF_INET6, MCAST_GROUP) + ifis
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, group)

    sock_addr = socket.getaddrinfo(
        MCAST_GROUP, MCAST_PORT, socket.AF_INET6, socket.SOCK_DGRAM)[0][4]
    sock.bind(sock_addr)

    cmd = ""
    while True:
        data, src = sock.recvfrom(1024)
        print("From " + str(src) + ": " + data.decode())


s = threading.Thread(target=sender('here'), args=(1,))
r = threading.Thread(target=receiver(), args=(1,))

s.start()
r.start()
