import os

from django.http import JsonResponse
from django.urls import path, include
from django.conf import settings
from django.contrib import admin
from base_feature_app.admin import admin_site
from django.conf.urls.static import static
from base_feature_app.views.auth import obtain_token_pair
from base_feature_project.views import SafeTokenRefreshView


def health_check(request):
    # 'project'/'environment' let external probes verify WHO answered: a shared
    # codebase means the project name alone cannot tell prod from staging
    # (measured: /qa pilot #3).
    return JsonResponse({
        'status': 'ok',
        'project': settings.BASE_DIR.parent.name,
        # settings first: DJANGO_ENV lives in backend/.env and is read by
        # decouple, and the systemd units never export it, so os.getenv alone
        # would report 'development' in production.
        'environment': getattr(
            settings, 'DJANGO_ENV', os.getenv('DJANGO_ENV', 'development')
        ),
    })


urlpatterns = [
    path('api/health/', health_check, name='health-check'),
    path('admin-gallery/', admin.site.urls),
    path('admin/', admin_site.urls),
    path('api/token/', obtain_token_pair, name='token_obtain_pair'),
    path('api/token/refresh/', SafeTokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('base_feature_app.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if getattr(settings, 'ENABLE_SILK', False):
    urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
