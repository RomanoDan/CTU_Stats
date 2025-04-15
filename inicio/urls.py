
from django.urls import path
from inicio.views import inicio, crear_participacion, lista_jugadores,reglamento,info_general,detalle_jugador

urlpatterns = [
    path('', inicio, name='inicio'),
    path('crear-participacion/', crear_participacion, name='crear_participacion'),
    path('jugadores/', lista_jugadores, name='lista_jugadores'),
    path('reglamento/', reglamento, name='reglamento'),
    path('info-campana/', info_general, name='info_general'),
    path('jugador/<int:jugador_id>/', detalle_jugador, name='detalle_jugador'),
]
