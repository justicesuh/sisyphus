from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views

app_name = 'web'

urlpatterns = [
    path('', views.index, name='index'),
    path('jobs/', views.job_list, name='job_list'),
    path('companies/', views.company_list, name='company_list'),
    path('companies/<uuid:uuid>/', views.company_detail, name='company_detail'),
    path('companies/<uuid:uuid>/toggle-ban/', views.company_toggle_ban, name='company_toggle_ban'),
    path('companies/<uuid:uuid>/notes/', views.company_add_note, name='company_add_note'),
    path('companies/<uuid:uuid>/notes/<int:note_id>/delete/', views.company_delete_note, name='company_delete_note'),
    path('jobs/<uuid:uuid>/', views.job_detail, name='job_detail'),
    path('jobs/<uuid:uuid>/status/', views.job_update_status, name='job_update_status'),
    path('jobs/<uuid:uuid>/notes/', views.job_add_note, name='job_add_note'),
    path('jobs/<uuid:uuid>/notes/<int:note_id>/delete/', views.job_delete_note, name='job_delete_note'),
    path('review/', views.job_review, name='job_review'),
    path('review/<uuid:uuid>/action/', views.job_review_action, name='job_review_action'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/resume/upload/', views.resume_upload, name='resume_upload'),
    path('profile/resume/delete/', views.resume_delete, name='resume_delete'),
]
