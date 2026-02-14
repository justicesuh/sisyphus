from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .api_views import SearchViewSet

app_name = 'searches'

router = DefaultRouter()
router.register('', SearchViewSet, basename='search-api')

urlpatterns = [
    path('', views.search_list, name='search_list'),
    path('create/', views.search_create, name='search_create'),
    path('<uuid:uuid>/', views.search_detail, name='search_detail'),
    path('<uuid:uuid>/edit/', views.search_edit, name='search_edit'),
    path('run-all/', views.search_run_all, name='search_run_all'),
    path('<uuid:uuid>/toggle/', views.search_toggle, name='search_toggle'),
    path('<uuid:uuid>/delete/', views.search_delete, name='search_delete'),
    path('api/', include(router.urls)),
]
