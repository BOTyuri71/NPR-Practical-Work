import socket
import struct
import threading

recommended_vel = 50
logs = []
vehicle_info = {}
all_vehicles_info = {}
area_info = {}

UDP_IP = "::" # = 0.0.0.0 u IPv4
UDP_PORT = 5005

def area_org(message):
    area_info.update({'Number of vehicles': len(message)})
    area_info.update({'Recommended velocity':recommended_vel})

    print(area_info)


def data_org(message):

    vehicle_info.update({'Time': message[0][0]})
    vehicle_info.update({'Position': message[1][1]})
    vehicle_info.update({'Velocity': message[3][0]})
    vehicle_info.update({'Acceleration': message[3][1]})
    vehicle_info.update({'Direction': message[3][2]})
    vehicle_info.update({'Rain': message[4][0]})
    vehicle_info.update({'Fog': message[4][1]})
    vehicle_info.update({'Type': message[2][0]})
    vehicle_info.update({'Dimensions': message[2][1]})
    vehicle_info.update({'Weight': message[2][2]})

    all_vehicles_info.update({message[1][0]:vehicle_info})

    area_org(all_vehicles_info)
    print(all_vehicles_info)

def packet_filter(message):
    temp2 = []

    temp = message.split(' ')
    temp.pop(1)
    
    for elem in temp:
        elem = elem.split(';')
        temp2.append(elem)

    data_org(temp2)
        

def server_communication():
    sock = socket.socket(socket.AF_INET6, # Internet
						socket.SOCK_DGRAM) # UDP
    sock.bind((UDP_IP, UDP_PORT))

    data, addr = sock.recvfrom(1024)
    logs.append(data.decode()) # buffer size is 1024 bytes
    packet_filter(data.decode())

while True:
    r = threading.Thread(target=server_communication(), args=(1,))

    r.start()
