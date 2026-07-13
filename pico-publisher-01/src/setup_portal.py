import network
import socket
import time
import machine

from config_manager import save_config

# numele retelei wi-fi create de pico w in modul access point
AP_SSID = "Pico-MQTT-Setup-01"

# parola pentru reteaua creata de pico w
AP_PASSWORD = "pico12345"

# fisierul html care contine formularul de configurare
HTML_FILE = "setup_page.html"


def url_decode(value):
    # browserul trimite spatiile ca +, deci le transform inapoi in spatii normale
    value = value.replace("+", " ")

    # unele caractere speciale pot veni codificate cu %, de exemplu %40 pentru @
    parts = value.split("%")
    result = parts[0]

    # refac caracterele codificate in format url
    for item in parts[1:]:
        if len(item) >= 2:
            try:
                # primele doua caractere dupa % sunt codul hexazecimal al caracterului
                result += chr(int(item[:2], 16)) + item[2:]
            except Exception:
                # daca nu se poate decoda, pastrez valoarea asa cum era
                result += "%" + item
        else:
            result += "%" + item

    return result


def parse_form_data(body):
    # transform datele primite din formular intr-un dictionar python
    # exemplu body: wifi_ssid=DIGI-5205&broker_ip=192.168.100.18&publish_qos=0
    data = {}

    # campurile din formular sunt separate prin &
    pairs = body.split("&")
    for pair in pairs:
        if "=" in pair:
            # fiecare camp are forma cheie=valoare
            key, value = pair.split("=", 1)

            # decodez si cheia, si valoarea, ca sa scap de + sau %xx
            data[url_decode(key)] = url_decode(value)

    return data


def load_html(message=""):
    # citesc pagina html folosita pentru formularul de configurare
    try:
        with open(HTML_FILE, "r") as f:
            html = f.read()

        # in pagina html am placeholder-ul {{message}}, pe care il inlocuiesc cu mesajul curent
        return html.replace("{{message}}", message)

    except Exception:
        # daca fisierul html lipseste, trimit o pagina simpla ca rezerva
        return "<html><body><h2>Pico W setup</h2><p>HTML file not found.</p></body></html>"


def send_html(conn, html):
    # construiesc raspunsul http pentru browser
    # status 200 ok inseamna ca cererea a fost procesata cu succes
    response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n"

    # trimit mai intai header-ele http
    conn.send(response.encode("utf-8"))

    # apoi trimit continutul paginii html
    conn.send(html.encode("utf-8"))


def get_content_length(headers):
    # caut in header-ele http linia content-length
    # aceasta spune cati bytes are corpul cererii, adica datele formularului
    lines = headers.split("\r\n")

    for line in lines:
        if line.lower().startswith("content-length:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except Exception:
                return 0

    # daca nu exista content-length, consider ca body-ul are lungime 0
    return 0


def read_http_request(conn):
    # citesc cererea http primita de la browser
    request = b""

    # header-ele http se termina cu secventa \r\n\r\n
    # citesc pana gasesc separarea dintre headers si body
    while b"\r\n\r\n" not in request:
        chunk = conn.recv(1024)
        if not chunk:
            break
        request += chunk

    # transform bytes in text
    request_text = request.decode("utf-8")

    # impart cererea in doua parti: headers si body
    parts = request_text.split("\r\n\r\n", 1)

    headers = parts[0]
    body = parts[1] if len(parts) > 1 else ""

    # aflu cati bytes ar trebui sa aiba body-ul complet
    content_length = get_content_length(headers)

    # uneori formularul nu ajunge tot dintr-un singur recv()
    # de aceea mai citesc pana cand body-ul are lungimea anuntata in content-length
    while len(body.encode("utf-8")) < content_length:
        chunk = conn.recv(1024)
        if not chunk:
            break
        body += chunk.decode("utf-8")

    return headers, body

# metoda principala access point setup portal, care porneste pico w in modul access point si asteapta ca utilizatorul sa introduca setarile in formular
def start_setup_portal(reason=""):
    # pornesc modul de configurare ap
    # in acest mod, pico w creeaza propria retea wi-fi si afiseaza pagina de configurare
    print("Starting setup portal")
    if reason:
        print("Reason:", reason)

    # opresc modul normal wi-fi, ca sa nu incurce pornirea access point-ului
    sta = network.WLAN(network.STA_IF)
    sta.active(False)
    time.sleep(1)

    # pregatesc interfata ap
    ap = network.WLAN(network.AP_IF)

    # opresc ap-ul daca era deja pornit, apoi il repornesc curat
    ap.active(False)
    time.sleep(1)

    ap.active(True)
    time.sleep(1)

    # configurez reteaua creata de pico w: nume, parola si canal wi-fi
    ap.config(essid=AP_SSID, password=AP_PASSWORD, channel=1)

    # astept pana cand ap-ul este activ
    while not ap.active():
        time.sleep(0.2)

    # ip-ul placii in reteaua creata de ea
    # de obicei este 192.168.4.1
    ip = ap.ifconfig()[0]

    print("Access Point started")
    print("SSID:", AP_SSID)
    print("Password:", AP_PASSWORD)
    print("Open: http://{}/".format(ip))

    # creez adresa pe care va asculta serverul http
    # portul 80 este portul standard pentru http
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]

    # creez socket-ul serverului http
    server = socket.socket()

    # permite refolosirea adresei daca serverul este repornit repede
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # leg serverul de adresa si port
    server.bind(addr)

    # serverul incepe sa astepte conexiuni
    # 1 inseamna ca pastreaza o conexiune in coada de asteptare
    server.listen(1)

    while True:
        # astept o conexiune de la browser
        conn, client_addr = server.accept()

        try:
            # citesc cererea http completa
            headers, body = read_http_request(conn)

            # daca utilizatorul a trimis formularul, cererea este post
            if headers.startswith("POST"):
                form = parse_form_data(body)

                # extrag valorile din formular
                wifi_ssid = form.get("wifi_ssid", "").strip()
                wifi_password = form.get("wifi_password", "").strip()
                broker_ip = form.get("broker_ip", "").strip()
                
                use_tls = form.get("use_tls", "off") == "on"

                # ssid-ul si ip-ul brokerului sunt obligatorii
                if not wifi_ssid or not broker_ip:
                    html = load_html("SSID and broker IP are required.")
                    send_html(conn, html)
                    conn.close()
                    continue

                # convertesc portul brokerului la int
                # daca valoarea nu este valida, folosesc portul standard mqtt 1883
                try:
                    default_port = "8883" if use_tls else "1883"
                    broker_port = int(form.get("broker_port", default_port))
                except Exception:
                    broker_port = 8883 if use_tls else 1883

                # convertesc qos-ul la int
                try:
                    publish_qos = int(form.get("publish_qos", "0"))
                except Exception:
                    publish_qos = 0

                # convertesc intervalul de publicare la int
                try:
                    publish_interval = int(form.get("publish_interval", "5"))
                except Exception:
                    publish_interval = 5

                # qos poate fi doar 0, 1 sau 2
                if publish_qos not in [0, 1, 2]:
                    publish_qos = 0

                # daca portul nu este valid, folosesc 1883
                if broker_port <= 0:
                    broker_port = 8883 if use_tls else 1883

                # daca intervalul nu este valid, folosesc 5 secunde
                if publish_interval <= 0:
                    publish_interval = 5

                # construiesc configuratia care va fi salvata in config.json
                config = {
                    "wifi_ssid": wifi_ssid,
                    "wifi_password": wifi_password,
                    "broker_ip": broker_ip,
                    "broker_port": broker_port,
                    "use_tls": use_tls,
                    "publish_qos": publish_qos,
                    "publish_interval": publish_interval
                }

                # salvez configuratia pe pico w
                save_config(config)

                print("Configuration saved:")
                print(config)

                # trimit mesaj in browser ca setarile au fost salvate
                html = load_html("Configuration saved. Pico W will restart.")
                send_html(conn, html)
                conn.close()

                # astept putin ca browserul sa primeasca raspunsul
                time.sleep(2)

                # restartez placa pentru a porni aplicatia cu noua configuratie
                machine.reset()

            else:
                # pentru cereri get, trimit pagina html cu formularul
                html = load_html(reason)
                send_html(conn, html)
                conn.close()

        except Exception as e:
            # daca apare o eroare la procesarea cererii, o afisez si inchid conexiunea
            print("Setup portal error:", e)
            try:
                conn.close()
            except Exception:
                pass
