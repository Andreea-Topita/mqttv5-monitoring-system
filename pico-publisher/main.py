import time
from wifi import connect_wifi
from mqtt_client import MQTTClientPico
from temp_sensor import TempSensor

#parola internet de acasa 
SSID = "DIGI-5205"
PASSWORD = "SPGgu6wJ"

# broker mqtt
BROKER_IP = "192.168.100.18"   # ip ul laptopului
BROKER_PORT = 1883

# identificare client si topicuri
CLIENT_ID = "pico_temp_01"
TOPIC_STATUS = "licenta/pico/status"
TOPIC_TEMP = "licenta/pico/temperatura"
TOPIC_HUM = "licenta/pico/umiditate"

# qos pentru datele senzorului
PUBLISH_QOS = 0

# qos separat pentru topicul de status
STATUS_QOS = 1

# la cate secunde se publica valorile
PUBLISH_INTERVAL = 5

sensor = TempSensor(gpio_pin=20)

client = MQTTClientPico(
    broker_ip=BROKER_IP,
    broker_port=BROKER_PORT,
    client_id=CLIENT_ID,
    keep_alive=10,
    will_topic=TOPIC_STATUS,
    will_payload="offline",
    will_qos=1,
    will_retain=True,
)
try:
    connect_wifi(SSID, PASSWORD)
    client.connect()

    # la conectare publica online cu retain
    # astfel un subscriber nou vede imediat ultimul status
    client.publish(TOPIC_STATUS, "online", qos=STATUS_QOS, retain=True)

    while True:
        try:
            temp, hum = sensor.read()

            print("Publishing temp:", temp)
            client.publish(TOPIC_TEMP, str(temp), qos=PUBLISH_QOS, retain=False)

            print("Publishing hum:", hum)
            client.publish(TOPIC_HUM, str(hum), qos=PUBLISH_QOS, retain=False)

        except Exception as sensor_error:
            print("Sensor read error:", sensor_error)

        for _ in range(PUBLISH_INTERVAL):
            time.sleep(1)
            client.ping()

except Exception as e:
    print("Error:", e)

finally:
    try:
        if client.connected:
            # la inchidere normala publicam noi offline
            # daca aplicatia moare brusc, brokerul publica will-ul offline
            client.publish(TOPIC_STATUS, "offline", qos=STATUS_QOS, retain=True)
    except:
        pass

    client.close()