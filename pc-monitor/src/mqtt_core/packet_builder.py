class PacketBuilder:

    def CONNECT(self, client_id, lw_topic, lw_payload, username, password,keep_alive=10):
        #FIXED HEADER
        packet = bytearray()
        packet.extend(b'\x10')  #CONNECT = 1, Flag = 0 (0001 0000)
        packet.extend(b'\x00')  #placeholder pentru lungimea ramasa
        #remaining length field = the length of the variable header plus the length of the payload

        #VARIABLE HEADER
        #protocol name = MQTT
        packet.extend(b'\x00\x04')  #Lungimea protocolului: 4
        packet.extend(b'MQTT')      #Protocol Name
        packet.extend(b'\x05')      #Protocol Level: MQTT v5
        
        #FLAGS
        packet.extend(b'\xC6')      #Flags (Username=1, Password=1,Will Retain=0, Will QoS=00, Will Flag=1, Clean Start=1, Reserved=0)
        
        #sa expire la un nr de secunde ; sa trimita un nou pachet ;
        #repornirea time 
        packet.extend(int(keep_alive).to_bytes(2, 'big'))  #Keep Alive: 10 sec(2 octeți, big-endian)

        #PROPERTIES
        packet.extend(b'\x00')
        # Length, Session Expiry Interval Identifier, Session Expiry Interval

        #PAYLOAD
        #client id
        packet.extend((len(client_id)).to_bytes(2, 'big'))   #Lungimea Client ID
        packet.extend(client_id.encode('utf-8',errors='replace'))    #Client ID folosind codificarea UTF-8
        #replace= inlocuieste caracterele invalide cu ?

        #LAST WILL TOPIC, MESSAGE
        packet.extend(b'\x00')          #Lungime Will properties=0
            #LAST WILL TOPIC
        packet.extend((len(lw_topic)).to_bytes(2, 'big'))          #Lungime Will Topic
        packet.extend(lw_topic.encode('utf-8',errors='replace'))   #Will Topic
            #LAST WILL MESSAGE
        packet.extend((len(lw_payload)).to_bytes(2, 'big'))        #Lungime Last Will Message
        packet.extend(lw_payload.encode('utf-8',errors='replace')) #Last Will Message
        
        #USERNAME
        packet.extend((len(username)).to_bytes(2, 'big'))          #Lungime Username 
        packet.extend(username.encode('utf-8', errors='replace'))  #Username

        #PASSWORD
        packet.extend((len(password)).to_bytes(2, 'big'))          #Lungime Password 
        packet.extend(password.encode('utf-8', errors='replace'))  #Password

        #FIXED HEADER UPDATE
        remaining_length=len(packet)-2   #primii 2 din fixed header
        packet[1:2]=remaining_length.to_bytes(1,'big')       #lungimea ramasa 
        #big endian = cei mai semnificativi sunt plasati la inceput
        #se genereaza un sir de octeti, slice permite modificarea unui interval din bytearray
        return packet
    
    def PUBLISH(self, packet_id, qos, topic, message, dup=0, retain=1):
    # dup flag pentru re-delivery: 0 sau 1
    # param retain: flag pentru a retine mesajul 0 sau 1
        packet = bytearray()
    
    # FIXED HEADER
        flags = 0x30  # PUBLISH = 3, bit 4 implicit 0 
    
        if dup:
            flags |= 0x08       #DUP flag (bit 3)
        if qos == 1:
            flags |= 0x02       #QoS 1 (bit 1)
        elif qos == 2:
            flags |= 0x04       #QoS 2 (bit 2)
        elif qos != 0:
            raise ValueError("Nivel QoS invalid. Trebuie să fie 0, 1 sau 2.")
        
        if retain:
            flags |= 0x01  # Seteaza RETAIN flag (bit 0)

        packet.append(flags)  #primul byte din Fixed Header
        packet.append(0x00)   #remaining Length

        # VARIABLE HEADER
        # Topic name
        packet.extend((len(topic)).to_bytes(2, 'big'))  # Topic length
        packet.extend(topic.encode('utf-8'))            # Topic
        # Packet Identifier (doar pentru QoS>0)
        if qos > 0:
            packet.extend(packet_id.to_bytes(2, 'big'))
        
        #properties length 
        packet.append(0x00)  

        #PAYLOAD
        packet.extend(message.encode('utf-8')) 
        
        #remaining Length
        remaining_length = len(packet) - 2
        packet[1:2] = remaining_length.to_bytes(1, 'big')

        return packet
    
    def PUBACK(self,packet_id,reason_code=0x00,properties=None):
        #A PUBACK packet is the response to a PUBLISH packet with QoS 1.
        packet = bytearray()
        
        #FIXED HEADER 
        packet.append(0x40)  # 0100 0000, byte 1
        
        #Remaining Length
        remaining_length = 2  #doar 2 bytes(packet_id + reason_code)
        
        #VARIABLE HEADER
        #packet identifier from the PUBLISH packet that is being acknowledged
        packet.append(reason_code)
        
        # Properties 
        if properties:
            prop_length = len(properties)
            packet.append(prop_length)  
            packet.extend(properties)  #datele propr
            remaining_length += prop_length + 1     #lung propr+1 pentru lungimea datelor

        
        #Remaining Length
        packet[1:2] = remaining_length.to_bytes(1, 'big')

        #adaugam Packet ID-ul din PUBLISH
        packet.extend(packet_id.to_bytes(2, 'big'))

        #Variable header parts
        vh = bytearray()
        vh.extend(packet_id.to_bytes(2, 'big'))

        #if you include reason code, you must also include properties length
        vh.append(reason_code)

        if properties:
            vh.append(len(properties))  # Property Length
            vh.extend(properties)
        else:
            vh.append(0x00) # Property Length = 0

        # Remaining Length
        packet.append(len(vh))
        packet.extend(vh)
        
        return packet


    def PUBREC(self,packet_id,reason_code=0x00, properties=None):
        packet = bytearray()

        # FIXED HEADER
        packet.append(0x50)  

        #Remaining Length
        remaining_length = 2 

        
        if reason_code != 0x00 or properties:
            remaining_length += 1  
            if properties:
                property_length = len(properties)
                remaining_length += 1 + property_length  

    
        packet.append(remaining_length)

        #VARIABLE HEADER
        #adaugam Packet Identifier
        packet.extend(packet_id.to_bytes(2, 'big'))

        if reason_code != 0x00 or properties:
            packet.append(reason_code)

            #adaugam proprietatile, daca sunt
            if properties:
                packet.append(len(properties))  #Property Length
                packet.extend(properties)  

        return packet
    
    def PUBREL(self,packet_id,reason_code=0x00,properties=None):
        #a pubrel packet is the response to a pubrec packet , it is the third packet of the qos 2 protocol exchange
        packet=bytearray()

        #FIXED HEADER
        packet.append(0x62) #byte 1

        remaining_length = 2  

        #adaugam remaining length
        packet.extend(remaining_length.to_bytes(1, 'big'))

        #VARIABLE HEADER
        #packet identifier from the PUBREC packet that is being acknowledged,
        packet.extend(packet_id.to_bytes(2, 'big'))

        #reason code
        if reason_code != 0x00 or properties:
            packet.append(reason_code)

            property_length = 0 if not properties else len(properties)
            packet.append(property_length)  
        
            remaining_length += property_length + 1 

            #adaugam properties daca exista
            if properties:
                packet.extend(properties)  #adaugam in pachet

        #update remaining length

        return packet 
    
    def PUBCOMP3(self, packet_id):
        #FIXED HEADER
        packet = bytearray()
        packet.append(0x70)    #byte 1
        packet.append(0x02)    #Remaining Length 

        #VARIABLE HEADER
        #Packet Identifier 
        packet.extend(packet_id.to_bytes(2, 'big'))  

        return packet
    
    def PUBCOMP2(self,packet_id,reason_code=0x00,properties=None):
        #a pubrel packet is the response to a pubrec packet , it is the third packet of the qos 2 protocol exchange
        packet=bytearray()

        #FIXED HEADER
        packet.append(0x70) #byte 1

        remaining_length = 2  

        #adaugam remaining length
        packet.extend(remaining_length.to_bytes(1, 'big'))

        #VARIABLE HEADER
        #packet identifier from the PUBREC packet that is being acknowledged,
        packet.extend(packet_id.to_bytes(2, 'big'))

        #reason code
        if reason_code != 0x00 or properties:
            packet.append(reason_code)

            property_length = 0 if not properties else len(properties)
            packet.append(property_length)  
        
            remaining_length += property_length + 1 

            #adaugam properties daca exista
            if properties:
                packet.extend(properties)  #adaugam in pachet

        #update remaining length

        return packet 
    
    def SUBSCRIBE(self, packet_Id, topic,QoS):
        #BITS 3,2,1 and 0 of the Fixed Header of the SUBSCRIBE packet are reserved and MUST be set to 0,0,1 and 0 respectively
       
        #FIXED HEADER 
        #0010 - bitii 3,2,1,0 de la Reserved  deci valoarea 2 (byte 1)
        packet=bytearray()
        packet.extend(b'\x82')
        #byte 2 remaining length
        packet.extend(b'\x00')

        #VARIABLE HEADER
            #Packet Identifier MSB LSB - byte 1 and 2
        packet.extend(packet_Id.to_bytes(2,'big'))
        #daca nu avem proprietati 
        packet.extend(b'\x00')      #PropertyLength byte 3

        #PAYLOAD
        #packet contains a list of Topic Filters indicating the Topics to which the Client wants to subscribe
        #topic filters=utf 8 encoded string 
        #minim 1 topic filter+ 1 subscription options 
        if  QoS not in [0,1,2]:
             raise ValueError(f"QoS invalid: {QoS}. Trebuie sa fie 0, 1 sau 2!")

        topic_length = len(topic)
        packet.extend(topic_length.to_bytes(2, 'big'))  #MSB si LSB
        packet.extend(topic.encode('utf-8',errors='replace'))


        packet.extend(QoS.to_bytes(1,'big'))            #QoS level
       
        #FIXED HEADER UPDATE - remaining length 
        remaining_length = len(packet) - 2                          #lungimea ramasa
        packet[1:2] = remaining_length.to_bytes(1,'big')            #setam lungimea ramasa in byte 2 din fixed header
        #octetul 2 din fixed header - index 1
        
        return packet
    
    def UNSUBSCRIBE(self,packet_id, topic):
        #an unsubscribe packet is sent by the client to the server to unsubscribe from topics
        packet=bytearray()

        #FIXED HEADER
        packet.extend(b'\xA2') #byte 1

        remaining_length = 2  #byte 2
        packet.extend(b'\x00')

        #VARIABLE HEADER 
        #packet identifier
        packet.extend(packet_id.to_bytes(2,'big'))

        #properties
        #Property Length 0x00 daca nu există
        packet.extend(b'\x00')  #byte 3

        #PAYLOAD
        #lista de Topic Filters (strings UTF-8)
        topic_length = len(topic)
        packet.extend(topic_length.to_bytes(2, 'big')) 
        packet.extend(topic.encode('utf-8', errors='replace'))  

        #remaining length
        remaining_length = len(packet) - 2  
        packet[1:2] = remaining_length.to_bytes(1, 'big')  

        return packet

    def PINGREQ(self):
        #return bytearray(b'\xC0\00')
        return bytearray(b'\xC0\x00')
    
    def DISCONNECT(self):
        #final packet sent from the Client or the Server
        #the client or servwr may send a disconnect packet before closing the connection
        #If the Connection is closed without the Client first sending a DISCONNECT packet with Reason Code 0x00 and the Connection has a Will Message, the Will Message is published
        #The Client or Server sending the DISCONNECT packet MUST use one of the DISCONNECT Reason Code values 
        
        #FIXED HEADER
        #byte 1 E0 ; byte 2 remaining length 00 -  close the connection normally
        #04 - disconnect with will message
        packet = bytearray()
        packet.extend(b'\xE0')

        packet.extend(b'\x00')
        #VARIABLE HEADER - reason code 

        #after sending a disconnect packet the sender: must not send any more control packets and must close the network connection
        return packet
    
    def AUTH(self, reason_code=0x00,auth_method="SCRAM-SHA-1",auth_data=b"", reason_string=""):
        #FIXED HEADER
        packet = bytearray()
        packet.extend(b'\xF0')    #byte 1

        packet.extend(b'\x00')    #byte 2 remaining length 

        #VARIABLE HEADER
        #reason code
        # packet.extend(b'\x00')
        #sau poate fi 0x18= continue authentication 
        packet.append(reason_code)

        #PROPERTIES
        properties = bytearray()

        #authentication method
        if auth_method:
            properties.append(0x15)  
             #name of the authentication method]
            method_encoded = auth_method.encode('utf-8')
            properties.extend(len(method_encoded).to_bytes(2, 'big'))  #lungime
            properties.extend(method_encoded)

        #authentication data
        if auth_data:
            properties.append(0x16) 
            #binary data cotaining authentication data 
            properties.extend(len(auth_data).to_bytes(2, 'big'))  # Length of the data
            properties.extend(auth_data)


        #reason string 
        if reason_string:
            properties.append(0x1F)  
            #utf 8 encoded string representing the reason for the disconnect 
            reason_encoded = reason_string.encode('utf-8')
            properties.extend(len(reason_encoded).to_bytes(2, 'big'))  # Length of the reason string
            properties.extend(reason_encoded)

        #adaugam proprietatile la pachet
        packet.extend(len(properties).to_bytes(1, 'big'))  #lungime
        packet.extend(properties)

        #lungimea ramasa
        remaining_length = len(packet) - 2  #excludem primul byte adica fixed header 
        packet[1:2] = remaining_length.to_bytes(1, 'big')  #update

        return packet