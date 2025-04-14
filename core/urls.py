
from django.urls import path
from core.views import default_401

urlpatterns = [
    path('401/', default_401, name='default_401'),
]
