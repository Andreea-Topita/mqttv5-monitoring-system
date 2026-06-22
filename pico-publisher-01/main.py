import time
from wifi import connect_wifi
from mqtt_client import MQTTClientPico
from temp_sensor import TempSensor
import ujson as json
from time_utils import sync_time, get_unix_time

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

USER_PROPERTIES = {
    "source_client_id": CLIENT_ID
}

# numele de baza SenML pentru dispozitiv
SENML_BASE_NAME = "urn:dev:" + CLIENT_ID + ":"


def build_senml_payload(measurement_name: str, unit: str, value) -> str:
    # Construim payload SenML in format JSON.
    # bn = base name / identificarea dispozitivului
    # n  = numele masuratorii
    # u  = unitatea de masura
    # v  = valoarea numerica
    # t  = timestamp Unix
    senml_record = [
        {
            "bn": SENML_BASE_NAME,
            "n": measurement_name,
            "u": unit,
            "v": float(value),
            "t": get_unix_time()
        }
    ]

    return json.dumps(senml_record)


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
    will_user_properties=USER_PROPERTIES
)

try:
    # connect wifi, apoi incearca sa ia timpul real, apoi se conecteaza la brokerul mqtt 
    connect_wifi(SSID, PASSWORD)

    # sincronizam timpul dupa conectarea la Wi-Fi
    sync_time()

    client.connect()

    # la conectare publica online cu retain
    # astfel un subscriber nou vede imediat ultima stare cunoscuta
    client.publish(
        TOPIC_STATUS,
        "online",
        qos=STATUS_QOS,
        retain=True,
        user_properties=USER_PROPERTIES
    )

    while True:
        try:
            temp, hum = sensor.read()

            temp_payload = build_senml_payload("temperature", "Cel", temp)
            hum_payload = build_senml_payload("humidity", "%RH", hum)

            print("Publishing temp:", temp_payload)
            client.publish(
                TOPIC_TEMP,
                temp_payload,
                qos=PUBLISH_QOS,
                retain=True,
                user_properties=USER_PROPERTIES
            )

            print("Publishing hum:", hum_payload)
            client.publish(
                TOPIC_HUM,
                hum_payload,
                qos=PUBLISH_QOS,
                retain=True,
                user_properties=USER_PROPERTIES
            )

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
            # daca aplicatia moare brusc, brokerul publica Will-ul offline
            client.publish(
                TOPIC_STATUS,
                "offline",
                qos=STATUS_QOS,
                retain=True,
                user_properties=USER_PROPERTIES
            )
    except:
        pass

    client.close()