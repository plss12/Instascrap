from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.template.loader import render_to_string
from selenium import webdriver
from .models import Profile, Insta
from .scrap import *

admin = True

def index(request):
    return render(request, 'Main.html', {'admin': admin})

def admin_win(request):
    if admin:
        return render(request, 'Admin.html')
    else:
        return index(request)
    
def scrap(request):
    if request.method == 'POST':
        user = request.POST.get('user')
        password = request.POST.get('password') 

        res = start_scraping(input_user=user, input_password=password, admin=admin)
        return render(request, 'Scrap_res.html', {'result': res})

    return render(request, 'Scrap.html')

def scraping_admin(request):
    if request.method == 'POST':
        user = request.POST.get('user')
        res = start_scraping(input_user=user, admin=admin)

    else:
        res = start_scraping(admin=admin)

    return render(request, 'Scrap_res.html', {'result': res})

def database(request):
    usuarios = Profile.objects.all()
    return render(request, 'Database.html', {'usuarios': usuarios})

def profile(request):
    data = None

    if request.method == 'POST':
        profile = request.POST.get('usuario')
        data = Profile.objects.get(profile=profile)
        return render(request, 'Profile.html', {'usuario': data})   

    if request.method == 'GET':
        profile = request.session.get('usuario', None)
        data_type = request.GET.get('type')
        if data_type == 'both':
            text = "Mutuos"
            mutual = Insta.objects.get(profile=profile, followers=True, following=True)
            context = {'data': mutual, 'text': text}
            html = render_to_string('Table.html', context)
        elif data_type == 'followers':
            text = "Seguidores no seguidos"
            followers = Insta.objects.get(profile=profile, followers=True, following=False)
            context = {'data': followers}
            html = render_to_string('Table.html', context)
        elif data_type == 'following':
            text = "Seguidos no seguidores"
            following = Insta.objects.get(profile=profile, following=True, followers=False)
            context = {'data': following}
            html = render_to_string('Table.html', context)

        return JsonResponse({'html': html})

    return render(request, 'Profile.html', {'usuario': data})