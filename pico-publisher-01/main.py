import time
import ujson as json
from wifi import connect_wifi
from mqtt_client import MQTTClientPico
from temp_sensor import TempSensor
from time_utils import sync_time, get_unix_time
from config_manager import load_config, save_config
from setup_portal import start_setup_portal

# identificare client si topicuri
CLIENT_ID = "pico_temp_01"

TOPIC_STATUS = "licenta/{}/status".format(CLIENT_ID)
TOPIC_TEMP = "licenta/{}/temperatura".format(CLIENT_ID)
TOPIC_HUM = "licenta/{}/umiditate".format(CLIENT_ID)
TOPIC_CONFIG = "licenta/{}/config".format(CLIENT_ID)

# qos separat pentru topicul de status
STATUS_QOS = 1

USER_PROPERTIES = {
    "source_client_id": CLIENT_ID
}

# numele de baza SenML pentru dispozitiv
SENML_BASE_NAME = "urn:dev:" + CLIENT_ID + ":"


def build_senml_payload(measurement_name: str, unit: str, value) -> str:
    # Construim payload SenML in format JSON
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


# incarcam configuratia salvata din portalul AP
config = load_config()

# daca nu exista configuratie, placa intra in modul de configurare
if config is None:
    start_setup_portal("No saved configuration found.")

SSID = config["wifi_ssid"]
PASSWORD = config["wifi_password"]
BROKER_IP = config["broker_ip"]
BROKER_PORT = config["broker_port"]
USE_TLS = config.get("use_tls", False)
PUBLISH_QOS = config["publish_qos"]
PUBLISH_INTERVAL = config["publish_interval"]

runtime_config = {
    "publish_qos": PUBLISH_QOS,
    "publish_interval": PUBLISH_INTERVAL
}

sensor = TempSensor(gpio_pin=20)
client = None


def handle_config_message(topic: str, message: str):
    # primeste configurari venite pe topicul licenta/<client_id>/config
    global config

    if topic != TOPIC_CONFIG:
        return

    try:
        data = json.loads(message)
    except Exception as e:
        print("invalid config json:", e)
        return

    new_qos = data.get("publish_qos")
    new_interval = data.get("publish_interval")

    if new_qos is not None:
        try:
            new_qos = int(new_qos)

            if new_qos in [0, 1, 2]:
                runtime_config["publish_qos"] = new_qos
                config["publish_qos"] = new_qos
                print("publish_qos updated to", new_qos)

        except Exception as e:
            print("invalid publish_qos:", e)

    if new_interval is not None:
        try:
            new_interval = int(new_interval)

            if new_interval > 0:
                runtime_config["publish_interval"] = new_interval
                config["publish_interval"] = new_interval
                print("publish_interval updated to", new_interval)

        except Exception as e:
            print("invalid publish_interval:", e)

    try:
        save_config(config)
        print("config saved after remote update")
    except Exception as e:
        print("could not save config:", e)
        
def wait_and_process_mqtt(seconds):
    # asteapta pana la urmatoarea publicare
    # in acest timp proceseaza mesajele mqtt primite
    end_time = time.time() + seconds

    while time.time() < end_time:
        if not client.connected:
            raise OSError("MQTT connection lost")

        client.loop_once(timeout_ms=200)
        client.ping()
        
try:
    # conectare la reteaua Wi-Fi configurata
    try:
        wlan = connect_wifi(SSID, PASSWORD)
    except Exception as wifi_error:
        print("Wi-Fi error:", wifi_error)
        start_setup_portal("Wi-Fi connection failed. Please configure again.")

    # sincronizam ceasul placii dupa conectarea la Wi-Fi
    # daca sincronizarea esueaza, aplicatia continua cu valoarea existenta in RTC
    time_synchronized = sync_time(retries=3, retry_delay=2)

    if not time_synchronized:
        print("Time sync warning: using current RTC time.")

    # cream clientul MQTT folosind brokerul salvat in config.json
    client = MQTTClientPico(
        broker_ip=BROKER_IP,
        broker_port=BROKER_PORT,
        client_id=CLIENT_ID,
        keep_alive=30,
        will_topic=TOPIC_STATUS,
        will_payload="offline",
        will_qos=STATUS_QOS,
        will_retain=True,
        will_user_properties=USER_PROPERTIES,
        use_tls=USE_TLS
    )
    
    # conectare la brokerul MQTT
    try:
        client.connect()
    except Exception as mqtt_error:
        print("MQTT error:", mqtt_error)
        start_setup_portal("MQTT broker connection failed. Please check broker IP.")

    # configuram functia care proceseaza mesajele de configurare
    client.set_message_callback(handle_config_message)

    # placa se aboneaza la propriul topic de configurare
    client.subscribe(TOPIC_CONFIG, qos=0)
    
    # la conectare publica online cu retain
    # astfel un subscriber nou vede imediat ultima stare cunoscuta
    client.publish(
        TOPIC_STATUS,
        "online",
        qos=STATUS_QOS,
        retain=True,
        user_properties=USER_PROPERTIES
    )

    print("Configuration loaded")
    print("SSID:", SSID)
    print("Broker:", BROKER_IP, BROKER_PORT)
    print("Use TLS:", USE_TLS)
    print("Publish QoS:", PUBLISH_QOS)
    print("Publish interval:", PUBLISH_INTERVAL)

    
    while True:
        if not wlan.isconnected():
            print("Wi-Fi connection lost")
            raise OSError("Wi-Fi connection lost")
        
        current_qos = runtime_config["publish_qos"]
        current_interval = runtime_config["publish_interval"]

        try:
            temp, hum = sensor.read()
        except Exception as sensor_error:
            print("Sensor read error:", sensor_error)
            
            wait_and_process_mqtt(current_interval)

            continue
        
        try:
            temp_payload = build_senml_payload("temperature", "Cel", temp)
            hum_payload = build_senml_payload("humidity", "%RH", hum)

            print("Publishing temp:", temp_payload)
            print("Current QoS:", current_qos)

            client.publish(
                TOPIC_TEMP,
                temp_payload,
                qos=current_qos,
                retain=False,
                user_properties=USER_PROPERTIES
            )

            print("Publishing hum:", hum_payload)
            print("Current QoS:", current_qos)

            client.publish(
                TOPIC_HUM,
                hum_payload,
                qos=current_qos,
                retain=False,
                user_properties=USER_PROPERTIES
            )


        except Exception as mqtt_error:
            print("MQTT publish error:", mqtt_error)
            raise
        
        wait_and_process_mqtt(current_interval)

except Exception as e:
    print("Error:", e)

finally:
    try:
        if client is not None and client.connected:
            # la inchidere normala publicam noi offline
            # daca aplicatia moare brusc, brokerul publica Will-ul offline
            client.publish(
                TOPIC_STATUS,
                "offline",
                qos=STATUS_QOS,
                retain=True,
                user_properties=USER_PROPERTIES
            )
    except Exception:
        pass

    try:
        if client is not None:
            client.close()
    except Exception:
        pass
