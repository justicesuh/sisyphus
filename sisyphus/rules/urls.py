from django.urls import path

from . import views

app_name = 'rules'

urlpatterns = [
    path('', views.rule_list, name='rule_list'),
    path('create/', views.rule_create, name='rule_create'),
    path('apply-all/', views.rule_apply_all, name='rule_apply_all'),
    path('<uuid:uuid>/', views.rule_edit, name='rule_edit'),
    path('<uuid:uuid>/delete/', views.rule_delete, name='rule_delete'),
    path('<uuid:uuid>/toggle/', views.rule_toggle, name='rule_toggle'),
    path('<uuid:uuid>/apply/', views.rule_apply, name='rule_apply'),
]
