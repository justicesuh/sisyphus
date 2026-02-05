from django.urls import path

from . import views

app_name = 'companies'

urlpatterns = [
    path('', views.company_list, name='company_list'),
    path('<uuid:uuid>/', views.company_detail, name='company_detail'),
    path('<uuid:uuid>/toggle-ban/', views.company_toggle_ban, name='company_toggle_ban'),
    path('<uuid:uuid>/notes/', views.company_add_note, name='company_add_note'),
    path('<uuid:uuid>/notes/<int:note_id>/delete/', views.company_delete_note, name='company_delete_note'),
]
