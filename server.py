class Server():
    def __init__(self,vel):
        self.vehicle_info = {}
        self.all_vehicles_info = {}
        self.area_info = {}
        self.logs = []
        self.recommended_vel = vel

    def area_org(self,message):
        self.area_info.update({'Number of vehicles': len(message)})
        self.area_info.update({'Recommended velocity': self.recommended_vel})

        print(self.area_info)


    def data_org(self,message):

        self.vehicle_info.update({'Time': message[0][0]})
        self.vehicle_info.update({'Position': message[2][0]})
        self.vehicle_info.update({'Velocity': message[4][0]})
        self.vehicle_info.update({'Acceleration': message[4][1]})
        self.vehicle_info.update({'Direction': message[4][2]})
        self.vehicle_info.update({'Rain': message[5][0]})
        self.vehicle_info.update({'Fog': message[5][1]})
        self.vehicle_info.update({'Type': message[3][0]})
        self.vehicle_info.update({'Dimensions': message[3][1]})
        self.vehicle_info.update({'Weight': message[3][2]})

        self.all_vehicles_info.update({message[1][0]: self.vehicle_info})

        self.area_org(self.all_vehicles_info)
        print(self.all_vehicles_info)

    def packet_filter(self,message):
        temp2 = []

        temp = message.split(' ')
        temp.pop(0)
    
        for elem in temp:
            elem = elem.split(';')
            temp2.append(elem)

        print(temp2)
        self.data_org(temp2)