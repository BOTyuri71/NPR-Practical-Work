import argparse
import threading
import socket
import struct
import vehicle
import time
import math
import re

MCAST_GROUP = 'FF16::1'
MCAST_PORT = 10000

class Vehicle_network():
    def __init__(self,id,x,y):
        self.neighbours_table = {}
        self.vehicle_states = []
        self.waiting_queue = []
        self.id = id
        self.x = x
        self.y = y
        self.vehicle = vehicle.Vehicle(self.id,self.x,self.y)
        self.udp_ip = "" 
        self.udp_port = 5005

    def beacon_pdu_string(self):
        ip = re.sub(r'%.*', '', self.udp_ip)
        
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)

        beacon_message = str(self.vehicle.id) + ' ' + str(self.vehicle.x) + ',' + str(self.vehicle.y)
        self.message =  'B ' + str(current_time)  + ' ' + str(ip) + ' ' + str(self.udp_port) + ' ' + beacon_message

        return self.message
    
    def state_pdu_string(self):
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)

        header = str(self.vehicle.id) + ';' + str(self.vehicle.x) + ',' + str(self.vehicle.y)
        data_info = str(self.vehicle.type) + ';' + str(self.vehicle.w) + ',' + str(self.vehicle.h) + ';' + str(self.vehicle.weight)
        data_vel = str(self.vehicle.vel) + ';' + str(self.vehicle.acc) + ';' + str(self.vehicle.direction)
        data_sensors = str(self.vehicle.rain_sensor) + ';' + str(self.vehicle.fog_sensor)
        self.message = 'ST ' + str(current_time) + ' ' + header + ' ' + data_info + ' ' + data_vel + ' ' + data_sensors

        return self.message
    
    def calculate_distance(self,position):
        
        position_splited = position.split(',')
        position_int = [int(position_splited[0]),int(position_splited[1])]

        rsu = [628, 66]
        
        return math.dist(position_int, rsu)

    def compare_distance(self):
        
        best_id = 'local'
        best_id_distance = 9999999

        for k, v in self.neighbours_table.items():
            if v.get('Distance') < best_id_distance:
                best_id = k
                best_id_distance = v.get('Distance')

        return best_id    
        

    def update_neighbours_table(self,message):
        neighbours_table_entry = {}
        message_splited = []

        message_splited = message.split(' ')
        print(message_splited)

        neighbours_table_entry.update({'Time': message_splited[1]})
        neighbours_table_entry.update({'IP': message_splited[2]})
        neighbours_table_entry.update({'Port': message_splited[3]})
        neighbours_table_entry.update({'Position': message_splited[5]})
        neighbours_table_entry.update({'Distance': self.calculate_distance(message_splited[5])})

        if (message_splited[4] == str(self.id)) :
            self.neighbours_table.update({"local": neighbours_table_entry})
        else : 
            self.neighbours_table.update({message_splited[4]: neighbours_table_entry})
        
        print(self.neighbours_table)

    def vehicle_unicast_sender(self,message,ip,port):
        try:
            sock = socket.socket(socket.AF_INET6, # Internet
					socket.SOCK_DGRAM) # UDP
            sock.sendto(message.encode('utf-8'), (ip, int(port)))  
            sock.close()  
        except: 
            print("Conexão não é possível com " + ip + ' ' + str(port) + '!')

    def vehicle_unicast_receiver(self):

        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

        for ainfo in socket.getaddrinfo(self.udp_ip, self.udp_port):
            if ainfo[0].name == 'AF_INET6' and ainfo[1].name == 'SOCK_DGRAM':
                target_address = ainfo[4]
                break

        print(str(target_address))

        # Associe o socket ao endereço link-local e porta
        sock.bind(target_address)

        while True:
            data, addr = sock.recvfrom(1024)
            self.vehicle_states.append(str(addr) + ' ' + data.decode())      
            print(self.vehicle_states)    


    def vehicle_multicast_sender(self):

        # Create ipv6 datagram socket
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 1)
    
        # Allow own messages to be sent back (for local testing)
        #sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, True)
        while True:
            sock.sendto(str(self.beacon_pdu_string()).encode('utf-8'), (MCAST_GROUP, MCAST_PORT))
            time.sleep(5)    

    def vehicle_multicast_receive(self):

        # Create IPv6 datagram socket
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

        # Allows address to be reused
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Binds to all interfaces on the given port
        sock.bind(('', MCAST_PORT))

        #Allow messages from this socket to loop back for development
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, True)

        # Construct message for joining multicast group
        mreq = struct.pack("16s15s".encode('utf-8'),socket.inet_pton(socket.AF_INET6, MCAST_GROUP), (chr(0) *16).encode('utf-8'))
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)


        while True:
            # Receive the multicast message
            data, address = sock.recvfrom(1024)
            # Process the received message here
            message =  data.decode('utf-8')
            self.update_neighbours_table(message)

            if 'RSU' in self.neighbours_table:
                rsu_items = self.neighbours_table.get("RSU")
                self.vehicle_unicast_sender(self.state_pdu_string(),rsu_items.get("IP"),rsu_items.get("Port"))
            #elif str(self.compare_distance()) != 'local':  
            #    dest_items = self.neighbours_table.get(str(self.compare_distance()))
            #    print(str(dest_items))
            #    self.vehicle_unicast_sender(self.state_pdu_string(),dest_items.get("IP"),dest_items.get("Port"))


parser = argparse.ArgumentParser()
parser.add_argument('id', type=int, help="Vehicle's ID")
parser.add_argument('ip', type=str, help="Vehicle's IP")
parser.add_argument('port', type=int, help="Vehicle's port")

args = parser.parse_args()

v = Vehicle_network(args.id,10,20)

v.udp_ip = args.ip
v.udp_port = args.port

r = threading.Thread(target=v.vehicle_multicast_receive)
r.daemon = True
r.start()
s = threading.Thread(target=v.vehicle_multicast_sender)
s.daemon = True
s.start()
ur = threading.Thread(target=v.vehicle_unicast_receiver)
ur.daemon = True
ur.start()

while True:
    pass