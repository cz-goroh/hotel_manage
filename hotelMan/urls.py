from django.contrib import admin
from django.urls import include, path, re_path
from hotelMan.admin import hotadmin
from django.conf.urls.static import static
from django.conf import settings
from . import views


app_name = 'hotelMan'
urlpatterns = [
    path('prolong/', views.prolong, name = 'prolong'),
]
