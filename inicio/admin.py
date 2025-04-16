from django.contrib import admin
from .models import Jugador, Participacion,Kill,TeamKill


admin.site.register(Jugador)
admin.site.register(Participacion)
admin.site.register(Kill)
admin.site.register(TeamKill)