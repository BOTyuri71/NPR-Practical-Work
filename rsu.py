import argparse
import socket
import struct
import threading
import time
import math
import vehicle
import re

MCAST_GROUP = 'FF16::1'
MCAST_PORT = 10000

class Rsu():
    def __init__(self,id,x,y):
        self.neighbours_table = {}
        self.from_vehicle_states = {}
        self.to_vehicle_warnings = []
        self.id = id
        self.x = x
        self.y = y
        self.udp_ip = "fe80::200:ff:feaa:62%eth2" 
        self.udp_port = 5005
        self.vehicle = vehicle.Vehicle(10,3,4)

    def beacon_pdu_string(self):
        ip = re.sub(r'%.*', '', self.udp_ip)

        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)


        beacon_message = str(self.id) + ' ' + str(self.x) + ',' + str(self.y)
        self.message =  'B ' + str(current_time) + ' ' + (ip) + ' ' + str(self.udp_port) + ' ' + beacon_message

        return self.message

    def state_pdu_string(self):
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)

        header = str(self.vehicle.id) + ' ' + str(self.vehicle.x) + ',' + str(self.vehicle.y)
        data_info = str(self.vehicle.type) + ';' + str(self.vehicle.w) + ',' + str(self.vehicle.h) + ';' + str(self.vehicle.weight)
        data_vel = str(self.vehicle.vel) + ';' + str(self.vehicle.acc) + ';' + str(self.vehicle.direction)
        data_sensors = str(self.vehicle.rain_sensor) + ';' + str(self.vehicle.fog_sensor)
        self.message = 'ST ' + str(current_time) + ' ' + header + ' ' + data_info + ' ' + data_vel + ' ' + data_sensors

        return self.message
        

    def calculate_distance(self,position):
        
        position_splited = position.split(',')
        position_int = [int(position_splited[0]),int(position_splited[1])]

        rsu = [self.x, self.y]
        
        return math.dist(position_int, rsu)

    def compare_times(self, tempo1, tempo2):
        tempo1 = time.strptime(tempo1, '%H:%M:%S')
        tempo2 = time.strptime(tempo2, '%H:%M:%S')

        diferenca = (tempo1.tm_hour - tempo2.tm_hour) * 3600 + \
                (tempo1.tm_min - tempo2.tm_min) * 60 + \
                (tempo1.tm_sec - tempo2.tm_sec)
    
        if diferenca < 0:
            return -1
        elif diferenca > 0:
            if diferenca >= 20:
                return 2 
            else:
                return 1
        else:
            return 0
    
    def update_from_vehicle_table(self,message):
        vehicle_state_entry = {}
        
        message_splited = []
        message_splited = message.split(' ')

        if message_splited[2] not in self.from_vehicle_states:
            vehicle_state_entry.update({'Time': message_splited[1]})
            vehicle_state_entry.update({'Message': message})
            self.from_vehicle_states.update({message_splited[2]: vehicle_state_entry})
        elif message_splited[2] in self.from_vehicle_states:
            key = self.from_vehicle_states.get(message_splited[2])
            t = key.get("Time")
            if self.compare_times(message_splited[1],t) > -1 :
                vehicle_state_entry.update({'Time': message_splited[1]})
                vehicle_state_entry.update({'Message': message})
                self.from_vehicle_states.update({message_splited[2]: vehicle_state_entry})

    def update_neighbours_table(self,message):
        neighbours_table_entry = {}
        message_splited = []

        message_splited = message.split(' ')

        neighbours_table_entry.update({'Time': message_splited[1]})
        neighbours_table_entry.update({'IP': message_splited[2]})
        neighbours_table_entry.update({'Port': message_splited[3]})
        neighbours_table_entry.update({'Position': message_splited[5]})
        neighbours_table_entry.update({'Distance': self.calculate_distance(message_splited[5])})

        if (message_splited[4] == str(self.id)) :
            self.neighbours_table.update({"local": neighbours_table_entry})
        else : 
            self.neighbours_table.update({message_splited[4]: neighbours_table_entry})
        
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        t = str(current_time)
        
        for k in list(self.neighbours_table.keys()):
            key = self.neighbours_table.get(k)
            t2 = key.get("Time")
            if self.compare_times(t,t2) == 2:
                self.neighbours_table.pop(k)

        print(self.neighbours_table)


    def rsu_unicast_sender(self,message,ip,port):
        sock = socket.socket(socket.AF_INET6, # Internet
					socket.SOCK_DGRAM) # UDP
        sock.sendto(str(message).encode('utf-8'), (ip, int(port)))
        sock.close()

    def rsu_unicast_receiver(self):
        
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

        for ainfo in socket.getaddrinfo(self.udp_ip, self.udp_port):
            if ainfo[0].name == 'AF_INET6' and ainfo[1].name == 'SOCK_DGRAM':
                target_address = ainfo[4]
                break

        # Associe o socket ao endereço link-local e porta
        sock.bind(target_address)

        while True:
            data, addr = sock.recvfrom(1024)
            self.update_from_vehicle_table(data.decode())     
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

            if len(self.from_vehicle_states) > 0:
                first_key = list(self.from_vehicle_states.keys())[0]
                key = self.from_vehicle_states.get(first_key)
                self.rsu_unicast_sender(key.get("Message"),'2001:0690:2280:0820::10',5000)
                del self.from_vehicle_states[first_key]
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
            message = data.decode('utf-8')
            self.update_neighbours_table(message)      


parser = argparse.ArgumentParser()
#parser.add_argument('ip', type=str, help="RSU's IP")
parser.add_argument('port', type=int, help="RSU's port")

args = parser.parse_args()
    
rsu = Rsu('RSU',628,66)
#rsu.udp_ip = args.ip
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
