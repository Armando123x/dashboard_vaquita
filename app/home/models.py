import os 
import requests 
import numpy 

from copy import deepcopy
from datetime import datetime
import paho.mqtt.publish as publish 
from django.conf import settings
from django.db import models
from twython import Twython
from django.urls import reverse
from django.core.mail import send_mail
from django.db.models.signals import post_init
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
 
from decimal import Decimal
import json
import traceback
from dotenv import load_dotenv


load_dotenv() 
# Create your models here.

STATION_STATES = [
    (0, 'Normal'),
    (1, 'Light'),
    (2, 'Medium'),
    (3, 'High'),
]




class StationDataManager(models.Manager):
    
    def get_values(self,station):
        return  self.filter(station=station).order_by('-date').values()

    def get_latest_per_key(self, station, key,limit=15):
        """
        Devuelve los últimos valores de 'voltage_battery' para la estación dada.
        El número de valores devueltos está determinado por 'limit' (por defecto 15).
        Si no hay registros, devuelve una lista vacía.
        """
        try:
            return self.filter(station=station).order_by('-date').values_list(key, flat=True)[:limit][::-1]
        
        except ObjectDoesNotExist:
            return numpy.ones(limit)*999

    def get_latest_time(self, station):
        """
        Devuelve la fecha más reciente ('date') de la estación dada.
        Si no hay registros, devuelve None.
        """
        try:
            return self.filter(station=station).latest('date').date
        except ObjectDoesNotExist:
            return None
    
class LastDataManager(models.Manager):

    def get_queryset(self):
        data = {}
        stations = Station.objects.all()
        for st in stations:
            x = StationData.objects.filter(station=st)
            if x: data[st.code] = x.latest()
        
        return data
    
    
def track_data(*fields):
    """
    Tracks property changes on a model instance.
    
    The changed list of properties is refreshed on model initialization
    and save.
    
    >>> @track_data('name')
    >>> class Post(models.Model):
    >>>     name = models.CharField(...)
    >>> 
    >>>     @classmethod
    >>>     def post_save(cls, sender, instance, created, **kwargs):
    >>>         if instance.has_changed('name'):
    >>>             print "Hooray!"
    """
    
    UNSAVED = dict()

    def _store(self):
        "Updates a local copy of attributes values"
        if self.id:
            self.__data = dict((f, getattr(self, f)) for f in fields)
        else:
            self.__data = UNSAVED

    def inner(cls):
        # contains a local copy of the previous values of attributes
        cls.__data = {}

        def has_changed(self, field):
            "Returns ``True`` if ``field`` has changed since initialization."
            if self.__data is UNSAVED:
                return False
            return self.__data.get(field) != getattr(self, field)
        cls.has_changed = has_changed

        def old_value(self, field):
            "Returns the previous value of ``field``"
            return self.__data.get(field)
        cls.old_value = old_value

        def whats_changed(self):
            "Returns a list of changed attributes."
            changed = {}
            if self.__data is UNSAVED:
                return changed
            for k, v in self.__data.iteritems():
                if v != getattr(self, k):
                    changed[k] = v
            return changed
        cls.whats_changed = whats_changed

        # Ensure we are updating local attributes on model init
        def _post_init(sender, instance, **kwargs):
            _store(instance)
        post_init.connect(_post_init, sender=cls, weak=False)

        # Ensure we are updating local attributes on model save
        def save(self, *args, **kwargs):
            save._original(self, *args, **kwargs)
            _store(self)
        save._original = cls.save
        cls.save = save
        return cls
    return inner

@track_data('mode')
class Server(models.Model):
    SERVER_MODES = [
    (0, 'Maintenance'),
    (1, 'Simulacrum'),
    (2, 'Operation'),
]

    name = models.CharField(max_length=20,help_text="Nombre del servidor.")
    mode = models.PositiveSmallIntegerField(default=1, choices=SERVER_MODES,help_text="Define el modo actual del servicio.")
    date = models.DateTimeField(null=True, blank=True)
    email = models.BooleanField(default=False)
    email_to = models.CharField(max_length = 150, default='',help_text="Correo de notificación")
    email_subject = models.CharField(max_length=50, default = 'SMH - IGP - {var0}',help_text="Correo para notificaciones.")
    email_body_resume = models.TextField(max_length=600, default = "REPORTE SMH - IGP\nFecha y hora de emisión de reporte: {var0}\n\nEl Sistema de monitoreo de huaicos reporta la activación de la quebrada Huaycoloro:\n\n{var1}\n\nPara más información, monitoreo en tiempo real y ubicación de estaciones:\nhttp://jro-huaycos.igp.gob.pe\nInsituto Geofísico del Perú." )
    email_body_station = models.TextField(max_length=600, default = "Estación: {var0}\nFecha y hora de activación: { 1 }\n{2} " )
    facebook = models.BooleanField(default=False)
    facebook_body = models.TextField(max_length=600, default = "#CEMOHUI - IGP - {var0}\nEl centro de monitoreo de huaicos informa la activación de la quebrada Huaycoloro a las {var1}, detectado por la estación: {var2}\nPara más información, monitoreo en tiempo real y ubicación de estaciones visita:\nhttp://jro-huaycos.igp.gob.pe\nInstituto Geofísico del Perú."  )
    telegram = models.BooleanField(default=False)
    telegram_body = models.TextField(max_length=600, default = "#CEMOHUI - IGP - {var0}\nEl centro de monitoreo de huaicos informa la activación de la quebrada Huaycoloro a las {var1}, detectado por la estación: {var2}\nPara más información, monitoreo en tiempo real y ubicación de estaciones visita:\nhttp://jro-huaycos.igp.gob.pe\nInstituto Geofísico del Perú."  )
    twitter  = models.BooleanField(default=False)
    twitter_body = models.TextField(max_length=600, default = "#CEMOHUI - IGP - {var0}\nEl centro de monitoreo de huaicos informa la activación de la quebrada Huaycoloro a las {var1}, detectado por la estación: {var2}\nPara más información, monitoreo en tiempo real y ubicación de estaciones visita:\nhttp://jro-huaycos.igp.gob.pe\nInstituto Geofísico del Perú." )
    
    siren = models.BooleanField(default=False)
    siren_lapse = models.IntegerField(default = 20)
    test = models.BooleanField(default=False)


    events = models.JSONField(default=list, help_text="Lista de eventos recientes con nombre de estación y hora de activación.")

    def check_event(self,name):

        mode = self.get_mode_display()

        if self.mode == 2:

            #En caso de que el servidor esté en modo operación, se enviará las alertas.
            self.send_alert()

    def send_alert(self,name):

        '''
        Metodo que enviará todas las alertas
        '''

        message = "aaaa"

        self.send_alert_to_receptor(name)
        self.send_email(message)
        self.send_facebook(message)
        self.send_twitter(message)
        self.send_telegram(message)
        self.add_event(name)


    def send_email(self,):

        if self.email:
            
            body_resume = deepcopy(self.email_body_resume)
            body = deepcopy(self.email_body_station)

            #Falta formatear las cadenas 


    
    def send_facebook(self,message):

        if self.facebook:

            page_id_1               = os.getenv("FACEBOOK_ID_PAGE",None)
            facebook_access_token   = os.getenv("FACEBOOK_TOKEN",None)
            msg = message
            post_url = 'https://graph.facebook.com/{}/feed'.format(page_id_1)
            payload = {
            'message': msg,
            'access_token': facebook_access_token
            }
            r = requests.post(post_url, data=payload,timeout=10)


            return 

    def send_twitter(self,message):

        if self.twitter:
            try:
                consumer_key    = os.getenv("TWITTER_CONSUMER_KEY")
                consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
                access_token    = os.getenv("TWITTER_ACCESS_TOKEN")
                access_secret   = os.getenv("TWITTER_ACCESS_SECRET")

                twitter = Twython(
                    consumer_key,
                    consumer_secret,
                    access_token,
                    access_secret
                )
                twitter.update_status(status=message)

            except:

                pass
                
            return
        
 

    def send_telegram_message(self,message):
        """
        Sends a message to a Telegram chat via Bot API.

        Args:
        - chat_id (str): The Telegram chat ID (e.g., the user or group ID).
        - message (str): The message to send.
        - bot_token (str): Your Telegram Bot API token.

        Returns:
        - response (dict): The API response as a Python dictionary.
        """
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_BOT_ID","Abc Debhani")

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message
        }
        response = requests.post(url, json=payload,timeout=10)
        return response.json()
        
    def send_telegram(self,):
        if self.telegram:

            message = "Estación se activó"

            self.send_telegram_message(message)


            return
        

    def send_alert_to_receptor(self,name):

        if self.siren:
            payload = { 
                'timestamp':datetime.now().isoformat(),
                'id':str(name),
                'status': True, 
                'lapse':self.siren_lapse
            }
            publish.single(settings.TOPIC_SIRENA,
                        payload=json.dumps(payload),
                        hostname=settings.MQTT_BROKER,
                        qos=2,
                        auth={
                            "username":settings.MQTT_USER,
                            "password":settings.MQTT_PASS
                            },
                            port=settings.MQTT_PORT)


    def add_event(self, name):

        MAX_EVENTS = 30  

        event = {
            "station_name": name,
            "activation_time": datetime.now().isoformat()   
        }
        
        self.events.append(event)
        if len(self.events) > MAX_EVENTS:
            self.events.pop(0)  

        self.save()

    def __str__(self):
        return '{} [{}] '.format(self.name, self.SERVER_MODES[self.mode][1])
    
    def save(self, *args, **kwargs):
        if self.has_changed('mode'):
            self.date = datetime.now()
        super(Server, self).save(*args, **kwargs)
 
    class Meta:
        app_label = 'home'

 
class Station(models.Model):    


    STATION_WEIGHTS = [
        (0, 'only_camara'),
        (1, 'camara_HFS_LIDAR'),
        (2,'camara_HFS'),
        (3,'HFS') 
    ]

    server                 = models.ForeignKey(Server, on_delete=models.CASCADE, related_name="stations",default = 1 )
    code                   = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    name                   = models.CharField(max_length=25,help_text="Nombre de la estación. Este nombre es el ID que usará la estación para la publicación en el broker MQTT.")      
    location               = models.CharField(max_length=30,default="",help_text="Nombre del departamento o ubicación del dispositivo.") 
    latitude               = models.FloatField(default=-11,help_text="Latitud de ubicación del dispositivo.")
    longitude              = models.FloatField(default=-70,help_text="Longitud de ubicación del dispositivo.")


    radar_HB100           = models.BooleanField(default=False,help_text="Activa o desactiva los sensores de velocidad HB100.")
    radar_HFS             = models.BooleanField(default=False,help_text="Activa o desactiva los sensores de presencia HFS.")
    lidar                 = models.BooleanField(default=False,help_text="Activa o desactiva el control del cause por lidar.")
    measure_voltage       = models.BooleanField(default=False,help_text="Activa o desactiva la medición de voltajes.")
    camera                = models.BooleanField(default=False,help_text="Activa o desactiva el uso de la cámara.")
    store_data            = models.BooleanField(default=False,help_text="Activa o desactiva el guardado de datos en la estación.")


    inference_mode        = models.BooleanField(default=False,help_text="Activa o desactiva las inferencias por video al servidor.")
     
    level_reference       = models.FloatField(default=0,help_text="Threshold de desnivel de columna de agua en cm.")
    
    send_data_mqtt        = models.DecimalField(max_digits=5, decimal_places=1, default=60,help_text="Tiempo de actualización de datos por MQTT en segundos.")
    send_photo_mqtt       = models.DecimalField(max_digits=5, decimal_places=1, default=60,help_text="Tiempo de actualización de fotos por MQTT en segundos.")
    time_video_sampling   = models.DecimalField(max_digits=5, decimal_places=1,default=60,help_text="Tiempo que se envía los videos para realizar inferencia al servidor ML.")

    river_width           = models.DecimalField(max_digits=6, decimal_places=1, default=99.9,help_text="Ancho del rio en metros.")  

    mqtt_broker           = models.CharField(max_length=40,default=settings.MQTT_BROKER,help_text="Broker MQTT. Solo cambie en caso de migraciones.")
    mqtt_port             = models.IntegerField( default=settings.MQTT_PORT,help_text="Puerto MQTT del Broker.")
    mqtt_user             = models.CharField(default=settings.MQTT_USER,max_length=20,help_text="Usuario MQTT.")
    mqtt_pass             = models.CharField(default=settings.MQTT_PASS,max_length=20,help_text="Password MQTT.")

    server_inference_ML   = models.CharField(max_length=40,default="38.10.105.243",help_text="Servidor para inferencias de video ML.")
    port_inference_ML     = models.IntegerField( default=777,help_text="Port del servidor para inferencias de video ML.")

    config_topic          = models.CharField(max_length=50,default=settings.TOPIC_CONFIG,help_text="Define el broker MQTT para recepción de configuración en la estación.")

    type_weights          = models.PositiveSmallIntegerField(default=0,choices= STATION_WEIGHTS,help_text="Selecciona el tipo de peso o configuración para activar la estación.")


    class Meta:
        ordering = ['name']

    def __str__(self):
        # return '%s' % (self.code)
        return '%s' % (self.name)
    
    def get_absolute_url(self):
        return reverse('station_view', kwargs={'pk': self.pk})


    def send_for_mqtt(self,name,payload):

        '''
        Se envía la configuración a las estaciones.
        En este caso, las estaciones enviarán un número 200 al tópico de recepción.

        Contenido de payload:
        ---------------------
            - type_user: "global" o "per_user". Hace referencia a si el cambio se realizará de forma global o solo por dispositivo.
            - type_message: "command" o "parameter". Hace referencia a si el mensaje a enviar es un comando o un cambio de valor de parametro.
            - payload: Define los cambios.
        '''

        try:
            
            
            type_message    = payload.get("type_message")
            type_user       = payload.get("type_user")
            payload         = payload.get("payload")

            MQTT_BROKER     = settings.MQTT_BROKER
            MQTT_PORT       = settings.MQTT_PORT
            MQTT_USER       = settings.MQTT_USER
            MQTT_PWD        = settings.MQTT_PASS

            TOPIC_CONFIG    = settings.TOPIC_CONFIG
            TOPIC_COMMAND   = os.path.join(TOPIC_CONFIG,"command")

            TOPIC_COMMAND_GENERAL = os.path.join(TOPIC_COMMAND,'global')
            TOPIC_COMMAND_USER    = os.path.join(TOPIC_COMMAND,name)

            TOPIC_CONFIG_GENERAL  = os.path.join(TOPIC_CONFIG,'global')
            TOPIC_CONFIG_USER     = os.path.join(TOPIC_CONFIG,name)        
            
            

        except:
            
            
            error = traceback.format_exc()
        

        else:

            if type_message == 'command':

                TOPIC = TOPIC_COMMAND_USER if type_user == 'per_user' else TOPIC_COMMAND_GENERAL

            elif type_message == 'parameter':
                TOPIC = TOPIC_CONFIG_USER if type_user == 'per_user' else TOPIC_CONFIG_GENERAL
    
        
            try: 
                    
                auth = {'username':MQTT_USER,
                        'password': MQTT_PWD}
                
                publish.single(TOPIC, payload=json.dumps(payload),qos=2,
                            auth=auth,port=MQTT_PORT,hostname=MQTT_BROKER)
                
                return 
            
            except:
                return
        
        finally:
            return 
        
    def save(self, *args, **kwargs):
        
        flag = kwargs.pop("from_mqtt",False)

        if flag == False:
            if self.pk is None:
                # Acciones a realizar cuando se cree una nueva estación

                values = dict()
                payload = dict()
                
                payload['type_message'] = 'parameter'
                payload['type_user'] = 'per_user'

                for field in  self._meta.fields:

                    field_name = deepcopy(field.name)
                    value  = deepcopy(getattr(self,field_name))

                    if field_name != 'server':

                        if isinstance(value,Decimal):
                            value = float(value)
                        
                        if field_name == 'inference_mode':
                            if value:
                                value == 'server'
                            else:
                                value == 'other'

                        if field_name == 'type_weights':

                            if str(value) == str(0):
                                value = 'only_camara'
                            elif str(value) == str(1):
                                value = 'camara_HFS_lidar'
                            elif str(value) == str(2):
                                value = 'camara_HFS'
                            elif str(value) == str(3):
                                value == 'HFS'

                        if field_name == "measure_voltage":
                            field_name = "ina"
                        
                        if field_name == "level_reference":
                            '''
                            Define cuanto es lo minimo para considerar como alerta de crecida.
                            Cambiamos el nombre para que sea reconocible en la estación.
                            '''
                            field_name = "MIN_HEIGHT_WATER_FOR_LIDAR"
                        
                        if field_name == "send_data_mqtt":

                            field_name = "TIME_SEND_MQTT"

                        if field_name == "name":
                            field_name = "id_device"

                        values[field_name] = value 

                payload['payload'] = values
    
                self.send_for_mqtt(values.get("id_device"),payload)

            else:
                
                old_instance = Station.objects.get(pk=self.pk)

                new_values = dict()
                payload = dict()

                payload['type_message'] = 'parameter'
                payload['type_user'] = 'per_user'

                flag = False
                
                for field in self._meta.fields:

                    field_name = deepcopy(field.name)
                    old_value = getattr(old_instance, field_name)
                    new_value = deepcopy(getattr(self, field_name))

                    # Verificar si ha cambiado
                    if field_name != 'server':
                        if old_value != new_value:

                            if isinstance(new_value,Decimal):
                                new_value = float(new_value)

                            flag = True
                            
                            if field_name == 'type_weights':

                                if str(new_value) == str(0):
                                    new_value = 'only_camara'
                                elif str(new_value) == str(1):
                                    new_value = 'camara_HFS_lidar'
                                elif str(new_value) == str(2):
                                    new_value = 'camara_HFS'
                                elif str(new_value) == str(3):
                                    new_value == 'HFS'

                            if field_name == 'inference_mode':
                                if value:
                                    value == 'server'
                                else:
                                    value == 'other'

                            if field_name == "measure_voltage":
                                field_name = "ina"
                            
                            if field_name == "level_reference":
                                '''
                                Define cuanto es lo minimo para considerar como alerta de crecida.
                                Cambiamos el nombre para que sea reconocible en la estación.
                                '''
                                field_name = "MIN_HEIGHT_WATER_FOR_LIDAR"
                            
                            if field_name == "send_data_mqtt":

                                field_name = "TIME_SEND_MQTT"

                            if field_name == "name":
                                field_name = "id_device"
                            
                            new_values[field_name] = new_value


                if flag:
                    payload['payload'] = new_values
                    
                    station = Station.objects.get(pk=self.pk) 
                    
                    return_code = self.send_for_mqtt(station.name,payload)    


        super(Station, self).save(*args, **kwargs)
 


def mood_path(instance, filename):
 
    # Obtener la extensión del archivo
    ext = filename.split('.')[-1]
    # Crear un nuevo nombre de archivo único
    unique_filename = f'{datetime.now().timestamp()}.{ext}'

    return f'stations/{instance.station.name}/{unique_filename}'

class StationDataPhoto(models.Model):
    '''
    Los datos se envían por diferentes tópicos. 
    Existe un tópico para fotos y otro tópico para datos.
    '''

    station = models.ForeignKey(Station,on_delete=models.CASCADE,related_name='photo', verbose_name=_('Station_photo'))
    photo   = models.ImageField(upload_to=mood_path)  
    date    = models.DateTimeField(auto_now=True)
    objects = StationDataManager()


    def __str__(self):

        date  = self.date.strftime('%Y-%m-%d %H:%M:%S %z')
        return '{} - [{} UTC]'.format(self.station,date)
 
 
class StationCommand(models.Model):
    MODE_CHOICES = [
        (0,'----- select ------'),
        (1,'Reiniciar sistema'),
        (2,'reset_LIDAR'),
        (3,'Actualizar firmware Raspberry Pi'),
        # Agrega más modos según lo que se necesite. 
    ]

    '''
    Clase que permitirá el envío de comandos.
    '''

    station = models.ForeignKey(Station,on_delete=models.CASCADE ,unique=True)

    mode = models.PositiveSmallIntegerField(default=0, choices=MODE_CHOICES )

    def __str__(self):
        return f"Select command for Station: {self.station.name}"
    

    def __send_command_mqtt(self,):

        TOPIC = os.path.join(settings.TOPIC_COMMAND,self.station.name)
        payload = self.get_mode_display()

        publish.single(TOPIC,
                    payload=payload,
                    hostname=settings.MQTT_BROKER,
                    qos=2,
                    auth={
                        "username":settings.MQTT_USER,
                        "password":settings.MQTT_PASS
                        },
                        port=settings.MQTT_PORT)



    def save(self, *args, **kwargs):
        
        if self.mode>0:
            self.__send_command_mqtt() #Enviamos el comando por MQTT.
        
        super(StationCommand, self).save(*args, **kwargs)
 
    class Meta:
        app_label = 'home'

class StationData(models.Model):

    '''
    Clase que guardará los datos recibidos por MQTT
    '''
    
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='data', verbose_name=_('Station_data'))
    state   = models.PositiveSmallIntegerField(default=0, choices=STATION_STATES)
    date        = models.DateTimeField(auto_now=True)
    time_init   = models.FloatField(default=0)
 
    
    camera       = models.BooleanField(default=False)
    lidar_status = models.BooleanField(default=False)
    level        = models.FloatField(default=0)
    difference_H = models.FloatField(default=0)

    #------------------- Sensor HFS -------------------------#
     
    cruceta1   = models.BooleanField(default=False)
    cruceta2   = models.BooleanField(default=False)
    cruceta3   = models.BooleanField(default=False)
    cruceta4   = models.BooleanField(default=False)

    #--------------- Sensor HB100 ---------------------------#

    doppler1   = models.FloatField(default=0)
    doppler2   = models.FloatField(default=0)
    doppler3   = models.FloatField(default=0)
    doppler4   = models.FloatField(default=0)

    time_operation = models.FloatField(default=0)

    #---------------- battery voltage -----------------------#

    voltage_battery = models.FloatField(default=0)
    current_battery = models.FloatField(default=0)

    current_pannel  = models.FloatField(default=0)
    voltage_pannel  = models.FloatField(default=0)


    temperature     = models.FloatField(default=0)
    # #------------------ others -------------------------------#
    inference_ML    = models.FloatField(default=0)
    status_ML       = models.BooleanField(default=False)
    internet_MB     = models.FloatField(default=0)
  
    latest = LastDataManager()
    objects= StationDataManager()
 

    def __str__(self):
        date  = self.date.strftime('%Y-%m-%d %H:%M:%S %z')
        return '{}-{} [{} UTC]'.format(self.station, self.state, date)

    class Meta:
        # app_label = 'home'
        get_latest_by = 'date'
        ordering = ['date']

    # def get_absolute_url(self):
    #     return reverse('station_data_view', kwargs={'pk': self.pk})