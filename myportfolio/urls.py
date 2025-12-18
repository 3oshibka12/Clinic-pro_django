# myportfolio/urls.py
from django.contrib import admin
from django.urls import path, include # <--- Добавь include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('clinic.urls')), # <--- Добавь эту строку
]