from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import ParticipacionForm, KillFormSet
from .models import Jugador, Participacion, Kill

def inicio(request):
    return render(request, 'inicio/inicio.html')

def lista_jugadores(request):
    jugadores = Jugador.objects.all().order_by('-kills')  # Puedes ordenar como prefieras
    return render(request, 'inicio/lista_jugadores.html', {'jugadores': jugadores})

def crear_participacion(request):
    if request.method == 'POST':
        form = ParticipacionForm(request.POST)
        formset = KillFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            nickname = form.cleaned_data['nickname']
            jugador, _ = Jugador.objects.get_or_create(nickname=nickname)

            participacion = Participacion(
                nickname=nickname,
                jugador=jugador,
                murio=form.cleaned_data['murio']
            )
            participacion.save()

            cantidad_kills = 0

            for kill_form in formset:
                if not kill_form.cleaned_data or kill_form.cleaned_data.get('DELETE'):
                    continue

                victima_nickname = kill_form.cleaned_data.get('victima_nickname')
                arma = kill_form.cleaned_data.get('arma')
                distancia = kill_form.cleaned_data.get('distancia')

                # Crea la víctima si no existe
                victima, _ = Jugador.objects.get_or_create(nickname=victima_nickname)

                Kill.objects.create(
                    participacion=participacion,
                    killer=jugador,
                    victima=victima,
                    arma=arma,
                    distancia=distancia
                )

                cantidad_kills += 1

            # Actualizar estadísticas
            participacion.cantidad_kills = cantidad_kills
            participacion.save()

            jugador.participaciones += 1
            jugador.kills += cantidad_kills
            if participacion.murio:
                jugador.muertes += 1
            jugador.save()

            return redirect('lista_jugadores')
    else:
        form = ParticipacionForm()
        formset = KillFormSet()

    return render(request, 'inicio/crear_participacion.html', {
        'form': form,
        'formset': formset
    })