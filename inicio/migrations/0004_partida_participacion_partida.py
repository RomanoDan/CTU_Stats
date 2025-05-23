# Generated by Django 5.2 on 2025-05-07 14:26

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inicio', '0003_jugador_teamkills_participacion_cantidad_teamkills_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Partida',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
                ('ganador', models.CharField(blank=True, choices=[('RUSIA', 'Rusia'), ('UCRANIA', 'Ucrania')], max_length=10, null=True)),
                ('comandante_rusia', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='partidas_comandante_rusia', to='inicio.jugador')),
                ('comandante_ucrania', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='partidas_comandante_ucrania', to='inicio.jugador')),
            ],
        ),
        migrations.AddField(
            model_name='participacion',
            name='partida',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='participaciones', to='inicio.partida'),
        ),
    ]
