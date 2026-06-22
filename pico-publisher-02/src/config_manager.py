import ujson as json

# numele fisierului in care se salveaza configuratia pe pico w
CONFIG_FILE = "config.json"

# valori implicite pentru configuratie
# sunt folosite daca lipseste vreo cheie din config.json
DEFAULT_CONFIG = {
    "wifi_ssid": "",
    "wifi_password": "",
    "broker_ip": "",
    "broker_port": 1883,
    "use_tls": False,
    "publish_qos": 0,
    "publish_interval": 5
}


def load_config():
    # incarca configuratia salvata din config.json
    # daca fisierul nu exista sau datele nu sunt valide, intoarce none
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.loads(f.read())

        # verific daca lipseste vreo cheie din fisier
        # daca lipseste, o completez cu valoarea implicita
        for key, value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = value

        # fara ssid si ip-ul brokerului nu pot porni aplicatia normal
        # in cazul acesta main.py va porni portalul de configurare
        if not config["wifi_ssid"] or not config["broker_ip"]:
            return None

        # daca totul este ok, returnez configuratia citita
        return config

    except Exception:
        # daca apare orice eroare la citire sau parsare, consider configuratia invalida
        return None


def save_config(config):
    # salveaza configuratia primita in fisierul config.json
    # configuratia vine de obicei din formularul din portalul ap
    with open(CONFIG_FILE, "w") as f:
        f.write(json.dumps(config))


def delete_config():
    # sterge fisierul config.json
    # este util daca vreau sa fortez placa sa intre din nou in modul ap
    try:
        import os
        os.remove(CONFIG_FILE)
    except Exception:
        # daca fisierul nu exista sau nu poate fi sters, nu opresc aplicatia
        pass

