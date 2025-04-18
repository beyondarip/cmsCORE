"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.static import serve


from django.shortcuts import render
from .views import page_not_found
from .media_views import protected_serve, FileUploadView
from .db_backup_views import backup_database, list_database_backups

def test_404(request):
    """View untuk testing halaman 404"""
    return render(request, '404.html', status=200)

urlpatterns = [
    re_path(r'^fjowejao/(?P<path>.*)$', protected_serve, name='protected_media'),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    path('404/', page_not_found, name='404'),
    path('', page_not_found, name='home'),
    path(settings.SECRET_KEY_LOGIN+"_"+'admin/', admin.site.urls),
    path('da42FH0V5PGs7Hon1YTO/', include('apps.members.urls', namespace='members')),
    path('django_f', TemplateView.as_view(template_name='index.html'), name='django_f'),
    
    path('YXBpL3VwbG9hZC8/', FileUploadView.as_view(), name='file_upload'),
    
    path('upVGVtcGxh/', TemplateView.as_view(template_name='upload_test.html'), name='test_upload'),
    
    path('updGVWaWV3/', TemplateView.as_view(template_name='login_upload.html'), name='login_upload'),
    
    # URL untuk backup database dan halaman tipuan
    path('YmFja3VwLWRiLw/', TemplateView.as_view(template_name='backup_db.html'), name='backup_db_page'),
    path('backup-db-file/', backup_database, name='backup_database'),
    path('backup-db-list/', list_database_backups, name='list_database_backups'),
]
# ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # path("__reload__/", include("django_browser_reload.urls")),
    # path('<slug:slug>/', page_view, name='page_view'),


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Set up custom error handlers
handler404 = 'config.views.page_not_found'


