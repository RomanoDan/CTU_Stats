from django.db import models
from django.db.models import Sum, F, FloatField

class Jugador(models.Model):
    nickname = models.CharField(max_length=50, unique=True)
    participaciones = models.PositiveIntegerField(default=0)
    kills = models.PositiveIntegerField(default=0)
    muertes = models.PositiveIntegerField(default=0)

    @property
    def killsporpartida(self):
        if self.participaciones == 0:
            return 0
        return self.kills / self.participaciones

    @property
    def aliveness(self):
        if self.participaciones == 0:
            return 0
        return ((self.participaciones - self.muertes) * 100) / self.participaciones

    @property
    def kdratio(self):
        if self.muertes == 0:
            return self.kills
        return self.kills / self.muertes

    def __str__(self):
        return self.nickname

    
class Participacion(models.Model):
    nickname = models.CharField(max_length=50)  # Campo de entrada manual
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name='participaciones_detalle', null=True, blank=True)
    murio = models.BooleanField(default=False)
    cantidad_kills = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        # Buscar o crear el jugador
        jugador_obj, created = Jugador.objects.get_or_create(nickname=self.nickname)
        self.jugador = jugador_obj

        # Solo sumar estadísticas si es una nueva participación
        if not self.pk:
            jugador_obj.participaciones += 1
            jugador_obj.kills += self.cantidad_kills
            if self.murio:
                jugador_obj.muertes += 1
            jugador_obj.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nickname} - Participación"
    

class Kill(models.Model):
    participacion = models.ForeignKey('Participacion', on_delete=models.CASCADE, related_name='kills')
    killer = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name='kills_hechas')
    victima = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name='veces_muerto')
    arma = models.CharField(max_length=50)
    distancia = models.FloatField()

    def __str__(self):
        return f"{self.killer.nickname} mató a {self.victima.nickname} con {self.arma} (distancia: {self.distancia})"

