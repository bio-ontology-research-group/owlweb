"""aberowlweb URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.contrib import admin
from django.conf.urls.static import static
from aberowlweb.views import AboutPageView
from django.conf import settings
from django.views.generic import TemplateView

urlpatterns = [
                  path('', include('aberowl.urls')),
                  path('__debug__/', include('debug_toolbar.urls')),
                  path('admin/', admin.site.urls),
                  path('accounts/', include('accounts.urls')),
                  path('about/', AboutPageView.as_view(), name='about'),
                  path('healthcheck', TemplateView.as_view(template_name='health.html')),
                  path('docs/', TemplateView.as_view(template_name="index.html"), name='api_docs'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL)
