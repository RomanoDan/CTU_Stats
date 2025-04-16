from django.shortcuts import render, redirect,get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Max, Count
from .forms import ParticipacionForm, KillFormSet
from .models import Jugador, Participacion, Kill

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
    jugadores_victimas = Jugador.objects.in_bulk(ids_victimas)

    victimas = [
        {
            'jugador': jugadores_victimas.get(item['victima']),
            'cantidad': item['cantidad']
        }
        for item in victimas_qs
        if jugadores_victimas.get(item['victima']) is not None
    ]

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
                bando_contrario = 'RUSIA' if participacion.bando == 'UCRANIA' else 'UCRANIA'
                victima, _ = Jugador.objects.get_or_create(
                    nickname=victima_nickname.strip(),
                    defaults={'bando': bando_contrario}
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
