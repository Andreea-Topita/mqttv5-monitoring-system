from src.infrastructure.mqtt.packet_builder import PacketBuilder
from src.infrastructure.mqtt.packet_parser import PacketParser
import socket
import threading
import time
import ssl

class MQTTClient:
    def __init__(self, client_id,on_message_callback=None):

        self.client_id = client_id
        self.username = ''
        self.password = ''
        self.topic=''
        self.keep_alive=10

        #lw
        self.lw_topic = None
        self.lw_payload = None
        self.lw_qos = None
        self.lw_retain = False

        #pt conexiune
        self.socket = None
        self.encoder = PacketBuilder()
        self.decoder = PacketParser()
        self.connected = False

        self.packet_id=1    #se incrementeaza pentru fiecare pachet trimis cu qos > 0

        #setat la momentul curent
        self.last_ping = time.time()  #retinem momentul ultimei trimiteri a unui mesaj pingreq
        #utilizat pt a verifica daca trebuie trimit un alt ping pentru a mentine conexiunea activa
        
        self.use_tls = False
        self.ca_cert_path = "/app/certs/ca.crt"
        self.tls_insecure = False

        # legatura ditntre partea de protocol si partea de aplicatie
        self.on_message_callback = on_message_callback
        
    # daca use tls false, clinet va folosi mqtt simplu pe tcp, true wrap socket in conexiune tls , ca cert path : certificat ca folosit pentru a verifica brokerul
    def tls_set(self, use_tls: bool, ca_cert_path: str = "/app/certs/ca.crt", tls_insecure: bool = False):
        self.use_tls = use_tls
        self.ca_cert_path = ca_cert_path
        self.tls_insecure = tls_insecure
    
    # decodare remaining length din pachetul mqtt, returneaza valoarea si numarul de bytes consumati pentru codarea acestei lungimi
    # fiecare octet are bitul 7 ca flag de continuare, iar restul 7 biti reprezinta valoarea
    def _decode_remaining_length(self, data, start_index=1):
        multiplier = 1
        value = 0
        index = start_index

        while True:
            if index >= len(data):
                return None, 0

            encoded_byte = data[index]
            value += (encoded_byte & 127) * multiplier
            index += 1

            if (encoded_byte & 128) == 0:
                break

            multiplier *= 128

        return value, index - start_index

    # extragerea unui pachet complet din bufferul de date, daca nu este suficient de mare, returneaza None
    def _extract_complete_packet(self, buffer):
        if len(buffer) < 2:
            return None

        # tcp da flux de octeti si pot primi doar o parte din pachet, deci trebuie sa verific daca am primit tot pachetul
        remaining_length, rl_bytes_count = self._decode_remaining_length(buffer, 1)    
        if remaining_length is None:
            return None

        # un octet pentru primul byte din fixed header, plus numarul de octeti folositi pentru codarea remaining length, plus remaining length
        total_length = 1 + rl_bytes_count + remaining_length

        if len(buffer) < total_length:
            return None

        packet = bytes(buffer[:total_length])   #extragere pachet complet din buffer
        del buffer[:total_length]   # stergere pachet extras din buffer, pentru a putea procesa urmatorul pachet
        return packet
    
    #receptionarea pachetelor primite de la broker
    def receive_packet(self):
        def parse_publish_packet(packet, qos):
            remaining_length, rl_bytes_count = self._decode_remaining_length(packet, 1)
            current_index = 1 + rl_bytes_count

            # sare peste fixeed header si ajunge la inceput la variable header
            topic_length = (packet[current_index] << 8) | packet[current_index + 1]     #combina 2 octeti pentru a obtine lungimea topicului (big endian)
            current_index += 2 

            # extragerea topicului 
            topic = packet[current_index:current_index + topic_length].decode('utf-8', errors='replace')
            current_index += topic_length

            if qos > 0:
                current_index += 2

            # extragerea proprietatilor din pachetul PUBLISH
            properties_length, properties_len_bytes = self._decode_varint_from_bytes(packet, current_index)
            current_index += properties_len_bytes

            # calcul unde se termina proprietatile si unde incepe payload-ul
            properties_end = current_index + properties_length
            user_properties = {}

            while current_index < properties_end:
                # extragerea id-ului proprietatii (1 byte)
                property_id = packet[current_index]
                current_index += 1

                if property_id == 0x26:  # User Property
                    # citire lungime cheie si valoare (2 bytes fiecare) si apoi citire efectiv a cheii si valorii
                    key_length = (packet[current_index] << 8) | packet[current_index + 1]
                    current_index += 2
                    key = packet[current_index:current_index + key_length].decode('utf-8', errors='replace')
                    current_index += key_length

                    # citire valoare (2 bytes pentru lungime + valoare)
                    value_length = (packet[current_index] << 8) | packet[current_index + 1]
                    current_index += 2
                    value = packet[current_index:current_index + value_length].decode('utf-8', errors='replace')
                    current_index += value_length

                    # adaugare cheie si valoare in dictionarul user_properties
                    user_properties[key] = value
                else:
                    raise ValueError(f"Unsupported PUBLISH property id: {property_id:#x}")

            # extragerea payload-ului (mesajul efectiv) dupa proprietati
            message = packet[properties_end:].decode('utf-8', errors='replace')

            return topic, message, user_properties
        
        # calculeaza pozitia unde incepe payload-ul in pachetul PUBLISH si extrage packet id din cei doi octeti care urmeaza dupa topic
        def extract_packet_id(packet):
            # ajunge la inceputul variable header-ului, dupa fixed header si remaining length
            remaining_length, rl_bytes_count = self._decode_remaining_length(packet, 1)
            current_index = 1 + rl_bytes_count

            #lungimea topicului (2 bytes)
            topic_length = (packet[current_index] << 8) | packet[current_index + 1]
            
            #indexul unde incepe packet ID (dupa topic)
            current_index += 2 + topic_length
            
            #extrage packet ID-ul (2 bytes, big endian)
            packet_id = (packet[current_index] << 8) | packet[current_index + 1]
            return packet_id
        
        
        buffer = bytearray()

        while self.connected:
            #dimensiunea maxima a pachetului - 1024 
            #bufferul cu care am ales sa lucram
            try:
                #citire din socket
                chunk = self.socket.recv(1024)

                if not chunk:  
                    print("Conexiunea a fost intrerupta de broker.")
                    self.connected = False
                    break

                # punere date in socket
                buffer.extend(chunk)

                while True:
                    packet = self._extract_complete_packet(buffer)

                    if packet is None:
                        break

                    print(f"Am primit pachet in hexa: {packet.hex()}")  #afis pachetul primit in format hex
                    
                    #CONNACK - raspuns la CONNECT
                    if self.decoder.CONNACK(packet):
                        self.connected = True
                        print("CONNACK primit.\n")
                        continue

                    #SUBACK - raspuns la SUBSCRIBE
                    if self.decoder.SUBACK(packet):
                        print("SUBACK primit.\n")
                        #The SUBACK packet MUST have the same Packet Identifier as the SUBSCRIBE packet that it is acknowledging
                        continue

                    if self.decoder.UNSUBACK(packet):
                        print("UNSUBACK primit.\n")
                        continue

                    #PINGRESP - raspuns pentru PING
                    if self.decoder.PINGRESP(packet):
                        print("PINGRESP primit. Brokerul este activ.\n")
                        self.last_ping = time.time()
                        continue

                    #PUBLISH QOS 1
                    if self.decoder.PUBACK(packet):
                        print("PUBACK primit.\n")
                        continue

                    #QOS 2
                    if self.decoder.PUBREC(packet):
                        print("PUBREC primit.")
                        #trimite pubrel
                        pubrec_id = (packet[2] << 8) | packet[3]   # packet identifier din PUBREC

                        pubrel_packet = self.encoder.PUBREL(pubrec_id)
                        self.socket.sendall(pubrel_packet)
                        print("PUBREL trimis.\n")
                        continue
                        

                    if self.decoder.PUBCOMP(packet):
                        print("PUBCOMP primit.\n")
                        self.packet_id += 1   # pt urmatorul pachet care va fi publicat
                        continue 

                    #QoS 2 (esti subscriber): dupa ce ai trimis PUBREC, brokerul trimite PUBREL
                    #raspunzi cu PUBCOMP (cu acelasi Packet ID)
                    if self.decoder.PUBREL(packet):
                        print("PUBREL primit (QoS2 step 3).")

                        pubrel_id = (packet[2] << 8) | packet[3]   # packet identifier din PUBREL
                        pubcomp_packet = self.encoder.PUBCOMP2(pubrel_id)

                        self.socket.sendall(pubcomp_packet)
                        print("PUBCOMP trimis (QoS2 step 4).\n")
                        continue

                    
                    #PUBLISH (QoS 0/1/2) - detectat din header
                    if self.decoder.is_publish(packet):
                        qos = self.decoder.publish_qos(packet)
                        print(f"PUBLISH primit (QoS={qos})\n")

                        topic, message, user_properties = parse_publish_packet(packet, qos)
                        # extragerea source client id din user properties, daca exista
                        source_client_id = user_properties.get("source_client_id")

                        print(f"Topic: {topic}")
                        print(f"Message: {message}")

                        # trimite mesajul catre callback-ul definit in partea de aplicatie
                        if self.on_message_callback:
                            self.on_message_callback(topic, message, source_client_id)

                        if qos == 1:
                            packet_id = extract_packet_id(packet)
                            puback_packet_ = self.encoder.PUBACK(packet_id)
                            self.socket.sendall(puback_packet_)
                            print("PUBACK trimis.\n")

                        elif qos == 2:
                            packet_id = extract_packet_id(packet)
                            pubrec_packet_ = self.encoder.PUBREC(packet_id)
                            self.socket.sendall(pubrec_packet_)
                            print("PUBREC trimis.\n")

                        continue
                        
                
            except Exception as e:
                if not self.connected:  
                    break
                print(f"Eroare la receptionarea pachetului: {e}")
                print("\nNu s-a primit niciun pachet.Inchidere.")
                break

        print("Thread-ul pentru receptie s-a oprit.")

    def conectare_broker(self, broker_address, broker_port):
        try:
            #socket TCP, Ipv4 
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect((broker_address, broker_port))   #deschidere conexiune TCP catre brokerul MQTT

            if self.use_tls:
                if self.tls_insecure:
                    # context tls fara verificarea certificatului brokerului
                    context = ssl._create_unverified_context()
                else:
                    # creeaza context TLS cu verificarea certificatului brokerului folosind certificatul CA specificat
                    context = ssl.create_default_context(cafile=self.ca_cert_path)

                # tcp invelit in TLS, datele trimise vor fi criptate si certificatele vor fi verificate
                self.socket = context.wrap_socket(
                    tcp_socket,
                    server_hostname=broker_address
                )

                print("Conectat la broker MQTT prin TLS.")
            else:
                self.socket = tcp_socket
                print("Conectat la broker MQTT prin TCP simplu.")


            # construirea si transmiterea pachetelui CONNECT
            connect_packet = self.encoder.CONNECT(
                self.client_id,
                self.lw_topic,
                self.lw_payload,
                self.lw_qos if self.lw_qos is not None else 0,
                self.lw_retain,
                self.username,
                self.password
            )
            self.socket.sendall(connect_packet)     #trimite toti octetii din buffer
            print("Pachet CONNECT trimis.")
            self.connected=True

            #fir separat care asculta permanent raspunsurile de la broker, pentru a nu bloca firul principal al aplicatiei
            #daemon=true pentru a ne asigura ca acest fir va fi oprit automat atunci cand apl se inchide
            threading.Thread(target=self.receive_packet, daemon=True).start()

            #fir pentru pinreq
            time.sleep(3)
            if self.connected:
                #thread pentru PINGREQ, pentru a verifica daca brokerul este inca activ si pentru a mentine conexiunea
                threading.Thread(target=self.pingreq).start()
                #pt mentinerea conexiunii mqtt, fir separat pentru Keep Alive
                #trimitere pingreq la intervale regulate pentru a mentine conexiunea activa

        except Exception as e:
            self.connected = False
            print(f"Eroare la conectarea la broker: {e}")
            raise


    def username_pw_set(self, username, password):
        #username si parola pentru autentificare
        self.username = username
        self.password = password   
        

    def topic_set(self,topic):
        self.topic=topic


    def pingreq(self):
        #trimit ping la fiecare 10 secunde
        while self.connected:
            try:
                #verificam intervalul de timp pt pingreq
                #dif dintre mo curent si timpul ult trimiteri de pingreq
                if time.time() - int(self.last_ping) >= self.keep_alive:
                    pingreq_packet = self.encoder.PINGREQ()
                    self.socket.sendall(pingreq_packet)

                    print("\nPINGREQ trimis.")

                    self.last_ping =time.time()  #actualizeaza timpul ultimei trimiteri
                time.sleep(1)
            except (OSError, ConnectionAbortedError) as e:
                print(f"Eroare la trimiterea PINGREQ: {e}")
                break
            
        print("Thread-ul pentru PINGREQ s-a oprit.")


    def disconnect(self):
        if self.connected:
            self.connected = False
            try:
                
                disconnect_packet = self.encoder.DISCONNECT()
                self.socket.sendall(disconnect_packet)

                print("Pachet DISCONNECT trimis.")
                #inchid socket-ul
            except Exception as e:
                print(f"Eroare la trimiterea pachetului DISCONNECT: {e}")
            finally:
                try:
                    #inchidem socketul folosit pentru comunicarea cu mosquitto
                    self.socket.close()
                    print("Socket-ul a fost inchis.")
                except Exception as e:
                    print(f"Eroare la inchiderea socket-ului: {e}")              
        else:
            print("Clientul este deja deconectat.")


    def publish(self, topic, message, qos):
        if not self.connected:
            print("Clientul nu este conectat la broker.")
            return False

        #generare id pentru mesaj
        message_id = self.packet_id
        try:
            publish_packet = self.encoder.PUBLISH(message_id, qos, topic, message)
            self.socket.sendall(publish_packet)
            
            print(f"Pachet PUBLISH trimis pentru topic '{topic}' cu QoS {qos}.\n")

            if qos ==1:
                self.packet_id += 1

        except Exception as e:
            print(f"Eroare la trimiterea pachetului PUBLISH: {e}")


    def subscribe(self, topic, qos):
        if not self.connected:
            print("Nu esti conectat la broker!")
            return

        message_id = self.packet_id
        try:
            subscribe_packet = self.encoder.SUBSCRIBE(message_id, topic, qos)
            self.socket.sendall(subscribe_packet)

            print(f"Pachet SUBSCRIBE trimis pentru topic '{topic}' cu QoS {qos}.\n")

            self.packet_id += 1

        except Exception as e:
            print(f"Eroare la trimiterea pachetului SUBSCRIBE: {e}")

    def unsubscribe(self,topic):
        if not self.connected:
            print("Nu esti conectat la broker!")
            return

        message_id = self.packet_id
        try:
            unsubscribe_packet = self.encoder.UNSUBSCRIBE(message_id, topic)
            self.socket.sendall(unsubscribe_packet)

            print(f"Pachet UNSUBSCRIBE trimis pentru topic '{topic}'.")

            self.packet_id += 1

        except Exception as e:
            print(f"Eroare la trimiterea pachetului UNSUBSCRIBE: {e}")
        
    def will_set(self, lw_topic, lw_payload, qos, retain=False):
        #seteaza last will pentru clientul mqtt
        self.lw_topic = lw_topic
        self.lw_payload = lw_payload
        self.lw_qos = qos
        self.lw_retain = retain

    # decodare varint dintr-un buffer de bytes, returneaza valoarea si numarul de bytes consumati pentru codarea acestei valori
    # ca sa stiu unde se termina proprietatile si unde incepe payload ul mesajului
    def _decode_varint_from_bytes(self, data: bytes, start_index: int):
        multiplier = 1
        value = 0
        consumed = 0
        index = start_index
        # initializare citire

        while True:
            if index >= len(data):
                raise ValueError("Malformed MQTT variable byte integer")

            encoded_byte = data[index]
            # la octetul curent, iau doar primii 7 biti utili din octet 
            value += (encoded_byte & 127) * multiplier
            consumed += 1
            index += 1
            # consumat un octet si trec la urmatorul

            # verificare bit cel mai din stanga, daca e 0, atunci nu mai am octeti de citit, daca e 1, mai am octeti de citit
            if (encoded_byte & 128) == 0:
                break
            
            multiplier *= 128
            if multiplier > 128 * 128 * 128:
                raise ValueError("Malformed MQTT variable byte integer")

        return value, consumed