from src.mqtt_core.packet_builder import PacketBuilder
from src.mqtt_core.packet_parser import PacketParser
import socket
import threading
import time

class MQTTClient:
    def __init__(self, client_id,on_message_callback=None):
        #constr de initializare variabile 

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
        
        self.on_message_callback = on_message_callback
        
    #receptionarea pachetelor primite de la broker
    def receive_packet(self):
        def parse_publish_packet(packet, qos):
            current_index = 2   #indexul de start pentru header-ul variabil

            #topicul: lungimea + cont
            topic_length = (packet[current_index] << 8) | packet[current_index + 1]  #primii 2 octeti: lung topicului
            current_index += 2
            topic = packet[current_index:current_index + topic_length].decode('utf-8', errors='replace')  #citim topicul
            current_index += topic_length

            #Packet Identifier (doar pentru QoS > 0)
            if qos > 0:
                current_index += 2

            if current_index < len(packet):
                properties_len = packet[current_index]
                current_index += 1 + properties_len

            #mesajul: partea dupa topic
            message = packet[current_index:].decode('utf-8', errors='replace')  #restul este mesajul

            return topic, message
        
        def extract_packet_id(packet):
            #Lungimea topicului (2 bytes)
            topic_length = (packet[2] << 8) | packet[3]
            
            #Indexul unde incepe Packet ID (dupa topic)
            current_index = 4 + topic_length
            
            #Extrage Packet ID-ul (2 bytes,  Big Endian)
            packet_id = (packet[current_index] << 8) | packet[current_index + 1]
            return packet_id
        
        
        while self.connected:
            #dimensiunea maxima a pachetului - 1024 
            #bufferul cu care am ales sa lucram
            try:
                packet = self.socket.recv(1024)
                if not packet:  
                    print("Conexiunea a fost intrerupta de broker.")
                    self.connected = False
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
                    pubrec_id = (packet[2] << 8) | packet[3]   # Packet Identifier din PUBREC

                    pubrel_packet = self.encoder.PUBREL(self.packet_id)
                    self.socket.sendall(pubrel_packet)
                    print("PUBREL trimis.\n")
                    continue
                    

                if self.decoder.PUBCOMP(packet):
                    print("PUBCOMP primit.\n")
                    self.packet_id+=1   # pt urmatorul pachet care va fi publicat
                    continue 

                #QoS 2 (esti subscriber): dupa ce ai trimis PUBREC, brokerul trimite PUBREL
                #raspunzi cu PUBCOMP (cu acelasi Packet ID)
                if self.decoder.PUBREL(packet):
                    print("PUBREL primit (QoS2 step 3).")

                    pubrel_id = (packet[2] << 8) | packet[3]   # Packet Identifier din PUBREL
                    pubcomp_packet = self.encoder.PUBCOMP2(pubrel_id)

                    self.socket.sendall(pubcomp_packet)
                    print("PUBCOMP trimis (QoS2 step 4).\n")
                    continue

                
                #######PT MESAJE CU 2 CLIENTI
                #PUBLISH (QoS 0/1/2) - detectat din header
                if self.decoder.is_publish(packet):
                    qos = self.decoder.publish_qos(packet)
                    print(f"PUBLISH primit (QoS={qos})\n")

                    topic, message = parse_publish_packet(packet, qos)

                    print(f"Topic: {topic}")
                    print(f"Message: {message}")

                    if self.on_message_callback:
                        self.on_message_callback(topic, repr(message))

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
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((broker_address, broker_port))
            print("Conectat la broker MQTT.")


            #pachet CONNECT 
            connect_packet = self.encoder.CONNECT(self.client_id, self.lw_topic, self.lw_payload, self.username, self.password)
            self.socket.sendall(connect_packet)
            print("Pachet CONNECT trimis.")
            self.connected=True

            #fir pentru primirea pachetelor de la broker prin metoda receive packet
            #daemon=true pentru a ne asigura ca acest fir va fi oprit automat atunci cand apl se inchide
            threading.Thread(target=self.receive_packet, daemon=True).start()

            #fir pentru pinreq
            time.sleep(3)
            if self.connected:
                #thread pentru PINGREQ, pentru a verifica daca brokerul este inca activ si pentru a mentine conexiunea
                threading.Thread(target=self.pingreq).start()
                #pt mentinerea conexiunii mqtt si ar trb sa ruleze cat timp conexiunea este activa

        except Exception as e:
            print(f"Eroare la conectarea la broker:{e}")


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

        #generare ID pentru mesaj
        message_id = self.packet_id
        try:
            publish_packet = self.encoder.PUBLISH(message_id, qos, topic, message)
            self.socket.sendall(publish_packet)
            
            print(f"Pachet PUBLISH trimis pentru topic '{topic}' cu QoS {qos}.\n")

            if qos ==1:
                self.packet_id += 1

        except Exception as e:
            print(f"Eroare la trimiterea pachetului PUBLISH: {e}")


    def subscribe(self,topic, qos):
        if not self.connected:
            print("Nu esti conectat la broker!")
            return
        
        #generare ID pentru mesaj
        message_id = self.packet_id
        try:
            subscribe_packet = self.encoder.SUBSCRIBE(message_id, topic, qos)
            self.socket.sendall(subscribe_packet)
            
            print(f"Pachet SUBSCRIBE trimis pentru topic '{topic}' cu QoS {qos}.\n")

            if qos > 0:
                self.packet_id += 1

        except Exception as e:
            print(f"Eroare la trimiterea pachetului SUBSCRIBE: {e}")

    def unsubscribe(self,topic):
        if not self.connected:
            print("Nu esti conectat la broker!")
            return
        
        #generare ID pentru mesaj
        message_id = self.packet_id
        try:
            unsubscribe_packet = self.encoder.UNSUBSCRIBE(message_id, topic)
            
            self.socket.sendall(unsubscribe_packet)
            print(f"Pachet UNSUBSCRIBE trimis pentru topic '{topic}'.")

        except Exception as e:
            print(f"Eroare la trimiterea pachetului UNSUBSCRIBE: {e}")
        
    def will_set(self, lw_topic, lw_payload, qos, retain=False):
        #seteaza Last Will pentru clientul MQTT
        self.lw_topic = lw_topic
        self.lw_payload = lw_payload
        self.lw_qos = qos
        self.lw_retain = retain