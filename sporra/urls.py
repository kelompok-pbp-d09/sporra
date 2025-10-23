from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from news.views import LandingPageView

urlpatterns = [
    path('', LandingPageView.as_view(), name='landing-page'),
    path('', RedirectView.as_view(url='news/', permanent=False)),
    path('admin/', admin.site.urls),
    path('news/', include('news.urls')),
    path('profile_user/', include('profile_user.urls')),
    path('event/', include('event.urls')),
    path('forum/', include('forumdiskusi.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
