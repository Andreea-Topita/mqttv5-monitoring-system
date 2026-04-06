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
TOPIC_STATUS = "licenta/pico/status"
TOPIC_TEMP = "licenta/pico/temperatura"
TOPIC_HUM = "licenta/pico/umiditate"

PUBLISH_QOS = 0
PUBLISH_INTERVAL = 5

sensor = TempSensor(gpio_pin=20)

client = MQTTClientPico(
    broker_ip=BROKER_IP,
    broker_port=BROKER_PORT,
    client_id=CLIENT_ID,
    keep_alive=10,
    will_topic=TOPIC_STATUS,
    will_payload="offline",
    will_qos=0,
)

try:
    connect_wifi(SSID, PASSWORD)
    client.connect()

    client.publish(TOPIC_STATUS, "online", qos=0)

    while True:
        temp, hum = sensor.read()

        print("Publishing temp:", temp)
        client.publish(TOPIC_TEMP, str(temp), qos=PUBLISH_QOS)

        print("Publishing hum:", hum)
        client.publish(TOPIC_HUM, str(hum), qos=PUBLISH_QOS)

        for _ in range(PUBLISH_INTERVAL):
            time.sleep(1)
            client.ping()

except Exception as e:
    print("Error:", e)
    client.close()