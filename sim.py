import random
import datetime
import time
import threading
import sys

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
    LINE_PROTOCOL_TOPIC = "LineProtocolTopic"
    JSON_TOPIC = "JSONTopic"
    line_protocol_producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER_URL, value_serializer=lambda m: json.dumps(m).encode('ascii'))
    json_producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER_URL, value_serializer=lambda m: json.dumps(m).encode('ascii'))

ACCIDENT_POSIBILITY = 1/1000000
DROWSINESS_POSIBILITY = 1/1000

f = open('location/chula_route.txt', 'r')
location = [(l.split(',')[0], l.split(',')[1]) for l in f.readlines()]
f.close()
f = open('car.txt', 'r')
cars = [(l.split(',')[0].strip(), l.split(',')[1].strip(), l.split(',')[2].strip(), l.split(',')[3].strip(), l.split(',')[4].strip()) for l in f.readlines()[1:]]
f.close()
f = open('driver.txt', 'r')
drivers = [l.strip() for l in f.readlines()]
f.close()

def car_thread(car, driver, location_offset, location_interval=1, passenger_interval=60, drowsiness_heartbeat=1800,
                accident_heartbeat=1800, cam_status_interval=60, car_status_interval=60):
    car_id, cam1_id, cam2_id, cam3_id, cam4_id = car[0], car[1], car[2], car[3], car[4]
    cur_date_time = datetime.datetime(2022, 1, 1, 9, 0)
    cur_unix_time = int(time.mktime(cur_date_time.timetuple()))
    i = location_offset
    counter = 0
    while True:
        cur_lat, cur_lng = location[i][0], location[i][1]
        # location
        if counter%location_interval == 0:
            location_data = {'car_id': car_id, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time, 'type': 'location'}
            print(location_data)
            if KAFKA_ENABLE:
                line_protocol_producer.send(LINE_PROTOCOL_TOPIC, location_data)
                json_producer.send(LINE_PROTOCOL_TOPIC, location_data)
        # passenger
        if counter%passenger_interval == 0:
            passenger_data = {'car_id': car_id, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time, 'type': 'passenger', 'passenger': random.randint(0, 9)}
            print(passenger_data)
            if KAFKA_ENABLE:
                line_protocol_producer.send(LINE_PROTOCOL_TOPIC, passenger_data)
                json_producer.send(LINE_PROTOCOL_TOPIC, passenger_data)
        # drowsiness
        if counter%drowsiness_heartbeat == 0:
            drowsiness_heatbeat_data = {'car_id': car_id, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time, 'type': 'drowsiness_heartbeat', 'ecr': random.randint(0, 40)/10}
            print(drowsiness_heatbeat_data)
            if KAFKA_ENABLE:
                line_protocol_producer.send(LINE_PROTOCOL_TOPIC, drowsiness_heatbeat_data)
                json_producer.send(LINE_PROTOCOL_TOPIC, drowsiness_heatbeat_data)
        # accident
        if counter%accident_heartbeat == 0:
            accident_heatbeat_data = {'car_id': car_id, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time, 'type': 'accident_heartbeat', 'status': 'active'}
            print(accident_heatbeat_data)
            if KAFKA_ENABLE:
                line_protocol_producer.send(LINE_PROTOCOL_TOPIC, accident_heatbeat_data)
                json_producer.send(LINE_PROTOCOL_TOPIC, accident_heatbeat_data)
        # camera status
        if counter%cam_status_interval == 0:
            cam1_status_data = {'car_id': car_id, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time, 'type': 'camera', 'camera_id': cam1_id, 'status': 'active'}
            cam2_status_data = {'car_id': car_id, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time, 'type': 'camera', 'camera_id': cam2_id, 'status': 'active'}
            cam3_status_data = {'car_id': car_id, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time, 'type': 'camera', 'camera_id': cam3_id, 'status': 'active'}
            cam4_status_data = {'car_id': car_id, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time, 'type': 'camera', 'camera_id': cam4_id, 'status': 'active'}
            print(cam1_status_data)
            print(cam2_status_data)
            print(cam3_status_data)
            print(cam4_status_data)
            if KAFKA_ENABLE:
                line_protocol_producer.send(LINE_PROTOCOL_TOPIC, cam1_status_data)
                line_protocol_producer.send(LINE_PROTOCOL_TOPIC, cam2_status_data)
                line_protocol_producer.send(LINE_PROTOCOL_TOPIC, cam3_status_data)
                line_protocol_producer.send(LINE_PROTOCOL_TOPIC, cam4_status_data)
                json_producer.send(LINE_PROTOCOL_TOPIC, cam1_status_data)
                json_producer.send(LINE_PROTOCOL_TOPIC, cam2_status_data)
                json_producer.send(LINE_PROTOCOL_TOPIC, cam3_status_data)
                json_producer.send(LINE_PROTOCOL_TOPIC, cam4_status_data)
        # car status
        if counter%car_status_interval == 0:
            car_status_data = {'car_id': car_id, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time, 'type': 'car_status', 'status': 'active'}
            print(car_status_data)
            if KAFKA_ENABLE:
                line_protocol_producer.send(LINE_PROTOCOL_TOPIC, car_status_data)
                json_producer.send(LINE_PROTOCOL_TOPIC, car_status_data)
        # simulate accident
        if random.uniform(0, 1) <= ACCIDENT_POSIBILITY:
            accident_data = {'car_id': car_id, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time, 'type': 'accident', 'driver_id': driver}
            print(accident_data)
            if KAFKA_ENABLE:
                line_protocol_producer.send(LINE_PROTOCOL_TOPIC, accident_data)
                json_producer.send(LINE_PROTOCOL_TOPIC, accident_data)
        # simulate drowsiness
        if random.uniform(0, 1) <= DROWSINESS_POSIBILITY:
            drowsiness_data = {'car_id': car_id, 'lat': cur_lat, 'lng': cur_lng, 'time': cur_unix_time, 'type': 'drowsiness', 'driver_id': driver, 'response_time': random.randint(0, 20)/10}
            print(drowsiness_data)
            if KAFKA_ENABLE:
                line_protocol_producer.send(LINE_PROTOCOL_TOPIC, drowsiness_data)
                json_producer.send(LINE_PROTOCOL_TOPIC, drowsiness_data)
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