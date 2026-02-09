from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .api_views import RuleViewSet

app_name = 'rules'

router = DefaultRouter()
router.register('', RuleViewSet, basename='rule-api')

urlpatterns = [
    path('', views.rule_list, name='rule_list'),
    path('create/', views.rule_create, name='rule_create'),
    path('apply-all/', views.rule_apply_all, name='rule_apply_all'),
    path('<uuid:uuid>/', views.rule_edit, name='rule_edit'),
    path('<uuid:uuid>/delete/', views.rule_delete, name='rule_delete'),
    path('<uuid:uuid>/toggle/', views.rule_toggle, name='rule_toggle'),
    path('<uuid:uuid>/apply/', views.rule_apply, name='rule_apply'),
    path('api/', include(router.urls)),
]
