from django.shortcuts import render

def default_401(request, exception=None):
    return render(request, 'core/401.html', status=401)