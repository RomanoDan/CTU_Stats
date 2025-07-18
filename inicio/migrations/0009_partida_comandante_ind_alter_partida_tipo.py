# Generated by Django 5.2 on 2025-07-06 14:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inicio', '0008_jugador_playeruid'),
    ]

    operations = [
        migrations.AddField(
            model_name='partida',
            name='comandante_ind',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='partidas_comandante_ind', to='inicio.jugador'),
        ),
        migrations.AlterField(
            model_name='partida',
            name='tipo',
            field=models.CharField(default='INTERNA', max_length=30),
        ),
    ]
