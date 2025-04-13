from django import forms
from .models import Participacion, Kill
from django.forms import formset_factory

class ParticipacionForm(forms.ModelForm):
    nickname = forms.CharField(label='Nickname del jugador', max_length=50)

    class Meta:
        model = Participacion
        fields = ['murio']  # 'nickname' está por fuera

class KillForm(forms.Form):
    victima_nickname = forms.CharField(label="Victima (Nickname)", max_length=50)
    arma = forms.CharField(max_length=50)
    distancia = forms.FloatField()

KillFormSet = formset_factory(KillForm, extra=1, can_delete=True)