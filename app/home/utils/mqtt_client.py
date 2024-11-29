
 
import gc
import os 
import cv2
import json
import traceback
import numpy
import threading
import paho.mqtt.client as mqtt


from io import BytesIO
from datetime import datetime 
from django.conf import settings
from home.others import process_center,gen_code
from home.models import StationData,Station,StationDataPhoto
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile

 




def on_message(client, userdata, msg):

    DATA_TOPIC = os.path.dirname(settings.TOPIC_DATA)
    PHOTO_TOPIC= os.path.dirname(settings.TOPIC_PHOTO)
    TOPIC_ALERT = os.path.dirname(settings.TOPIC_ALERT)
    TOPIC_DASHBOARD = settings.TOPIC_DASHBOARD
    
    topic_rcv  = os.path.dirname(msg.topic) #Obtenemos el topico
    id_station = os.path.basename(msg.topic)


    with open("/app/sav2,txt","a") as f:
        f.write(f"{str(msg.topic)}")
 
    if os.path.abspath(DATA_TOPIC) == os.path.abspath(topic_rcv):
        payload = msg.payload.decode("utf-8")
        payload = json.loads(payload)['values']

        id_station  = payload.get("id", None)
 
        try:
            station = Station.objects.filter(name=id_station).first()
            
        except:
            '''
            Estación no existe o no ha sido registrada.
            Se creará un logout con el nombre de estas y de cuantos publicaciones se reciben.
            '''
            pass

        else:

            '''
            Por el momento ...
            '''
 
            try:
                latitude    = payload.get("latitude",None)
                longitude   = payload.get("longitude",None)
                internet_MB = payload.get("ALL_USE_MB",None)

                status_station = payload.get("status",False)
                
                location    = payload.get("location",None)
                level       = payload.get("h0",None)
                level_dH    = payload.get("lidar_dH",None)

                sensor_HFS01 = payload.get("sensor_HFS01",None)
                sensor_HFS02 = payload.get("sensor_HFS02",None)
                sensor_HFS03 = payload.get("sensor_HFS03",None)
                sensor_HFS04 = payload.get("sensor_HFS04",None)

                voltage_battery = payload.get("bus_voltage_bateria",None)
                current_battery = payload.get("current_bateria",None)

                voltage_pannel   = payload.get("bus_voltage_panel",None)
                current_pannel   = payload.get("current_panel",None)

                camera_status = payload.get("camera_status",False)

                temperature  = payload.get("temperature",False)
                inference_ML = payload.get("camera_inference",0)
                string_inference = payload.get("string_inference",None)

                lidar = payload.get("lidar_status")



                if str(camera_status).lower() == 'false':
                    camera_status = False
                else:
                    camera_status = True

                status_station = False if str(status_station).lower() == 'false' else True
                
                if string_inference is not None:

                    if string_inference == "huayco":
                        status_ML = True
                    else:
                        status_ML = False

                
                state = 0 if status_station == False else 3

                '''
                Creamos nueva instancia
                '''

                kwargs = {
                    'station':station, 
                    'level':level,
                    'difference_H':level_dH,
                    'cruceta1' :sensor_HFS01,
                    'cruceta2' :sensor_HFS02,
                    'cruceta3' :sensor_HFS03,
                    'cruceta4' :sensor_HFS04,
                    'temperature':temperature,
                    'voltage_battery':voltage_battery,
                    'current_battery':current_battery,
                    'voltage_pannel':voltage_pannel,
                    'current_pannel':current_pannel,
                    'camera':camera_status,
                    'inference_ML':inference_ML,
                    'internet_MB':internet_MB,
                    'lidar_status':lidar,
                    'state':state,
                    'status_ML':status_ML

                }

                inference = StationData (**kwargs)
                inference.save()
            except:
                pass
#            

            else:
                pass
            
    elif os.path.abspath(TOPIC_DASHBOARD) == os.path.abspath(msg.topic):
        payload = msg.payload.decode("utf-8")
        payload = json.loads(payload)
        
        id_station = payload.pop('name',None)


        if id_station is not None:
            with open("/app/sav.txt","w") as f:
                f.write(f"Empezando {payload} {id_station}\n")
            station = Station.objects.filter(name=id_station).first()
            for key in payload.keys():

                value = payload.get(key)
                
                if key == 'inference_mode':
                    if value == 'server'  or value==True:
                        value = True
                    else:
                        value = False
                if key == "type_weights":

                    for tup in station.STATION_WEIGHTS:

                        if tup[1] == value:
                            value = tup[0]
                            break
                        
                try:
                    setattr(station,key,value)
                    with open("/app/sav,txt","a") as f:
                        f.write(f"Guardando: {key} {value}\n")

                except:
                    with open("/app/sav.txt","a") as f:
                        f.write(f"Error:{traceback.format_exc()} {key} {value}\n")

            try:
                station.save(from_mqtt=True)
            
            except:
                    with open("/app/sav.txt","a") as f:
                        f.write(f"Error:{traceback.format_exc()}  \n")


    elif os.path.abspath(PHOTO_TOPIC) == os.path.abspath(topic_rcv):
        
        '''
        Verificamos si corresponde a un topico de imagenes recibido
        '''
 
        try:
            station = Station.objects.filter(name=id_station).first()
            
        except:

            pass

        else:
            
            try:
 
                photo = msg.payload
                photo = numpy.frombuffer(photo, dtype=numpy.uint8)
                photo = cv2.imdecode(photo, cv2.IMREAD_COLOR)

                _, photo = cv2.imencode('.png', photo)  # Puedes cambiar '.png' por el formato que desees
                photo = photo.tobytes()

                inference = StationDataPhoto(station=station)
 
                inference.photo.save(f'{station.name}.png', ContentFile(photo))   
                
                inference.save()

            except:
                pass

    elif os.path.abspath(TOPIC_ALERT) == os.path.abspath(topic_rcv):

        '''
        El tópico recibido corresponde a una activación de la estación.
        Validaremos según el servidor, si corresponde a un envío de alertas o posiblemente a un mantenimiento.
        '''
        
        with open("read_alert",'a') as f:
            f.write(f"alerta recibida {id_station}\n")
        try:
            station = Station.objects.filter(name=id_station).first()

            if station:

                server = station.server 
                server.check_event(name=station.name) #El servidor revisará el evento.
                
        except:
            with open("read_alert",'a') as f:
                f.write(f"alerta error {traceback.format_exc()}\n")

def on_connect(client, userdata, flags, rc): 
    client.subscribe(settings.TOPIC_DATA)
    client.subscribe(settings.TOPIC_PHOTO)
    client.subscribe(settings.TOPIC_ALERT)
    client.subscribe(settings.TOPIC_DASHBOARD)


def mqtt_worker():

    client = mqtt.Client(settings.MQTT_CLIENT)
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASS)

    client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, 90)
    client.loop_forever()

def start_mqtt_client():

    with open("/app/check_mqtt.txt","w") as file:
        file.write("iniciando...")

    mqtt_thread = threading.Thread(target=mqtt_worker)
    mqtt_thread.daemon = True  # Permite que el hilo se cierre cuando la aplicación principal se cierra
    mqtt_thread.start()

start_mqtt_client()