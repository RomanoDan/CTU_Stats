from django.shortcuts import render, redirect,get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Avg, Max, Count
from .forms import ParticipacionForm, KillFormSet
from .models import Jugador, Participacion, Kill, Teamkill, Partida
import json

def inicio(request):
    return render(request, 'inicio/inicio.html')

def reglamento(request):
    return render(request, 'inicio/reglamento.html')

def info_general(request):
    return render(request, 'inicio/info_general.html')

def lista_jugadores(request):
    jugadores_rusia = Jugador.objects.filter(bando='RUSIA')
    jugadores_ucrania = Jugador.objects.filter(bando='UCRANIA')
    return render(request, 'inicio/lista_jugadores.html', {
    'jugadores_rusia': jugadores_rusia,
    'jugadores_ucrania': jugadores_ucrania,
})

def detalle_jugador(request, jugador_id):
    jugador = get_object_or_404(Jugador, id=jugador_id)

    # Estadísticas generales
    participaciones = jugador.participaciones_detalle.count()
    kills = jugador.kills
    muertes = jugador.muertes
    teamkills = jugador.teamkills
    kdratio = jugador.kdratio
    aliveness = jugador.aliveness
    kills_por_partida = kills / participaciones if participaciones > 0 else 0
    disparos = jugador.disparos
    hits = jugador.hits
    precision = jugador.precision

    # Estadísticas por arma
    kills_qs = Kill.objects.filter(killer=jugador)
    kills_por_arma = kills_qs.values('arma').annotate(
        promedio_distancia=Avg('distancia'),
        max_distancia=Max('distancia'),
        cantidad=Count('id')
    )

    # ==== Victimas ====
    victimas_qs = kills_qs.values('victima').annotate(cantidad=Count('id')).order_by('-cantidad')
    ids_victimas = [item['victima'] for item in victimas_qs]

    # ==== Teamkills ====
    teamkills_qs = Teamkill.objects.filter(killer=jugador).values('victima').annotate(cantidad=Count('id'))
    ids_teamkills = [item['victima'] for item in teamkills_qs]

    # Unificamos ids
    ids_victimas_totales = set(ids_victimas + ids_teamkills)
    jugadores_victimas_totales = Jugador.objects.in_bulk(ids_victimas_totales)

    # Creamos un diccionario con sumatoria de kills y teamkills
    victimas_dict = {}

    for item in victimas_qs:
        victimas_dict[item['victima']] = {'cantidad': item['cantidad'], 'teamkill': False}

    for item in teamkills_qs:
        if item['victima'] in victimas_dict:
            victimas_dict[item['victima']]['cantidad'] += item['cantidad']
            victimas_dict[item['victima']]['teamkill'] = True
        else:
            victimas_dict[item['victima']] = {'cantidad': item['cantidad'], 'teamkill': True}

    # Convertimos a lista ordenada
    victimas = [
        {
            'jugador': jugadores_victimas_totales.get(victima_id),
            'cantidad': data['cantidad'],
            'teamkill': data['teamkill']
        }
        for victima_id, data in victimas_dict.items()
        if jugadores_victimas_totales.get(victima_id) is not None
    ]

    # Ordenamos por cantidad descendente
    victimas.sort(key=lambda x: x['cantidad'], reverse=True)

    # ==== Asesinos ====
    asesinos_qs = Kill.objects.filter(victima=jugador).values('killer').annotate(cantidad=Count('id')).order_by('-cantidad')
    ids_asesinos = [item['killer'] for item in asesinos_qs]
    jugadores_asesinos = Jugador.objects.in_bulk(ids_asesinos)

    asesinos = [
        {
            'jugador': jugadores_asesinos.get(item['killer']),
            'cantidad': item['cantidad']
        }
        for item in asesinos_qs
        if jugadores_asesinos.get(item['killer']) is not None
    ]

    contexto = {
        'jugador': jugador,
        'participaciones': participaciones,
        'kills': kills,
        'muertes': muertes,
        'kdratio': kdratio,
        'aliveness': aliveness,
        'kills_por_partida': kills_por_partida,
        'kills_por_arma': kills_por_arma,
        'victimas': victimas,
        'asesinos': asesinos,
        'disparos': disparos,
        'hits': hits,
        'precision': precision,
        'teamkills': teamkills,
    }
    
    return render(request, 'inicio/detalle_jugador.html', contexto)





def es_admin(user):
    return user.is_staff or user.is_superuser

@login_required(login_url='login')  # Redirige al login si no está logueado
@user_passes_test(es_admin, login_url='default_401')  # Redirige si no es admin
def crear_participacion(request):
    if request.method == 'POST':
        form = ParticipacionForm(request.POST)
        formset = KillFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            nickname = form.cleaned_data['nickname']
            bando = form.cleaned_data['bando']  # Nuevo campo desde el form
            murio = form.cleaned_data['murio']
            cantidad_disparos = form.cleaned_data['cantidad_disparos']
            cantidad_hits = form.cleaned_data['cantidad_hits']

            # Crear instancia de Participacion
            participacion = Participacion(
                nickname=nickname,
                murio=murio,
                cantidad_disparos=cantidad_disparos,
                cantidad_hits=cantidad_hits
            )
            participacion.bando = bando  # Asignamos bando temporal
            participacion.save()  # Aquí ya se crea el jugador con ese bando

            cantidad_kills = 0

            for kill_form in formset:
                if not kill_form.cleaned_data or kill_form.cleaned_data.get('DELETE'):
                    continue

                victima_nickname = kill_form.cleaned_data.get('victima_nickname')
                arma = kill_form.cleaned_data.get('arma')
                distancia = kill_form.cleaned_data.get('distancia')

                if not victima_nickname:
                    continue

                # Crear o buscar la víctima con el bando contrario
                #bando_contrario = 'RUSIA' if participacion.bando == 'UCRANIA' else 'UCRANIA'
                victima, _ = Jugador.objects.get_or_create(
                    nickname=victima_nickname.strip(),
                    #defaults={'bando': bando_contrario}
                )

                Kill.objects.create(
                    participacion=participacion,
                    killer=participacion.jugador,
                    victima=victima,
                    arma=arma,
                    distancia=distancia
                )

                cantidad_kills += 1

            # Guardar la cantidad de kills y actualizar jugador + estadísticas
            participacion.cantidad_kills = cantidad_kills
            participacion.save()

            return redirect('lista_jugadores')
    else:
        form = ParticipacionForm()
        formset = KillFormSet()

    return render(request, 'inicio/crear_participacion.html', {
        'form': form,
        'formset': formset
    })



def es_admin(user):
    return user.is_staff

@login_required(login_url='login')  # Redirige al login si no está logueado
@user_passes_test(es_admin, login_url='default_401')  # Redirige si no es admin
def importar_participacion_json(request):
    if request.method == 'POST' and request.FILES.get('archivo_json'):
        # Obtener datos del formulario
        nombre_partida = request.POST.get('nombre_partida', 'Partida sin nombre')
        comandante_rusia_nickname = request.POST.get('comandante_rusia', None)
        comandante_ucrania_nickname = request.POST.get('comandante_ucrania', None)
        bando_ganador = request.POST.get('bando_ganador', None)

        # Procesar archivo JSON
        archivo = request.FILES['archivo_json']
        data = json.load(archivo)

        # Buscar o crear los comandantes
        comandante_rusia = None
        if comandante_rusia_nickname:
            comandante_rusia, _ = Jugador.objects.get_or_create(
                nickname=comandante_rusia_nickname.strip(),
                defaults={'bando': 'RUSIA'}
            )

        comandante_ucrania = None
        if comandante_ucrania_nickname:
            comandante_ucrania, _ = Jugador.objects.get_or_create(
                nickname=comandante_ucrania_nickname.strip(),
                defaults={'bando': 'UCRANIA'}
            )

        # Crear la partida
        partida = Partida.objects.create(
            nombre=nombre_partida,
            comandante_rusia=comandante_rusia,
            comandante_ucrania=comandante_ucrania,
            ganador=bando_ganador
        )

        # Crear participaciones
        participaciones_dict = {}
        for player in data.get('players', []):
            nickname = player['name'].strip()
            bando = 'RUSIA' if player['side'] == 'EAST' else 'UCRANIA'
            disparos = player.get('shots', 0)
            hits = player.get('hits', 0)

            jugador, _ = Jugador.objects.get_or_create(
                nickname=nickname,
                defaults={'bando': bando}
            )

            participacion = Participacion.objects.create(
                nickname=nickname,
                jugador=jugador,
                murio=False,  # Se actualizará después si el jugador murió
                cantidad_disparos=disparos,
                cantidad_hits=hits,
                partida=partida,  # Relacionar con la partida creada
            )
            participaciones_dict[player['playerUID']] = participacion

        # Procesar kills
        for kill in data.get('kills', []):
            killer_uid = kill.get('killer')
            victim_uid = kill.get('victim')
            arma = kill.get('weapon', 'Desconocida')
            distancia = float(kill.get('distance', 0))

            killer_part = participaciones_dict.get(killer_uid)
            victim_part = participaciones_dict.get(victim_uid)

            if not killer_part or not victim_part:
                continue

            killer = killer_part.jugador
            victima = victim_part.jugador

            # Validar si es un teamkill
            if killer.bando == victima.bando:
                Teamkill.objects.create(
                    participacion=killer_part,
                    killer=killer,
                    victima=victima
                )
                killer_part.cantidad_teamkills += 1
                killer_part.save()
                continue  # No registrar como kill normal

            # Registrar la kill
            Kill.objects.create(
                participacion=killer_part,
                killer=killer,
                victima=victima,
                arma=arma,
                distancia=distancia
            )

            # Actualizar estadísticas
            killer_part.cantidad_kills += 1
            killer_part.save()

            # Marcar que la víctima murió
            victim_part.murio = True
            victim_part.save()

        messages.success(request, 'Partida y participaciones importadas correctamente.')
        return redirect('lista_jugadores')

    return render(request, 'inicio/importar_json.html')


def detalle_partida(request, partida_id):
    partida = get_object_or_404(Partida, id=partida_id)
    participaciones = partida.participaciones.all()

    # Separar participaciones por bando
    participaciones_rusia = participaciones.filter(jugador__bando='RUSIA')
    participaciones_ucrania = participaciones.filter(jugador__bando='UCRANIA')

    # Calcular MVP
    mvp_candidates = participaciones.order_by('-cantidad_kills')
    if mvp_candidates.exists():
        max_kills = mvp_candidates.first().cantidad_kills
        mvp_candidates = mvp_candidates.filter(cantidad_kills=max_kills)

        # Restar teamkills en caso de empate
        min_teamkills = min(p.cantidad_teamkills for p in mvp_candidates)
        mvp_candidates = [p for p in mvp_candidates if p.cantidad_teamkills == min_teamkills]

        # Filtrar por jugadores vivos si sigue el empate
        if len(mvp_candidates) > 1:
            vivos = [p for p in mvp_candidates if not p.murio]
            if vivos:
                mvp_candidates = vivos

    # Si sigue el empate, dejar a todos los empatados como MVP
    mvps = mvp_candidates

    contexto = {
        'partida': partida,
        'participaciones_rusia': participaciones_rusia,
        'participaciones_ucrania': participaciones_ucrania,
        'mvps': mvps,
    }
    return render(request, 'inicio/detalle_partida.html', contexto)