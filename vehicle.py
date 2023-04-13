import time


class Vehicle():
    def __init__(self,id,x,y):
        self.id = id
        self.x = x
        self.y = y

        self.type = "FIAT"
        self.w = 0
        self.h = 0
        self.weight = 0.0

        self.vel = 0.0
        self.acc = 2.0
        self.direction = 'north'

        self.rain_sensor = False
        self.fog_sensor = False

        self.message = ''

    def nextVel(self,time):
        self.vel = self.vel + time*self.acc
    
    def state_pdu_string(self):
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)

        header = str(self.id) + ';' + str(self.x) + ',' + str(self.y)
        data_info = str(self.type) + ';' + str(self.w) + ',' + str(self.h) + ';' + str(self.weight)
        data_vel = str(self.vel) + ';' + str(self.acc) + ';' + str(self.direction)
        data_sensors = str(self.rain_sensor) + ';' + str(self.fog_sensor)
        self.message = str(current_time) + ' ST' + ' ' + header + ' ' + data_info + ' ' + data_vel + ' ' + data_sensors