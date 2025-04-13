
from django.urls import path
from inicio.views import inicio, crear_participacion, lista_jugadores

urlpatterns = [
    path('', inicio, name='inicio'),
    path('crear-participacion/', crear_participacion, name='crear_participacion'),
    path('jugadores/', lista_jugadores, name='lista_jugadores'),
]
