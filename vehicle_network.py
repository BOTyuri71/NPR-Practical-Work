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
        self.neighbours_table_reverse = {}
        self.vehicle_states = {}
        self.my_warnings = {}
        self.warnings_queue = []
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

        header = str(self.vehicle.id) + ' ' + str(self.vehicle.x) + ',' + str(self.vehicle.y)
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
    
    def calculate_distance_warnings(self,position1,position2):
        
        position1_splited = position1.split(',')
        position1_int = [int(position1_splited[0]),int(position1_splited[1])]

        position2_splited = position2.split(',')
        position2_int = [int(position2_splited[0]),int(position2_splited[1])]
        
        return math.dist(position1_int, position2_int)

    def compare_distance(self):
        
        best_id = 'local'
        best_id_distance = 9999999

        for k, v in self.neighbours_table.items():
            if v.get('Distance') < best_id_distance:
                best_id = k
                best_id_distance = v.get('Distance')

        return best_id    
        
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
            if diferenca >= 200:
                return 3 
            else:
                return 1
        else:
            return 0
    
    def update_vehicle_states(self,message):
        vehicle_state_entry = {}
        
        message_splited = []
        message_splited = message.split(' ')

        if message_splited[2] not in self.vehicle_states:
            vehicle_state_entry.update({'Time': message_splited[1]})
            vehicle_state_entry.update({'Message': message})
            self.vehicle_states.update({message_splited[2]: vehicle_state_entry})
        elif message_splited[2] in self.vehicle_states:
            key = self.vehicle_states.get(message_splited[2])
            t = key.get("Time")
            if self.compare_times(message_splited[1],t) > -1 :
                vehicle_state_entry.update({'Time': message_splited[1]})
                vehicle_state_entry.update({'Message': message})
                self.vehicle_states.update({message_splited[2]: vehicle_state_entry})

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

    def update_warning(self,message):
        warning_table_entry = []
        
        message_splited = []
        message_splited = message.split(' ')
        print(message_splited)

        if message_splited[3] == str(self.id):
            if message_splited[1] == 'V':
                warning_table_entry.append('Cuidado! Está em excesso de velocidade. Reduza para sua segurança!')
            if message_splited[1] == 'W':
                warning_table_entry.append('Atenção! Está com uma velocidade elevada para as condições climatéricas atuais.')
            self.my_warnings.update({ message_splited[2]:warning_table_entry})
        else:
            self.warnings_queue.append(message)      

        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        t = str(current_time)

        for k in list(self.my_warnings.keys()):
            if self.compare_times(t,k) == 3:
                self.my_warnings.pop(k)

        print(self.my_warnings)
        print(self.warnings_queue)

        if len(self.warnings_queue) > 0:
            new_table = dict(self.neighbours_table)
            print(new_table)
            if "RSU" in new_table:
                new_table.pop("RSU")
            if "local" in new_table:
                new_table.pop("local")
            for k in new_table:
                dicionario_interno = new_table[k]
                dicionario_interno["Distance_to_dest"] = self.calculate_distance_warnings(message_splited[4],dicionario_interno.get("Position"))
            print(new_table)

            best_id = 'local'
            best_id_distance = 9999999

            for k, v in new_table.items():
                if v.get('Distance') < best_id_distance:
                    best_id = k
                    best_id_distance = v.get('Distance')  


            dest_items = new_table.get(str(best_id))
            self.vehicle_unicast_sender(str(self.warnings_queue[0]),dest_items.get("IP"),dest_items.get("Port"))
            del self.warnings_queue[0]
    
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

        # Associe o socket ao endereço link-local e porta
        sock.bind(target_address)

        while True:
            data, addr = sock.recvfrom(1024)
            message = data.decode()
            if message.startswith("ST "):
                self.update_vehicle_states(data.decode())      
                print(self.vehicle_states)    
            if message.startswith("W "):
                self.update_warning(message)

    def vehicle_multicast_sender(self):

        # Create ipv6 datagram socket
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 1)
    
        # Allow own messages to be sent back (for local testing)
        #sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, True)
        while True:
            sock.sendto(str(self.beacon_pdu_string()).encode('utf-8'), (MCAST_GROUP, MCAST_PORT))

            if 'RSU' in self.neighbours_table:
                rsu_items = self.neighbours_table.get("RSU")
                self.vehicle_unicast_sender(self.state_pdu_string(),rsu_items.get("IP"),rsu_items.get("Port"))
            elif str(self.compare_distance()) != 'local':  
               dest_items = self.neighbours_table.get(str(self.compare_distance()))
               self.vehicle_unicast_sender(self.state_pdu_string(),dest_items.get("IP"),dest_items.get("Port"))

            if len(self.vehicle_states) > 0:
                first_key = list(self.vehicle_states.keys())[0]
                key = self.vehicle_states.get(first_key)

                dest_items = self.neighbours_table.get(str(self.compare_distance()))

                self.vehicle_unicast_sender(key.get("Message"),dest_items.get("IP"),dest_items.get("Port"))
                del self.vehicle_states[first_key]

            time.sleep(3)    

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
            if message.startswith('B '):
                self.update_neighbours_table(message)
            if message.startswith('W '):
                self.update_warning(message)

parser = argparse.ArgumentParser()
parser.add_argument('id', type=int, help="Vehicle's ID")
parser.add_argument('ip', type=str, help="Vehicle's IP")
parser.add_argument('port', type=int, help="Vehicle's port")

args = parser.parse_args()

v = Vehicle_network(args.id,0,0)

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