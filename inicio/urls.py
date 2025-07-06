
from django.urls import path
from inicio.views import inicio, lista_jugadores,lista_jugadores_general,reglamento,info_general,detalle_jugador,detalle_jugador_general,detalle_partida_general,importar_participacion_json,detalle_partida

urlpatterns = [
    path('', inicio, name='inicio'),
    path('jugadores/', lista_jugadores, name='lista_jugadores'),
    path('reglamento/', reglamento, name='reglamento'),
    path('info-campana/', info_general, name='info_general'),
    path('jugador/<int:jugador_id>/', detalle_jugador, name='detalle_jugador'),
    path('importar-json/', importar_participacion_json, name='importar_json'),
    path('partida/<int:partida_id>/', detalle_partida, name='detalle_partida'),
    path('partida_g/<int:partida_id>/', detalle_partida_general, name='detalle_partida_general'),
    path('jugadores_g/', lista_jugadores_general, name='lista_jugadores_general'),
    path('jugador_g/<int:jugador_id>/', detalle_jugador_general, name='detalle_jugador_general'),
]
