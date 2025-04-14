from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
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

            # Crear instancia de Participacion
            participacion = Participacion(
                nickname=nickname,
                murio=murio
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
