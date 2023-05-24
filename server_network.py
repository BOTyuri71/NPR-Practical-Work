import time
import threading
import socket
import struct
import server
import time


UDP_IP = "2001:0690:2280:0820::10" # = 0.0.0.0 u IPv4
UDP_PORT = 5000

class Server_network():
    def __init__(self):
        self.server = server.Server(50.0)

    def server_communication(self):
        sock = socket.socket(socket.AF_INET6, # Internet
						socket.SOCK_DGRAM) # UDP
        sock.bind((UDP_IP, UDP_PORT))

        while True:
            data, addr = sock.recvfrom(1024)
            self.server.logs.append(data.decode()) # buffer size is 1024 bytes
            self.packet_filter(data.decode())

            self.build_warning_velocity()
            time.sleep(1)
            self.build_warning_weather()
    
    def compare_times(self, tempo1, tempo2):
        tempo1 = time.strptime(tempo1, '%H:%M:%S')
        tempo2 = time.strptime(tempo2, '%H:%M:%S')

        diferenca = (tempo1.tm_hour - tempo2.tm_hour) * 3600 + \
                (tempo1.tm_min - tempo2.tm_min) * 60 + \
                (tempo1.tm_sec - tempo2.tm_sec)
    
        if diferenca < 0:
            if diferenca <= 3:
                return 0 
            else:
                return 1
        elif diferenca > 0:
            if diferenca >= 3:
                return 1
            else :
                return 0 
        else:
            return 0
        
    def verify_distance(self,posicao1, posicao2):
        if len(posicao1) != len(posicao2):
            return False

        distancia = sum((x - y) ** 2 for x, y in zip(posicao1, posicao2)) ** 0.5

        if distancia == 1:
            return True
        else:
            return False

    def warning_velocity_pdu_string(self,id,pos):
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        
        self.message = 'W V ' + str(current_time) + ' ' + id + ' ' + pos 

        return self.message
    
    def warning_weather_pdu_string(self,id,pos):
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        
        self.message = 'W W ' + str(current_time) + ' ' + id + ' ' + pos 

        return self.message
    
    def warning_accident_pdu_string(self,id1,pos1,id2,pos2):
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)

        if self.verify_distance(pos1,pos2) == True:
            self.message = 'W A ' + str(current_time) + ' ' + id1 + ' ' + id2

            return self.message


    def area_org(self,message):
        self.server.area_info.update({'Number of vehicles': len(message)})
        self.server.area_info.update({'Recommended velocity': self.server.recommended_vel})

        print(self.server.area_info)


    def data_org(self,message):

        self.server.vehicle_info.update({'Time': message[0][0]})
        self.server.vehicle_info.update({'Position': message[2][0]})
        self.server.vehicle_info.update({'Velocity': message[4][0]})
        self.server.vehicle_info.update({'Acceleration': message[4][1]})
        self.server.vehicle_info.update({'Direction': message[4][2]})
        self.server.vehicle_info.update({'Rain': message[5][0]})
        self.server.vehicle_info.update({'Fog': message[5][1]})
        self.server.vehicle_info.update({'Type': message[3][0]})
        self.server.vehicle_info.update({'Dimensions': message[3][1]})
        self.server.vehicle_info.update({'Weight': message[3][2]})

        self.server.all_vehicles_info.update({message[1][0]: self.server.vehicle_info})

        self.area_org(self.server.all_vehicles_info)
        print(self.server.all_vehicles_info)

    def packet_filter(self,message):
        temp2 = []

        temp = message.split(' ')
        temp.pop(0)
    
        for elem in temp:
            elem = elem.split(';')
            temp2.append(elem)

        print(temp2)
        self.data_org(temp2)

    def server_unicast_sender(self,message,ip,port):
        try:
            sock = socket.socket(socket.AF_INET6, # Internet
					socket.SOCK_DGRAM) # UDP
            sock.sendto(message.encode('utf-8'), (ip, int(port)))  
            sock.close()  
        except: 
            print("Conexão não é possível com " + ip + ' ' + str(port) + '!')

    def build_warning_velocity(self):

        if(len(self.server.all_vehicles_info) > 0):
            for key, value in self.server.all_vehicles_info.items():
                
                if float(value.get("Velocity")) > self.server.recommended_vel:
                    message = self.warning_velocity_pdu_string(key,value.get("Position"))
                    self.server_unicast_sender(message,'2001:0690:2280:0820::1',5005) 

    def build_warning_weather(self):

        if(len(self.server.all_vehicles_info) > 0):
            for key, value in self.server.all_vehicles_info.items():
                
                new_rec_vel = self.server.recommended_vel - 10.0
                if float(value.get("Velocity")) > new_rec_vel:
                    if (value.get("Rain") == 'True') and (value.get("Fog") == 'True'):
                        message = self.warning_weather_pdu_string(key,value.get("Position"))
                        self.server_unicast_sender(message,'2001:0690:2280:0820::1',5005)              

v = Server_network()

r = threading.Thread(target=v.server_communication())
r.daemon = True
r.start()

