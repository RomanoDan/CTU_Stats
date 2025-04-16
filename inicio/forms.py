from django import forms
from .models import Participacion, Kill
from django.forms import formset_factory,BaseFormSet

class ParticipacionForm(forms.ModelForm):
    bando = forms.ChoiceField(choices=[('RUSIA', 'Rusia'), ('UCRANIA', 'Ucrania')])
    nickname = forms.CharField(label='Nickname del jugador', max_length=50)

    class Meta:
        model = Participacion
        fields = ['murio','cantidad_disparos','cantidad_hits']  # 'nickname' está por fuera

class KillForm(forms.Form):
    victima_nickname = forms.CharField(label="Victima (Nickname)", max_length=50)
    arma = forms.CharField(max_length=50)
    distancia = forms.FloatField()

class BaseKillFormSet(BaseFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)

KillFormSet = formset_factory(KillForm, formset=BaseKillFormSet, extra=1, can_delete=True)