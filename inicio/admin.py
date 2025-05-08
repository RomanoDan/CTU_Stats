from django.contrib import admin
from .models import Jugador, Participacion,Kill,Teamkill,Partida


admin.site.register(Jugador)
admin.site.register(Participacion)
admin.site.register(Kill)
admin.site.register(Teamkill)
admin.site.register(Partida)