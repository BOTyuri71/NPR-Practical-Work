import argparse
import socket
import struct
import threading
import time
import math
import vehicle

MCAST_GROUP = 'FF16::1'
MCAST_PORT = 10000

class Rsu():
    def __init__(self,id,x,y):
        self.neighbours_table = {}
        self.from_vehicle_states = []
        self.to_vehicle_warnings = []
        self.id = id
        self.x = x
        self.y = y
        self.udp_ip = "" 
        self.udp_port = 5005
        self.vehicle = vehicle.Vehicle(10,3,4)

    def state_pdu_string(self):
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)

        header = str(self.vehicle.id) + ';' + str(self.vehicle.x) + ',' + str(self.vehicle.y)
        data_info = str(self.vehicle.type) + ';' + str(self.vehicle.w) + ',' + str(self.vehicle.h) + ';' + str(self.vehicle.weight)
        data_vel = str(self.vehicle.vel) + ';' + str(self.vehicle.acc) + ';' + str(self.vehicle.direction)
        data_sensors = str(self.vehicle.rain_sensor) + ';' + str(self.vehicle.fog_sensor)
        self.message = str(current_time) + ' ST' + ' ' + header + ' ' + data_info + ' ' + data_vel + ' ' + data_sensors

        return self.message
        
    def beacon_pdu_string(self):
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)

        beacon_message = str(self.id) + ' ' + str(self.x) + ',' + str(self.y)
        self.message = str(self.udp_port) + ' ' + str(current_time) + ' B ' + beacon_message

        return self.message

    def calculate_distance(self,position):
        
        position_splited = position.split(',')
        position_int = [int(position_splited[0]),int(position_splited[1])]

        rsu = [self.x, self.y]
        
        return math.dist(position_int, rsu)

    def update_neighbours_table(self,message):
        neighbours_table_entry = {}
        message_splited = []

        message_splited = message.split(' ')

        neighbours_table_entry.update({'IP': message_splited[0]})
        neighbours_table_entry.update({'Port': message_splited[1]})
        neighbours_table_entry.update({'Position': message_splited[5]})
        neighbours_table_entry.update({'Distance': self.calculate_distance(message_splited[5])})

        if (message_splited[4] == str(self.id)) :
            self.neighbours_table.update({"local": neighbours_table_entry})
        else : 
            self.neighbours_table.update({message_splited[4]: neighbours_table_entry})
        
        print(self.neighbours_table)  

    def rsu_unicast_sender(self,message,ip,port):
        sock = socket.socket(socket.AF_INET6, # Internet
					socket.SOCK_DGRAM) # UDP
        sock.sendto(str(message).encode('utf-8'), (ip, int(port)))
        sock.close()

    def rsu_unicast_receiver(self):
        sock = socket.socket(socket.AF_INET6, # Internet
						socket.SOCK_DGRAM) # UDP
        sock.bind((self.udp_ip, self.udp_port))

        while True:
            data, addr = sock.recvfrom(1024)
            print(data.decode())
            self.from_vehicle_states.append(str(addr) + ' ' + data.decode())      
            print(self.from_vehicle_states)    

    def rsu_multicast_sender(self):

        # Create ipv6 datagram socket
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 1)

        ifn = "eth2"
        ifi = socket.if_nametoindex(ifn)
        ifis = struct.pack("I", ifi)
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, ifis)
    
        # Allow own messages to be sent back (for local testing)
        #sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, True)
        while True:
            sock.sendto(str(self.beacon_pdu_string()).encode('utf-8'), (MCAST_GROUP, MCAST_PORT))
            #.rsu_unicast_sender(self.state_pdu_string(),"::1",5005)
            time.sleep(5)
            
    def rsu_multicast_receiver(self):
        # Initialise socket for IPv6 datagrams
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        # Allows address to be reused
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Binds to all interfaces on the given port
        sock.bind((MCAST_GROUP, MCAST_PORT))

        # Allow messages from this socket to loop back for development
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, True)

        # Construct message for joining multicast group
        face_name = 'eth2'
        face_index = socket.if_nametoindex(face_name)
        mreq = struct.pack("16si".encode('utf-8'), socket.inet_pton(socket.AF_INET6, MCAST_GROUP), face_index)
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)

        print('listening on port:', sock.getsockname()[1])
     
        while True:
            # Receive the multicast message
            data, address = sock.recvfrom(1024)
            # Process the received message here
            message = address[0] + ' ' + data.decode('utf-8')
            self.update_neighbours_table(message)      


parser = argparse.ArgumentParser()
parser.add_argument('ip', type=str, help="RSU's IP")
parser.add_argument('port', type=int, help="RSU's port")

args = parser.parse_args()
    
rsu = Rsu('RSU',628,66)
rsu.udp_ip = args.ip
rsu.udp_port = args.port

r = threading.Thread(target=rsu.rsu_multicast_receiver)
r.daemon = True
r.start()
s = threading.Thread(target=rsu.rsu_multicast_sender)
s.daemon = True
s.start()
ur = threading.Thread(target=rsu.rsu_unicast_receiver)
ur.daemon = True
ur.start()

while(True):
    pass
