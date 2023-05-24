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

        self.vel = 60.0
        self.acc = 2.0
        self.direction = 'north'

        self.rain_sensor = True
        self.fog_sensor = True

        self.message = ''

    def nextVel(self,time):
        self.vel = self.vel + time*self.acc
    