import sys
import os
import django



# Añade el directorio raíz de tu proyecto a PYTHONPATH
sys.path.append('/app')  # Ajusta esta ruta según la estructura de tu proyecto

# Configura el módulo de configuración de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")  # Reemplaza 'nombre_del_proyecto' con el nombre real de tu proyecto

# Configura Django
django.setup()

from django.conf import settings

from django.core.mail import send_mail

def enviar_correo_ejemplo():
    subject = 'Asunto del correo'
    message = 'Este es el contenido del correo electrónico.'
    from_email = settings.EMAIL_HOST_USER
    # from_email = 'acastro@igp.gob.pe'
    recipient_list = ['acastro@igp.gob.pe','armando.castro.c@uni.pe']  

 
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list,fail_silently=True,)
 
enviar_correo_ejemplo()