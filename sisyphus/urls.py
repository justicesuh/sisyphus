from django.contrib import admin
from django.urls import path

from sisyphus.ui import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index),
    path('login/', views.login),
    path('logout/', views.logout),
]
