from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views

app_name = 'web'

urlpatterns = [
    path('', views.index, name='index'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<uuid:uuid>/', views.job_detail, name='job_detail'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
