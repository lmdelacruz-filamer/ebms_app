"""
URL configuration for ebms_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include

# this is for images so we can see them in the browser while coding
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('ems_app.urls')),
    path('admin/', admin.site.urls),
# this is for the image so it will show in the browser
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
