import os
import sys
from django.apps import AppConfig
#from .utils import mqtt_client

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + 'utils')

# from .utils import mqtt_client
class HomeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "home"
 
    def ready(self):
        import home.signals
        #mqtt_client.start_mqtt_client()