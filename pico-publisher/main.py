import time
from wifi import connect_wifi
from mqtt_client import MQTTClientPico
from temp_sensor import TempSensor

#parola internet de acasa 
SSID = "Digi-5205"
PASSWORD = "SPGgu6wJ"

BROKER_IP = "192.168.100.18"   # ip ul laptopului
BROKER_PORT = 1883

CLIENT_ID = "pico_temp_01"
TOPIC_TEMP = "licenta/pico/temperatura"

sensor = TempSensor(gpio_pin=20)

client = MQTTClientPico(
    broker_ip=BROKER_IP,
    broker_port=BROKER_PORT,
    client_id=CLIENT_ID,
    keep_alive=10,
    will_topic="licenta/pico/status",
    will_payload="offline",
    will_qos=0,
)

try:
    connect_wifi(SSID, PASSWORD)
    client.connect()

    client.publish("licenta/pico/status", "online", qos=0)

    while True:
        temp, hum = sensor.read()

        payload = "{{\"temperature\": {}, \"humidity\": {}}}".format(temp, hum)

        print("Publishing:", payload)
        client.publish(TOPIC_TEMP, payload, qos=0)

        for _ in range(5):
            time.sleep(1)
            client.ping()

except Exception as e:
    print("Error:", e)
    client.close()
