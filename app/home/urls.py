from django.urls import path

from . import views
 

urlpatterns = [
    path('', views.index, name='index'),
    path('/server', views.index, name='index_server'),
    path('station/events',views.events_page,name='events'),
    path('station/<int:pk>/', views.station, name='station_view'),
    # path('station/<int:pk>/change2/',StationUpdateView.as_view(),name='model_config'),
    path('station/<int:pk>/customize', views.customize_station, name='custome_station'),
    path('station/<int:pk>/customize/send_mqtt$', views.send_mqtt, name='send_mqtt'),
    
]
