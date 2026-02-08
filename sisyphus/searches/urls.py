from django.urls import path

from . import views

app_name = 'searches'

urlpatterns = [
    path('', views.search_list, name='search_list'),
    path('create/', views.search_create, name='search_create'),
    path('<uuid:uuid>/', views.search_detail, name='search_detail'),
    path('<uuid:uuid>/edit/', views.search_edit, name='search_edit'),
    path('<uuid:uuid>/toggle/', views.search_toggle, name='search_toggle'),
    path('<uuid:uuid>/delete/', views.search_delete, name='search_delete'),
]
