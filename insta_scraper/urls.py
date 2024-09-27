from django.contrib import admin
from django.urls import path
from scraper import views

urlpatterns = [
    path('',views.index),
    path('ad/',views.admin_win),
    path('db',views.database),
    path('profile',views.profile),
    path('scrap',views.scrap),
    path('scraping_admin',views.scraping_admin),
    path('admin/', admin.site.urls),
]
