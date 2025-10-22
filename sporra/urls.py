# sporra/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from news.views import LandingPageView

urlpatterns = [ 
    path('', LandingPageView.as_view(), name='landing-page'),
    path('admin/', admin.site.urls),
    path('news/', include('news.urls')),
    path('profile_user/', include('profile_user.urls')),
    

    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)