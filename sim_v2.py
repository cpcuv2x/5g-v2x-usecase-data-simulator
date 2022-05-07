import calendar
import datetime
import json
import math
import random
import threading
import time
from typing import Dict

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from kafka import KafkaProducer
from pydantic import BaseModel

f = open('location/chula_route.txt', 'r')
location = [(l.split(',')[0], l.split(',')[1]) for l in f.readlines()]


class AddCarBody(BaseModel):
    id: str


class ImportCar:
    car_id: str
    driver_id: str
    cam_driver_id: str
    cam_door_id: str
    cam_front_id: str
    cam_back_id: str


class UpdateCarBody(BaseModel):
    id: str
    driverId: str
    camDriverId: str
    camDriverActive: bool
    camDoorId: str
    camDoorActive: bool
    camFrontId: str
    camFrontActive: bool
    camBackId: str
    camBackActive: bool
    accidentModuleActive: bool
    accidentProbability: float
    drowsinessModuleActive: bool
    drowsinessProbability: float
    ecrThreshold: float
    # additional
    kafkaEnable: bool
    kafkaBrokerUrl: str
    kafkaWebServiceTopic: str
    kafkaTelegrafTopic: str
    locationOffset: int
    locationInterval: int
    passengerInterval: int
    ecrInterval: int
    heartbeatInterval: int


class DeleteCarBody(BaseModel):
    id: str


class StartCarBody(BaseModel):
    id: str


class StopCarBody(BaseModel):
    id: str


class ResetCarBody(BaseModel):
    id: str


class Car:
    id: str
    active: bool
    driver_id: str
    cam_driver_id: str
    cam_driver_active: bool
    cam_door_id: str
    cam_door_active: bool
    cam_front_id: str
    cam_front_active: bool
    cam_back_id: str
    cam_back_active: bool
    accident_module_active: bool
    accident_probability: float
    drowsiness_module_active: bool
    drowsiness_probability: float
    ecr_threshold: float
    # additional
    kafka_enable: bool
    kafka_broker_url: bool
    kafka_web_service_topic: str
    kafka_telegraf_topic: str
    location_offset: int
    location_interval: int
    passenger_interval: int
    ecr_interval: int
    heartbeat_interval: int
    # variant
    cur_date_time: datetime.datetime
    i: int
    counter: int
    drowsiness_counter: int

    def __init__(self, id: str):
        self.id = id
        self.active = False
        self.driver_id = ""
        self.cam_driver_id = ""
        self.cam_driver_active = False
        self.cam_door_id = ""
        self.cam_door_active = False
        self.cam_front_id = ""
        self.cam_front_active = False
        self.cam_back_id = ""
        self.cam_back_active = False
        self.accident_module_active = False
        self.accident_probability = 0.000001
        self.drowsiness_module_active = False
        self.drowsiness_probability = 0.001
        self.ecr_threshold = 0.5
        # additional
        self.kafka_enable = True
        self.kafka_broker_url = "localhost:9092"
        self.kafka_web_service_topic = "cpcuv2x-events-web-service"
        self.kafka_telegraf_topic = "cpcuv2x-events-telegraf"
        self.location_interval = 1
        self.location_offset = 0
        self.passenger_interval = 60
        self.ecr_interval = 30
        self.heartbeat_interval = 60
        # variant
        self.cur_date_time = datetime.datetime(2022, 1, 1, 9, 0, 0, 0)
        self.i = self.location_offset
        self.counter = 0
        self.drowsiness_counter = -1

    def update(self, payload: UpdateCarBody):
        self.driver_id = payload.driverId
        self.cam_driver_id = payload.camDriverId
        self.cam_driver_active = payload.camDriverActive
        self.cam_door_id = payload.camDoorId
        self.cam_door_active = payload.camDoorActive
        self.cam_front_id = payload.camFrontId
        self.cam_front_active = payload.camFrontActive
        self.cam_back_id = payload.camBackId
        self.cam_back_active = payload.camBackActive
        self.accident_module_active = payload.accidentModuleActive
        self.accident_probability = payload.accidentProbability
        self.drowsiness_module_active = payload.drowsinessModuleActive
        self.drowsiness_probability = payload.drowsinessProbability
        self.ecr_threshold = payload.ecrThreshold
        # additional
        self.kafka_enable = payload.kafkaEnable
        self.kafka_broker_url = payload.kafkaBrokerUrl
        self.kafka_web_service_topic = payload.kafkaWebServiceTopic
        self.kafka_telegraf_topic = payload.kafkaTelegrafTopic
        self.location_interval = payload.locationInterval
        self.location_offset = payload.locationOffset
        self.passenger_interval = payload.passengerInterval
        self.ecr_interval = payload.ecrInterval
        self.heartbeat_interval = payload.heartbeatInterval

    def task(self):
        kafka_producer = None
        if self.kafka_enable:
            kafka_producer = KafkaProducer(
                bootstrap_servers=self.kafka_broker_url, value_serializer=lambda m: json.dumps(m).encode('ascii'))

        while self.active:
            cur_unix_time = int(calendar.timegm(
                self.cur_date_time.timetuple()))
            cur_lat, cur_lng = location[self.i][0], location[self.i][1]
            random_accident_chance, random_drowsiness_chance = random.uniform(
                0, 1), random.uniform(0, 1)
            random_passenger = random.randint(0, 9)
            if random_drowsiness_chance <= self.drowsiness_probability:
                random_ecr = round(random.uniform(
                    self.ecr_threshold, 1), 3)
                response_time = random.randint(0, 20)/10
                # set counter for the sending drowsiness event after the response time has passed
                self.drowsiness_counter = self.counter + \
                    math.ceil(response_time)
            else:
                random_ecr = round(random.uniform(
                    0, self.ecr_threshold-0.001), 3)
            # simulate accident
            if random_accident_chance <= self.accident_probability:
                accident_data = {'type': 'event', 'kind': 'accident', 'car_id': self.id,
                                 'driver_id': self.driver_id, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time}
                print(accident_data)
                if self.kafka_enable:
                    # line_protocol_producer.send(self.kafka_telegraf_topic, accident_data)
                    kafka_producer.send(
                        self.kafka_web_service_topic, accident_data)
            # simulate drowsiness
            if self.counter == self.drowsiness_counter:
                self.drowsiness_counter = -1
                drowsiness_data = {'type': 'event', 'kind': 'drowsiness_alarm', 'car_id': self.id, 'driver_id': self.driver_id,
                                   'response_time': response_time, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time}
                print(drowsiness_data)
                if self.kafka_enable:
                    # line_protocol_producer.send(self.kafka_telegraf_topic, drowsiness_data)
                    kafka_producer.send(
                        self.kafka_web_service_topic, drowsiness_data)
            # heartbeat
            if self.counter % self.heartbeat_interval == 0:
                cam_driver_status_data = {
                    'camera_id': self.cam_driver_id, 'status': 'active' if self.cam_driver_active else 'inactive'}
                cam_door_status_data = {
                    'camera_id': self.cam_door_id, 'status': 'active' if self.cam_door_active else 'inactive'}
                cam_front_status_data = {
                    'camera_id': self.cam_front_id, 'status': 'active' if self.cam_front_active else 'inactive'}
                cam_back_status_data = {
                    'camera_id': self.cam_back_id, 'status': 'active' if self.cam_back_active else 'inactive'}
                drowsiness_heatbeat_data = {
                    'status': 'active' if self.drowsiness_module_active else 'inactive'}
                accident_heatbeat_data = {
                    'status': 'active' if self.accident_module_active else 'inactive'}
                device_status = {'cam_driver': cam_driver_status_data, 'cam_door': cam_door_status_data, 'cam_front': cam_front_status_data,
                                 'cam_back': cam_back_status_data, 'drowsiness_module': drowsiness_heatbeat_data, 'accident_module': accident_heatbeat_data}
                heartbeat_data = {'type': 'heartbeat', 'kind': 'car', 'car_id': self.id, 'driver_id': self.driver_id,
                                  'time': cur_unix_time, 'lat': cur_lat, 'lng': cur_lng, 'device_status': device_status}
                print(heartbeat_data)
                if self.kafka_enable:
                    kafka_producer.send(
                        self.kafka_web_service_topic, heartbeat_data)
            # location
            if self.counter % self.location_interval == 0:
                location_data = {'type': 'metric', 'kind': 'car_location',
                                 'car_id': self.id, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time}
                print(location_data)
                if self.kafka_enable:
                    kafka_producer.send(
                        self.kafka_web_service_topic, location_data)
            # passenger
            if self.counter % self.passenger_interval == 0:
                passenger_data = {'type': 'metric', 'kind': 'car_passenger', 'car_id': self.id,
                                  'passenger': random_passenger, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time}
                print(passenger_data)
                if self.kafka_enable:
                    kafka_producer.send(
                        self.kafka_telegraf_topic, passenger_data)
                    kafka_producer.send(
                        self.kafka_web_service_topic, passenger_data)
            # ecr
            if self.counter % self.ecr_interval == 0:
                ecr_data = {'type': 'metric', 'kind': 'driver_ecr', 'car_id': self.id, 'ecr': random_ecr, 'ecr_threshold': self.ecr_threshold,
                            'driver_id': self.driver_id, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time}
                print(ecr_data)
                if self.kafka_enable:
                    kafka_producer.send(
                        self.kafka_telegraf_topic, ecr_data)
                    kafka_producer.send(
                        self.kafka_web_service_topic, ecr_data)
            self.i = (self.i+1) % len(location)
            self.counter += 1
            self.cur_date_time = self.cur_date_time + \
                datetime.timedelta(seconds=1)
            time.sleep(1)

    def start(self):
        if not self.active:
            self.active = True
            t = threading.Thread(target=self.task)
            t.setDaemon(True)
            t.start()

    def stop(self):
        self.active = False

    def reset(self):
        self.cur_date_time = datetime.datetime(2022, 1, 1, 9, 0, 0, 0)
        self.i = self.location_offset
        self.counter = 0
        self.drowsiness_counter = -1


class Simulator:
    cars: Dict[str, Car]

    def __init__(self):
        self.cars = dict()
        pass

    def add_car(self, payload: AddCarBody):
        self.cars[payload.id] = Car(payload.id)

    def import_car(self, payload: ImportCar):
        c = Car(payload.car_id)
        c.driver_id = payload.driver_id
        c.cam_driver_id = payload.cam_driver_id
        c.cam_door_id = payload.cam_door_id
        c.cam_front_id = payload.cam_front_id
        c.cam_back_id = payload.cam_back_id
        self.cars[payload.car_id] = c

    def update_car(self, payload: UpdateCarBody):
        self.cars.get(payload.id).update(payload)

    def delete_car(self, payload: DeleteCarBody):
        self.cars.get(payload.id).stop()
        self.cars.pop(payload.id)

    def start_car(self, payload: StartCarBody):
        self.cars.get(payload.id).start()

    def stop_car(self, payload: StopCarBody):
        self.cars.get(payload.id).stop()

    def reset_car(self, payload: ResetCarBody):
        self.cars.get(payload.id).reset()


class FastAPIApp(FastAPI):
    sim: Simulator
    templates: Jinja2Templates

    def __init__(self, sim: Simulator):
        super().__init__()
        self.sim = sim

        self.mount(
            "/static", StaticFiles(directory="static"), name="static")

        self.templates = Jinja2Templates(directory="templates")

        @self.get("/", response_class=HTMLResponse)
        async def get_page(request: Request):
            return self.templates.TemplateResponse("index.html", {"request": request, "cars": self.sim.cars.values(), "lenLocationOffset": len(location)})

        @self.post("/add-car")
        async def add_car(body: AddCarBody):
            self.sim.add_car(body)

        @self.post("/update-car")
        async def update_car(body: UpdateCarBody):
            self.sim.update_car(body)

        @self.post("/delete-car")
        async def delete_car(body: DeleteCarBody):
            self.sim.delete_car(body)

        @self.post("/start-car")
        async def start_car(body: StartCarBody):
            self.sim.start_car(body)

        @self.post("/stop-car")
        async def stop_car(body: StopCarBody):
            self.sim.stop_car(body)

        @self.post("/reset-car")
        async def reset_car(body: ResetCarBody):
            self.sim.reset_car(body)


sim = Simulator()
app = FastAPIApp(sim)

df = pd.read_csv('presets_v2.csv')

for i in range(0, len(df)):
    sim.import_car(df.iloc[i])
