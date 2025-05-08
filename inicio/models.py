from django.db import models
from django.db.models import Sum, F, FloatField
from django.utils.timezone import now

class Jugador(models.Model):
    BANDO_CHOICES = [
        ('RUSIA', 'Rusia'),
        ('UCRANIA', 'Ucrania'),
    ]
    nickname = models.CharField(max_length=50, unique=True)
    bando = models.CharField(max_length=10, choices=BANDO_CHOICES, default='RUSIA')
    participaciones = models.PositiveIntegerField(default=0)
    kills = models.PositiveIntegerField(default=0)
    teamkills = models.PositiveIntegerField(default=0)
    muertes = models.PositiveIntegerField(default=0)
    disparos = models.PositiveIntegerField(default=0)
    hits = models.PositiveIntegerField(default=0)

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
    
    @property
    def precision(self):
        if self.disparos == self.hits:
            return 100
        return (self.hits*100)/self.disparos

    def __str__(self):
        return self.nickname

class Partida(models.Model):
    nombre = models.CharField(max_length=100)
    fecha = models.DateTimeField(default=now)
    comandante_rusia = models.ForeignKey(
        Jugador, on_delete=models.SET_NULL, null=True, blank=True, related_name='partidas_comandante_rusia'
    )
    comandante_ucrania = models.ForeignKey(
        Jugador, on_delete=models.SET_NULL, null=True, blank=True, related_name='partidas_comandante_ucrania'
    )
    ganador = models.CharField(max_length=10, choices=Jugador.BANDO_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"Partida: {self.nombre} - Ganador: {self.ganador if self.ganador else 'Sin definir'}"

class Participacion(models.Model):
    nickname = models.CharField(max_length=50) 
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name='participaciones_detalle', null=True, blank=True)
    murio = models.BooleanField(default=False)
    cantidad_kills = models.PositiveIntegerField(default=0)
    cantidad_disparos = models.PositiveIntegerField(default=0)
    cantidad_hits = models.PositiveIntegerField(default=0)
    cantidad_teamkills = models.PositiveIntegerField(default=0)
    partida = models.ForeignKey(Partida, on_delete=models.CASCADE, related_name='participaciones', null=True, blank=True)

    bando = None  

    def save(self, *args, **kwargs):
        # Buscar o crear el jugador asociado
        jugador_obj, _ = Jugador.objects.get_or_create(
            nickname=self.nickname.strip(),
            defaults={'bando': self.bando if self.bando else 'RUSIA'}
        )
        self.jugador = jugador_obj

        # Guardar la participación primero
        super().save(*args, **kwargs)
        
        # Recalcular estadísticas del jugador
        participaciones = self.jugador.participaciones_detalle.all()
        jugador_obj.participaciones = participaciones.count()
        jugador_obj.kills = sum(p.cantidad_kills for p in participaciones)
        jugador_obj.muertes = participaciones.filter(murio=True).count()
        jugador_obj.disparos = sum(p.cantidad_disparos for p in participaciones)
        jugador_obj.hits = sum(p.cantidad_hits for p in participaciones)
        jugador_obj.teamkills = sum(p.cantidad_teamkills for p in participaciones)
        jugador_obj.save()

        # (Opcional) Verificación de víctimas sin bando o no asignadas
        for kill in getattr(self, 'kills', []).all():
            if not kill.victima:
                nickname_victima = kill.nickname_victima.strip()
                bando_contrario = 'UCRANIA' if self.jugador.bando == 'RUSIA' else 'RUSIA'
                victima, _ = Jugador.objects.get_or_create(
                    nickname=nickname_victima,
                    defaults={'bando': bando_contrario}
                )
                kill.victima = victima
                kill.save()


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

class Teamkill(models.Model):
    participacion = models.ForeignKey('Participacion', on_delete=models.CASCADE, related_name='teamkills')
    killer = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name='teamkills_realizadas')
    victima = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name='teamkills_recibidas')

    def __str__(self):
        return f"{self.killer.nickname} teamkilled {self.victima.nickname}"