
from django.urls import path
from django.contrib.auth import views as auth_views
from usuarios.views import registro

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='usuarios/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='inicio'), name='logout'),
    path('registro/', registro, name='registro'),
]
