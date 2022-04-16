import random
import datetime
import time
import threading
import sys
import math

random.seed(0)

KAFKA_ENABLE = False
if len(sys.argv) > 1:
    argv1 = sys.argv[1]
    if argv1 == "--kafka-enable":
        KAFKA_ENABLE = True

if KAFKA_ENABLE:
    import json
    from kafka import KafkaProducer
    KAFKA_BROKER_URL = "localhost:9092"
    LINE_PROTOCOL_TOPIC = "cpcuv2x-events-for-influxdb"
    JSON_TOPIC = "cpcuv2x-events-for-web-service"
    line_protocol_producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER_URL, value_serializer=lambda m: json.dumps(m).encode('ascii'))
    json_producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER_URL, value_serializer=lambda m: json.dumps(m).encode('ascii'))

ACCIDENT_POSSIBILITY = 1/1000000
DROWSINESS_POSSIBILITY = 1/1000
ECR_THRESHOLD = 0.5

f = open('location/chula_route.txt', 'r')
location = [(l.split(',')[0], l.split(',')[1]) for l in f.readlines()]
f.close()
f = open('car.txt', 'r')
cars = [(l.split(',')[0].strip(), l.split(',')[1].strip(), l.split(',')[2].strip(), l.split(',')[3].strip(), l.split(',')[4].strip()) for l in f.readlines()[1:]]
f.close()
f = open('driver.txt', 'r')
drivers = [l.strip() for l in f.readlines()]
f.close()

def car_thread(car, driver, location_offset, location_interval=1, car_information_interval=60, heartbeat_interval=60):
    car_id, cam_driver_id, cam_door_id, cam_front_id, cam_back_id = car[0], car[1], car[2], car[3], car[4]
    cur_date_time = datetime.datetime(2022, 1, 1, 9, 0)
    cur_unix_time = int(time.mktime(cur_date_time.timetuple()))
    i = location_offset
    counter = 0
    drowsiness_counter = -1
    response_time = 0
    while True:
        cur_lat, cur_lng = location[i][0], location[i][1]
        random_accident_chance, random_drowsiness_chance = random.uniform(0, 1), random.uniform(0, 1)
        random_passenger = random.randint(0, 9)
        if random_drowsiness_chance <= DROWSINESS_POSSIBILITY:
            random_ecr = round(random.uniform(ECR_THRESHOLD, 1), 3)
            response_time = random.randint(0, 20)/10
            # set counter for the sending drowsiness event after the response time has passed
            drowsiness_counter = counter + math.ceil(response_time)
        else:
            random_ecr = round(random.uniform(0, ECR_THRESHOLD-0.001), 3)
        # simulate accident
        if random_accident_chance <= ACCIDENT_POSSIBILITY:
            accident_data = {'type':'event', 'kind': 'accident', 'car_id': car_id, 'driver_id': driver, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time}
            print(accident_data)
            if KAFKA_ENABLE:
                line_protocol_producer.send(LINE_PROTOCOL_TOPIC, accident_data)
                json_producer.send(LINE_PROTOCOL_TOPIC, accident_data)
        # simulate drowsiness
        if counter == drowsiness_counter:
            drowsiness_counter = -1
            drowsiness_data = {'type':'event', 'kind': 'drowsiness_alarm', 'car_id': car_id, 'driver_id': driver, 'response_time': response_time, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time}
            print(drowsiness_data)
            if KAFKA_ENABLE:
                line_protocol_producer.send(LINE_PROTOCOL_TOPIC, drowsiness_data)
                json_producer.send(LINE_PROTOCOL_TOPIC, drowsiness_data)
        # heartbeat
        if counter%heartbeat_interval == 0:
            cam_driver_status_data = {'camera_id': cam_driver_id, 'status': 'active'}
            cam_door_status_data = {'camera_id': cam_door_id, 'status': 'active'}
            cam_front_status_data = {'camera_id': cam_front_id, 'status': 'active'}
            cam_back_status_data = {'camera_id': cam_back_id, 'status': 'active'}
            drowsiness_heatbeat_data = {'status': 'active'}
            accident_heatbeat_data = {'status': 'active'}
            device_status = {'cam_driver': cam_driver_status_data, 'cam_door': cam_door_status_data, 'cam_front': cam_front_status_data, 'cam_back': cam_back_status_data, 'drowsiness_module': drowsiness_heatbeat_data, 'accident_module': accident_heatbeat_data}
            heartbeat_data = {'type':'heartbeat', 'kind': 'car', 'car_id': car_id, 'driver_id': driver, 'time': cur_unix_time, 'lat': cur_lat, 'lng': cur_lng, 'device_status': device_status}
            print(heartbeat_data)
            if KAFKA_ENABLE:
                line_protocol_producer.send(JSON_TOPIC, heartbeat_data)
        # location
        if counter%location_interval == 0:
            location_data = {'type':'metric', 'kind': 'car_location', 'car_id': car_id, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time}
            print(location_data)
            if KAFKA_ENABLE:
                json_producer.send(LINE_PROTOCOL_TOPIC, location_data)
        # car information
        if counter%car_information_interval == 0:
            car_information_data = {'type':'metric', 'kind': 'car_information', 'car_id': car_id, 'driver_id': driver, 'ecr': random_ecr, 'ecr_threshold': ECR_THRESHOLD, 'passenger': random_passenger, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time}
            print(car_information_data)
            if KAFKA_ENABLE:
                line_protocol_producer.send(LINE_PROTOCOL_TOPIC, car_information_data)
                json_producer.send(LINE_PROTOCOL_TOPIC, car_information_data)
        i = (i+1)%len(location)
        counter += 1
        cur_date_time = cur_date_time + datetime.timedelta(seconds=1)
        cur_unix_time = int(time.mktime(cur_date_time.timetuple()))
        time.sleep(1)

i = 0
for car in cars:
    threading.Thread(target=car_thread, args=[cars[i], drivers[i], int(i*5)], daemon=True).start()
    i += 1

while True:
    pass