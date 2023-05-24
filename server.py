import time
import socket

class Server():
    def __init__(self,vel):
        self.vehicle_info = {}
        self.all_vehicles_info = {}
        self.area_info = {}
        self.logs = []
        self.recommended_vel = vel

    