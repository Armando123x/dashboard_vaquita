import os 
import json 
import traceback
import paho.mqtt.client as mqtt

 


def mqtt_send():

    def on_connect(client,userdata,flags,rc):

        print(f"Conectado con rc: {rc}")
        return
 
    try:

        message = {
            'uwu':123
        }
        type_   = 'per_user'
        name    = 'x1'
        option  = 'parameter'


        if name == None:
            name = ''


        MQTT_BROKER =  '190.187.237.140'
        MQTT_PORT   =5007
        MQTT_CLIENT   = 'igproj_master'
        MQTT_USER   = 'igproj'
        MQTT_PASS   = 'igproj2023'

        TOPIC_CONFIG =  'igp/roj/config'
        TOPIC_COMMAND = 'igp/roj/config/command'

        TOPIC_COMMAND_GENERAL = os.path.join(TOPIC_COMMAND,'global')
        TOPIC_COMMAND_USER    = os.path.join(TOPIC_COMMAND,name)

        TOPIC_CONFIG_GENERAL  = os.path.join(TOPIC_CONFIG,'global')
        TOPIC_CONFIG_USER     = os.path.join(TOPIC_CONFIG,name)

        client    =  mqtt.Client(MQTT_CLIENT)
        
        client.on_connect = on_connect
        client.username_pw_set(MQTT_USER,MQTT_PASS) 

        client.connect(MQTT_BROKER,MQTT_PORT,90)
        print(1)
    except:
        error = traceback.format_exc()
        pp = f"Error al conectarse al broker MQTT. Copia de error:\n{error}" 
        print(pp)

        return False
    else: 
       
        print("Conexión al broker MQTT realizada con éxito." +'\n')
        message = json.dumps(message)

        #Elección del topic
        TOPIC = None
        
        if option=="command":
            
            if type_ == "per_user":

                TOPIC = TOPIC_COMMAND_USER
            else:
                TOPIC = TOPIC_COMMAND_GENERAL

           
            try:
                client.publish(TOPIC,message,qos=1)
            except:
                return False

        elif option=="parameter":

            if type_ == "per_user":

                TOPIC = TOPIC_CONFIG_USER
            else:
                TOPIC = TOPIC_CONFIG_GENERAL
          
            try:        
                client.publish(TOPIC,message,qos=1)
            except:
                return False
        return True




mqtt_send()