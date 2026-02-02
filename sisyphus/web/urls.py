from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views

app_name = 'web'

urlpatterns = [
    path('', views.index, name='index'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<uuid:uuid>/', views.job_detail, name='job_detail'),
    path('jobs/<uuid:uuid>/status/', views.job_update_status, name='job_update_status'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
