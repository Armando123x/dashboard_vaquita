 
from .others import *
from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime, timezone, timedelta
from django.contrib.auth.decorators import login_required
from .models import Server, Station, StationData
from .utils.mqtt_client import * 
from .models import Station 
from django.core.paginator import Paginator


def get_stations():

    # stations = list(StationData.latest.all().values())
    # stations.sort(key=lambda x: x.date, reverse=True)

    stations = Station.objects.all()
    return stations


def format_time(dt_seconds):
    # Define las constantes de tiempo en segundos
    minute = 60
    hour = 60 * minute
    day = 24 * hour
    month = 30 * day  # Aproximadamente 30 días por mes
    
    # Dependiendo del valor de dt_seconds, convierte a la unidad adecuada
    if dt_seconds >= month:
        months = dt_seconds // month
        days = (dt_seconds % month) // day
        return f"{int(months)} meses, {int(days)} días"
    elif dt_seconds >= day:
        days = dt_seconds // day
        hours = (dt_seconds % day) // hour
        return f"{int(days)} días, {int(hours)} horas"
    elif dt_seconds >= hour:
        hours = dt_seconds // hour
        minutes = (dt_seconds % hour) // minute
        return f"{int(hours)} horas, {int(minutes)} minutos"
    elif dt_seconds >= minute:
        minutes = dt_seconds // minute
        seconds = dt_seconds % minute
        return f"{int(minutes)} minutos, {int(seconds)} segundos"
    else:
        return f"{int(dt_seconds)} segundos"
    

def events_page(request):
    stations = list(StationData.latest.all().values())
    stations.sort(key=lambda x: x.date, reverse=True)

    obj = Server.objects.first()

    events = obj.events


    data = dict()

    for event in events:
        if len(event.keys())>0:
            event['activation_time'] = datetime.fromisoformat(event['activation_time'])
    
    eventos = events[::-1]
    
    paginator = Paginator(eventos, 10) 

    page_number = request.GET.get('page',1)
    page_obj = paginator.get_page(page_number)

    data['title'] = "Eventos"
    data['stations'] = stations
    data['page_obj'] = page_obj
    


    return render(request,"pages/alert.html",data)


def index(request):
    obj = Server.objects.first() #Solo se define un server

    server = Server.objects.filter().values()[0]
    server['mode'] = obj.SERVER_MODES[server['mode']][1]
 
    stations = list(StationData.latest.all().values())
    stations.sort(key=lambda x: x.date, reverse=True)
    #filter
    events = obj.events

    for event in events:
        if len(event.keys())>0:
            event['activation_time'] = datetime.fromisoformat(event['activation_time'])
    
    events = events[::-1][:7]

    data = {
        'title': server['name'],
        'suptitle': 'Server',
        'stations': stations,
        'events': events,
        'server': server,
        'debug': '',
        'index_config':True
    }
    
    return render(request, 'pages/server.html', data)




 

def station(request, pk):

    stations = get_stations()

    server = Server.objects.filter()[0]

    stations = list(StationData.latest.all().values())
    stations.sort(key=lambda x: x.date, reverse=True)

    station = Station.objects.get(pk=pk)
    #station_data = StationData.objects.filter(station=station).order_by('-date').values()
    station_data = StationData.objects.get_values(station)
    latest = station_data.first()

    try:
        # heights = StationData.objects.filter(station=station).order_by('-date').values_list('difference_H', flat=True)[:15] 
        y_heights = StationData.objects.get_latest_per_key(station=station,key='difference_H')
        x_heights = StationData.objects.get_latest_per_key(station=station,key='date')

        x_heights = [dt.strftime("%H:%M:%S") for dt in x_heights]
        x_heights = json.dumps(x_heights)

    except :
        y_heights = numpy.ones(15)*999
        x_heights = (numpy.arange(15)).tolist()

    try:   
        #voltage_panel = StationData.objects.filter(station=station).order_by('-date').values_list('voltage_pannel', flat=True)[:15] 
        y_voltage_panel = StationData.objects.get_latest_per_key(station=station,key='voltage_pannel')
        x_voltage_panel = StationData.objects.get_latest_per_key(station=station,key='date')
        x_voltage_panel = [dt.strftime("%H:%M:%S") for dt in x_voltage_panel]
        x_voltage_panel = json.dumps(x_voltage_panel)    
    
    except :
        y_voltage_panel = numpy.ones(15)*999
        x_voltage_panel = (numpy.arange(15)).tolist()
    
    try:
        #voltage_battery = StationData.objects.filter(station=station).order_by('-date').values_list('voltage_battery', flat=True)[:15] 
        y_voltage_battery = StationData.objects.get_latest_per_key(station=station,key='voltage_battery')
        x_voltage_battery = StationData.objects.get_latest_per_key(station=station,key='date')
        x_voltage_battery = [dt.strftime("%H:%M:%S") for dt in x_voltage_battery]
        x_voltage_battery = json.dumps(x_voltage_battery)      
    
    except :
        y_voltage_battery = numpy.ones(15)*999
        x_voltage_battery = (numpy.arange(15)).tolist()
    
    try:
        time_latest = StationData.objects.get_latest_time(station=station)

        dt = datetime.now().timestamp() - time_latest.timestamp()
        
        time_latest = format_time(dt)
        

    except:
        time_latest = None

    try:
        latest_image = StationDataPhoto.objects.latest('date')
        latest_image = latest_image.photo.name  # Retornar el nombre del archivo de la imagen
    except StationDataPhoto.DoesNotExist:
        latest_image = os.path.join(settings.STATIC_URL,'img',"empty.png")
    else: 
        latest_image = os.path.join(settings.MEDIA_URL,latest_image)

    try: 
        time_img = StationDataPhoto.objects.get_latest_time(station=station)

        dt = datetime.now().timestamp() - time_img.timestamp()
        img_time_latest = format_time(dt)

    except:
        img_time_latest = None


    data = {
        'title': server.name,
        'suptitle': 'Stations',
        'station': station, 
        'stations':stations,
        'x_heights':(x_heights),
        'y_heights':list(y_heights), 
        'y_voltage_panel':list(y_voltage_panel),
        'x_voltage_panel':(x_voltage_panel),
        'y_voltage_battery':list(y_voltage_battery),
        'x_voltage_battery':(x_voltage_battery),
        'latest_data':latest,
        'time_latest':time_latest,
        'img_latest': img_time_latest,
        'url_img':latest_image,
        'pk':pk
    }

    return render(request, 'pages/station.html', data)


@login_required
def customize_station(request,pk):

    server = Server.objects.filter()[0]

    stations = list(StationData.latest.all().values())
    stations.sort(key=lambda x: x.date, reverse=True)

    data = {
        'title': server.name,
        'suptitle': 'Configure server',
        'stations': stations,
        'pk':pk
    }
    return render(request, 'pages/customize.html', data)    

@login_required
def send_mqtt(request,pk):

    
    message = request.GET.get("message",None)
   
    type_   = request.GET.get("type",None)
    option  = request.GET.get("option",None)

   
    
    if message is None or type_ is None:

        return HttpResponse("Error envío MQTT",status=400)
    
    if type_=="per_user":

        if pk == None:
            return HttpResponse("Error envío MQTT",status=400)

        station = Station.objects.get(pk=pk)
        name_station = station.name

 
    payload = dict()

    payload['message'] = message
    payload['type']    = type_
    if type_=="per_user":
        payload['name']    = name_station
    payload['option']  = option

 

    response = mqtt_send(payload)

    if response == False:

        return HttpResponse("Error envío MQTT",status=400)
    
    else:

        return HttpResponse("Correcto envío por MQTT")

