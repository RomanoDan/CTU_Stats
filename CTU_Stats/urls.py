
from django.contrib import admin
from django.urls import path, include
from inicio.views import inicio

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('inicio.urls'))
]
