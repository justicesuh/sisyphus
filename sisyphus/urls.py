from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('sisyphus.metrics.urls')),
    path('', include('sisyphus.jobs.urls')),
    path('', include('sisyphus.accounts.urls')),
    path('companies/', include('sisyphus.companies.urls')),
    path('rules/', include('sisyphus.rules.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # type: ignore[arg-type]
