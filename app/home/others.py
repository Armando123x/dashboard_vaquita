import os 
import json
import logging
import traceback
import paho.mqtt.client as mqtt

import random
import string 


logger = logging.getLogger(__name__)


def gen_code():
    
    number = random.choice([4,5,6,7])
    caracteres = string.ascii_letters + string.digits
    codigo = ''.join(random.choice(caracteres) for _ in range(number))

    return codigo 

def process_center(status,payload):
    pass

def mqtt_send(payload):

    def on_connect(client,userdata,flags,rc):
        with open("/app/log.txt","a") as file:

            file.write(f"Conectado MQTT con resultado {rc}\n")
    def on_connect_fail(client,userdata,flags,rc):
        with open("/app/log.txt","a") as file:

            file.write(f"No conectado a  MQTT con resultado {rc}\n")
    try:

        message = payload.get("message",None)
        type_   = payload.get("type",None)
        name    = payload.get("name",None)
        option  = payload.get("option")

        message = json.loads(message)
        if name == None:
            name = ''


        MQTT_BROKER = os.environ.get("MQTT_BROKER")
        MQTT_PORT   = int(os.environ.get("MQTT_PORT"))
        MQTT_CLIENT   = 'igproj_master'
        MQTT_USER   = 'igproj'
        MQTT_PASS   = os.environ.get("MQTT_PASS") 

        TOPIC_CONFIG = os.environ.get("TOPIC_CONFIG")
        TOPIC_COMMAND = os.environ.get("TOPIC_COMMAND")

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
    
    except:
        error = traceback.format_exc()
        pp = f"Error al conectarse al broker MQTT. Copia de error:\n{error}"
        logger.error(pp)
        with open("/app/log.txt","a") as file:
            file.write(pp +'\n')

        return False
    else:
        logger.info("Conexión al broker MQTT realizada con éxito.")
        with open("/app/log.txt","a") as file:
            file.write(f"Conexión al broker MQTT realizada con éxito.Dict {message.keys()}" +'\n')
        message = json.dumps(message)

        #Elección del topic
        TOPIC = None
        
        if option=="command":
            
            if type_ == "per_user":

                TOPIC = TOPIC_COMMAND_USER
            else:
                TOPIC = TOPIC_COMMAND_GENERAL

            with open("/app/log.txt","a") as file:
                file.write(f"Topico a publicar:{TOPIC} Mensaje:{message}" +'\n')
            try:
                client.publish(TOPIC,message,qos=1)
            except:
                return False

        elif option=="parameter":

            if type_ == "per_user":

                TOPIC = TOPIC_CONFIG_USER
            else:
                TOPIC = TOPIC_CONFIG_GENERAL
            with open("/app/log.txt","a") as file:
                file.write(f"Topico a publicar:{TOPIC} Mensaje:{message}" +'\n' + f"IP:{MQTT_BROKER} PORT:{MQTT_PORT}\nPWD:{MQTT_PASS} user:{MQTT_USER}")    
            try:        
                client.publish(TOPIC,message,qos=1)
            except:
                return False
        return True




