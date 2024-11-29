import sys
import os
import django

# Añade el directorio raíz de tu proyecto a PYTHONPATH
sys.path.append('/app')  # Ajusta esta ruta según la estructura de tu proyecto

# Configura el módulo de configuración de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")  # Reemplaza 'nombre_del_proyecto' con el nombre real de tu proyecto

# Configura Django
django.setup()


from home.models import Server,Station,StationData
import datetime 
import random

def run(): 
    def random_datetime():
        now = datetime.datetime.now()
        random_days = random.randint(0, 30)
        random_hours = random.randint(0, 23)
        random_minutes = random.randint(0, 59)
        random_seconds = random.randint(0, 59)
        return now  

    server1 = Server(name='Server1', mode=1, date=datetime.datetime.now(), email_to='aef@dominio.com')
    server1.save()

    # # server2 = Server(name='Server4', mode=1, date=datetime.datetime.now(), email_to='abc@dominio.com')
    # # server2.save()

 
    # station = str(random.randint(1, 100))+str(random.randint(1, 100))
    # location = f"Location {random.randint(1, 100)}"
    # name = f"Name {random.randint(1, 100)}"
    # time_init = random.uniform(0, 24)
    # latitude = random.uniform(-90, 90)
    # longitude = random.uniform(-180, 180)
    # camera = bytes(random.getrandbits(8) for _ in range(10))  # Datos binarios aleatorios
    # level = random.uniform(0, 100)
    # difference_H = random.uniform(0, 10)
    # voltage = random.uniform(10, 14)


    # st = Station(
    #     code=2,
    #     name=station,
    #     radar_HB100=True,
    #     radar_HFS=True,
    #     lidar=True,
    #     INA=True,
    #     camera=True,
    #     set_level_reference=True,
    #     level_reference=10,
    #     latitude=10,
    #     longitude=-76
        
    #      )
    # # st.save()

    # # Crear una instancia del modelo y guardar los datos
    # m = StationData(
    #     station=st,
    #     state =1,
    #     location=location,
    #     date=random_datetime(),
    #     name=name,
    #     time_init=time_init,
    #     latitude=latitude,
    #     longitude=longitude,
    #     camera=camera,
    #     level=level,
    #     difference_H=difference_H,
    #     voltage=voltage,
    #     cruceta1=False,
    #     cruceta2=False,
    #     cruceta3=False,
    #     cruceta4=False,
    #     doppler1=10,
    #     doppler2=11,
    #     doppler3=11,
    #     doppler4=234,
    # )

    # m.save()
run()