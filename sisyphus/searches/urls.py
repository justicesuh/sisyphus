from django.urls import path

from . import views

app_name = 'searches'

urlpatterns = [
    path('', views.search_list, name='search_list'),
    path('create/', views.search_create, name='search_create'),
    path('<uuid:uuid>/', views.search_detail, name='search_detail'),
]
