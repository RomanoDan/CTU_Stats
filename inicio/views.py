from django.shortcuts import render, redirect,get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Avg, Max, Count
from .forms import ParticipacionForm, KillFormSet
from .models import Jugador, Participacion, Kill, Teamkill, Partida, Sum
import json

def inicio(request):
    return render(request, 'inicio/inicio.html')

def reglamento(request):
    return render(request, 'inicio/reglamento.html')

def info_general(request):
    return render(request, 'inicio/info_general.html')

def lista_jugadores(request):
    # Trae todas las participaciones de tipo CHASIV
    participaciones = Participacion.objects.filter(partida__tipo='CHASIV')

    jugadores_dict = {}
    for p in participaciones:
        jugador = p.jugador
        if jugador.id not in jugadores_dict:
            jugadores_dict[jugador.id] = {
                'jugador': jugador,
                'participaciones': 0,
                'kills': 0,
                'muertes': 0,
                'kdratio': 0,
                'bando': p.bando,
                'comodin': jugador.comodin,
            }
        jugadores_dict[jugador.id]['participaciones'] += 1
        jugadores_dict[jugador.id]['kills'] += p.cantidad_kills
        jugadores_dict[jugador.id]['muertes'] += 1 if p.murio else 0
        # Si el jugador fue comodín en alguna participación, lo marcamos como comodín
        if jugador.comodin:
            jugadores_dict[jugador.id]['comodin'] = True

    # Calcula el kdratio
    for data in jugadores_dict.values():
        muertes = data['muertes']
        kills = data['kills']
        data['kdratio'] = kills / muertes if muertes > 0 else kills

    jugadores = list(jugadores_dict.values())

    return render(request, 'inicio/lista_jugadores.html', {
        'jugadores': jugadores,
    })

def detalle_jugador(request, jugador_id):
    tipo = request.GET.get('tipo', 'CHASIV')  
    jugador = get_object_or_404(Jugador, id=jugador_id)

    participaciones_qs = jugador.participaciones_detalle.filter(partida__tipo=tipo)
    participaciones = participaciones_qs.count()
    kills = participaciones_qs.aggregate(total=Count('kills'))['total'] or 0
    muertes = participaciones_qs.filter(murio=True).count()
    teamkills = participaciones_qs.aggregate(total=Count('cantidad_teamkills'))['total'] or 0
    disparos = participaciones_qs.aggregate(total=Count('cantidad_disparos'))['total'] or 0
    hits = participaciones_qs.aggregate(total=Count('cantidad_hits'))['total'] or 0

    kdratio = kills / muertes if muertes > 0 else kills
    aliveness = 100 * (participaciones - muertes) / participaciones if participaciones > 0 else 0
    kills_por_partida = kills / participaciones if participaciones > 0 else 0
    precision = (hits * 100 / disparos) if disparos > 0 else 0

    kills_qs = Kill.objects.filter(
        killer=jugador,
        participacion__partida__tipo=tipo
    )
    kills_por_arma = kills_qs.values('arma').annotate(
        promedio_distancia=Avg('distancia'),
        max_distancia=Max('distancia'),
        cantidad=Count('id')
    )

    victimas_qs = kills_qs.values('victima').annotate(cantidad=Count('id')).order_by('-cantidad')
    ids_victimas = [item['victima'] for item in victimas_qs]

    teamkills_qs = Teamkill.objects.filter(
        killer=jugador,
        participacion__partida__tipo=tipo
    ).values('victima').annotate(cantidad=Count('id'))
    ids_teamkills = [item['victima'] for item in teamkills_qs]

    ids_victimas_totales = set(ids_victimas + ids_teamkills)
    jugadores_victimas_totales = Jugador.objects.in_bulk(ids_victimas_totales)

    victimas_dict = {}
    for item in victimas_qs:
        victimas_dict[item['victima']] = {'cantidad': item['cantidad'], 'teamkill': False}
    for item in teamkills_qs:
        if item['victima'] in victimas_dict:
            victimas_dict[item['victima']]['cantidad'] += item['cantidad']
            victimas_dict[item['victima']]['teamkill'] = True
        else:
            victimas_dict[item['victima']] = {'cantidad': item['cantidad'], 'teamkill': True}

    victimas = [
        {
            'jugador': jugadores_victimas_totales.get(victima_id),
            'cantidad': data['cantidad'],
            'teamkill': data['teamkill']
        }
        for victima_id, data in victimas_dict.items()
        if jugadores_victimas_totales.get(victima_id) is not None
    ]
    victimas.sort(key=lambda x: x['cantidad'], reverse=True)

    asesinos_qs = Kill.objects.filter(
        victima=jugador,
        participacion__partida__tipo=tipo
    ).values('killer').annotate(cantidad=Count('id')).order_by('-cantidad')
    ids_asesinos = [item['killer'] for item in asesinos_qs]

    teamkills_recibidas_qs = Teamkill.objects.filter(
        victima=jugador,
        participacion__partida__tipo=tipo
    ).values('killer').annotate(cantidad=Count('id'))
    ids_teamkills_recibidas = [item['killer'] for item in teamkills_recibidas_qs]

    ids_asesinos_totales = set(ids_asesinos + ids_teamkills_recibidas)
    jugadores_asesinos_totales = Jugador.objects.in_bulk(ids_asesinos_totales)

    asesinos_dict = {}
    for item in asesinos_qs:
        asesinos_dict[item['killer']] = {'cantidad': item['cantidad'], 'teamkill': False}
    for item in teamkills_recibidas_qs:
        if item['killer'] in asesinos_dict:
            asesinos_dict[item['killer']]['cantidad'] += item['cantidad']
            asesinos_dict[item['killer']]['teamkill'] = True
        else:
            asesinos_dict[item['killer']] = {'cantidad': item['cantidad'], 'teamkill': True}

    asesinos = [
        {
            'jugador': jugadores_asesinos_totales.get(killer_id),
            'cantidad': data['cantidad'],
            'teamkill': data['teamkill']
        }
        for killer_id, data in asesinos_dict.items()
        if jugadores_asesinos_totales.get(killer_id) is not None
    ]
    asesinos.sort(key=lambda x: x['cantidad'], reverse=True)

    # Solo partidas del tipo seleccionado
    partidas_tipo = participaciones_qs.values_list('partida', flat=True).distinct()
    partidas = Partida.objects.filter(id__in=partidas_tipo)

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
        'tipo': tipo,
        'partidas': partidas,
    }
    return render(request, 'inicio/detalle_jugador.html', contexto)

def lista_jugadores_general(request):
    jugadores_ids = Participacion.objects.filter(
        partida__tipo='GENERAL'
    ).values_list('jugador_id', flat=True).distinct()

    jugadores_list = []
    for jugador in Jugador.objects.filter(id__in=jugadores_ids):
        participaciones_qs = jugador.participaciones_detalle.filter(partida__tipo='GENERAL')
        participaciones = participaciones_qs.count()
        kills = participaciones_qs.aggregate(total=Sum('cantidad_kills'))['total'] or 0
        muertes = participaciones_qs.filter(murio=True).count()
        kdratio = kills / muertes if muertes > 0 else kills
        jugadores_list.append({
            'jugador': jugador,
            'participaciones': participaciones,
            'kills': kills,
            'muertes': muertes,
            'kdratio': kdratio,
        })

    return render(request, 'inicio/lista_jugadores_general.html', {
        'jugadores': jugadores_list,
    })

def detalle_jugador_general(request, jugador_id):
    tipo = request.GET.get('tipo', 'GENERAL')  
    jugador = get_object_or_404(Jugador, id=jugador_id)

    participaciones_qs = jugador.participaciones_detalle.filter(partida__tipo=tipo)
    participaciones = participaciones_qs.count()
    kills = participaciones_qs.aggregate(total=Count('kills'))['total'] or 0
    muertes = participaciones_qs.filter(murio=True).count()
    teamkills = participaciones_qs.aggregate(total=Count('cantidad_teamkills'))['total'] or 0
    disparos = participaciones_qs.aggregate(total=Count('cantidad_disparos'))['total'] or 0
    hits = participaciones_qs.aggregate(total=Count('cantidad_hits'))['total'] or 0

    kdratio = kills / muertes if muertes > 0 else kills
    aliveness = 100 * (participaciones - muertes) / participaciones if participaciones > 0 else 0
    kills_por_partida = kills / participaciones if participaciones > 0 else 0
    precision = (hits * 100 / disparos) if disparos > 0 else 0

    kills_qs = Kill.objects.filter(
        killer=jugador,
        participacion__partida__tipo=tipo
    )
    kills_por_arma = kills_qs.values('arma').annotate(
        promedio_distancia=Avg('distancia'),
        max_distancia=Max('distancia'),
        cantidad=Count('id')
    )

    victimas_qs = kills_qs.values('victima').annotate(cantidad=Count('id')).order_by('-cantidad')
    ids_victimas = [item['victima'] for item in victimas_qs]

    teamkills_qs = Teamkill.objects.filter(
        killer=jugador,
        participacion__partida__tipo=tipo
    ).values('victima').annotate(cantidad=Count('id'))
    ids_teamkills = [item['victima'] for item in teamkills_qs]

    ids_victimas_totales = set(ids_victimas + ids_teamkills)
    jugadores_victimas_totales = Jugador.objects.in_bulk(ids_victimas_totales)

    victimas_dict = {}
    for item in victimas_qs:
        victimas_dict[item['victima']] = {'cantidad': item['cantidad'], 'teamkill': False}
    for item in teamkills_qs:
        if item['victima'] in victimas_dict:
            victimas_dict[item['victima']]['cantidad'] += item['cantidad']
            victimas_dict[item['victima']]['teamkill'] = True
        else:
            victimas_dict[item['victima']] = {'cantidad': item['cantidad'], 'teamkill': True}

    victimas = [
        {
            'jugador': jugadores_victimas_totales.get(victima_id),
            'cantidad': data['cantidad'],
            'teamkill': data['teamkill']
        }
        for victima_id, data in victimas_dict.items()
        if jugadores_victimas_totales.get(victima_id) is not None
    ]
    victimas.sort(key=lambda x: x['cantidad'], reverse=True)

    asesinos_qs = Kill.objects.filter(
        victima=jugador,
        participacion__partida__tipo=tipo
    ).values('killer').annotate(cantidad=Count('id')).order_by('-cantidad')
    ids_asesinos = [item['killer'] for item in asesinos_qs]

    teamkills_recibidas_qs = Teamkill.objects.filter(
        victima=jugador,
        participacion__partida__tipo=tipo
    ).values('killer').annotate(cantidad=Count('id'))
    ids_teamkills_recibidas = [item['killer'] for item in teamkills_recibidas_qs]

    ids_asesinos_totales = set(ids_asesinos + ids_teamkills_recibidas)
    jugadores_asesinos_totales = Jugador.objects.in_bulk(ids_asesinos_totales)

    asesinos_dict = {}
    for item in asesinos_qs:
        asesinos_dict[item['killer']] = {'cantidad': item['cantidad'], 'teamkill': False}
    for item in teamkills_recibidas_qs:
        if item['killer'] in asesinos_dict:
            asesinos_dict[item['killer']]['cantidad'] += item['cantidad']
            asesinos_dict[item['killer']]['teamkill'] = True
        else:
            asesinos_dict[item['killer']] = {'cantidad': item['cantidad'], 'teamkill': True}

    asesinos = [
        {
            'jugador': jugadores_asesinos_totales.get(killer_id),
            'cantidad': data['cantidad'],
            'teamkill': data['teamkill']
        }
        for killer_id, data in asesinos_dict.items()
        if jugadores_asesinos_totales.get(killer_id) is not None
    ]
    asesinos.sort(key=lambda x: x['cantidad'], reverse=True)

    partidas_tipo = participaciones_qs.values_list('partida', flat=True).distinct()
    partidas = Partida.objects.filter(id__in=partidas_tipo)

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
        'tipo': tipo,
        'partidas': partidas,
    }
    return render(request, 'inicio/detalle_jugador_general.html', contexto)

def es_admin(user):
    return user.is_staff
@login_required(login_url='login')
@user_passes_test(es_admin, login_url='default_401')
def importar_participacion_json(request):
    if request.method == 'POST' and request.FILES.get('archivo_json'):
        nombre_partida = request.POST.get('nombre_partida', 'Partida sin nombre')
        comandante_west_nickname = request.POST.get('comandante_west', None)
        comandante_east_nickname = request.POST.get('comandante_east', None)
        bando_ganador = request.POST.get('bando_ganador', None)
        tipo = request.POST.get('tipo', 'INTERNA')

        archivo = request.FILES['archivo_json']
        data = json.load(archivo)

        partida = Partida.objects.create(
            nombre=nombre_partida,
            ganador=bando_ganador,
            tipo=tipo,
        )

        # Crear participaciones
        participaciones_dict = {}
        for player in data.get('players', []):
            nickname = player['name'].strip()
            playeruid = player['playerUID']
            bando = player.get('side', 'IND')  
            disparos = player.get('shots', 0)
            hits = player.get('hits', 0)

            jugador, created = Jugador.objects.get_or_create(
                playeruid=playeruid,
                defaults={'nickname': nickname}
            )
            
            if not created and jugador.nickname != nickname:
                jugador.nickname = nickname
                jugador.save()

            participacion = Participacion.objects.create(
                nickname=nickname,
                jugador=jugador,
                murio=False,
                cantidad_disparos=disparos,
                cantidad_hits=hits,
                partida=partida,
                bando=bando,  
            )
            participaciones_dict[player['playerUID']] = participacion

        comandante_west = None
        if comandante_west_nickname:
            comandante_west = Jugador.objects.filter(nickname=comandante_west_nickname).first()

        comandante_east = None
        if comandante_east_nickname:
            comandante_east = Jugador.objects.filter(nickname=comandante_east_nickname).first()
        
        partida.comandante_west = comandante_west
        partida.comandante_east = comandante_east
        partida.save()

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

            # Validar si es un teamkill usando el bando de la participación
            if killer_part.bando == victim_part.bando:
                Teamkill.objects.create(
                    participacion=killer_part,
                    killer=killer_part.jugador,
                    victima=victim_part.jugador
                )
                killer_part.cantidad_teamkills += 1
                killer_part.save()
                victim_part.murio = True
                victim_part.save()
                continue

            # Registrar la kill normal
            Kill.objects.create(
                participacion=killer_part,
                killer=killer_part.jugador,
                victima=victim_part.jugador,
                arma=arma,
                distancia=distancia
            )
            killer_part.cantidad_kills += 1
            killer_part.save()
            victim_part.murio = True
            victim_part.save()

        messages.success(request, 'Partida y participaciones importadas correctamente.')
        return redirect('inicio')

    return render(request, 'inicio/importar_json.html')


def detalle_partida(request, partida_id):
    partida = get_object_or_404(Partida, id=partida_id)
    participaciones = partida.participaciones.all()

    # Separar participaciones por bando usando el campo bando de Participacion
    participaciones_east = participaciones.filter(bando='EAST', jugador__comodin=False)
    participaciones_west = participaciones.filter(bando='WEST', jugador__comodin=False)
    participaciones_comodines = participaciones.filter(jugador__comodin=True)

    # Calcular MVP (igual que antes)
    mvp_candidates = participaciones.order_by('-cantidad_kills')
    if mvp_candidates.exists():
        max_kills = mvp_candidates.first().cantidad_kills
        mvp_candidates = mvp_candidates.filter(cantidad_kills=max_kills)
        min_teamkills = min(p.cantidad_teamkills for p in mvp_candidates)
        mvp_candidates = [p for p in mvp_candidates if p.cantidad_teamkills == min_teamkills]
        if len(mvp_candidates) > 1:
            vivos = [p for p in mvp_candidates if not p.murio]
            if vivos:
                mvp_candidates = vivos
    mvps = mvp_candidates

    contexto = {
        'partida': partida,
        'participaciones_east': participaciones_east,
        'participaciones_west': participaciones_west,
        'participaciones_comodines': participaciones_comodines,
        'mvps': mvps,
    }
    return render(request, 'inicio/detalle_partida.html', contexto)