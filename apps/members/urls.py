from django.urls import path
from .views import HelloWorldAPIView

app_name = 'members'

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.conf import settings
from django.views.generic import TemplateView
from config.media_views import protected_serve, FileUploadView, FileListView
from config.db_backup_views import backup_database, list_database_backups


from django.urls import re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router = DefaultRouter()
# router.register(r'tags', views.TagViewSet, basename='tag')
# router.register(r'sections', views.SectionViewSet, basename='section')
# router.register(r'elements', views.ElementViewSet, basename='element')
# router.register(r'flashcards', views.FlashcardViewSet, basename='flashcard')
# router.register(r'questions', views.QuestionViewSet, basename='question')
# router.register(r'multiple-choice', views.MultipleChoiceViewSet, basename='multiple-choice')
# router.register(r'todos', views.TodoViewSet, basename='todo')
# router.register(r'notes', views.NoteViewSet, basename='note')
# router.register(r'study/sessions', views.StudySessionViewSet, basename='study-session')
# router.register(r'study/records', views.StudyRecordViewSet, basename='study-record')

router.register(r'tadG9kb3MK', views.TagViewSet, basename='tag')
router.register(r'sectdG9kb3', views.SectionViewSet, basename='section')
router.register(r'elements', views.ElementViewSet, basename='element')
router.register(r'flas3amVvZXc4eXVyOW', views.FlashcardViewSet, basename='flashcard')
router.register(r'que4eXVyOW', views.QuestionViewSet, basename='question')
router.register(r'mult4eXVyOW', views.MultipleChoiceViewSet, basename='multiple-choice')
router.register(r'todVyM3EyOT', views.TodoViewSet, basename='todo')
router.register(r'notlvd2F1an', views.NoteViewSet, basename='note')
router.register(r'study/sessions', views.StudySessionViewSet, basename='study-session')
router.register(r'study/records', views.StudyRecordViewSet, basename='study-record')

# router.register(r'tadG9kb3MK', views.TagViewSet, basename='tag')
# router.register(r'sectdG9kb3', views.SectionViewSet, basename='section')
# router.register(r'elem25ib3dhamUKZm', views.ElementViewSet, basename='element')
# router.register(r'flas3amVvZXc4eXVyOW', views.FlashcardViewSet, basename='flashcard')
# router.register(r'que4eXVyOW', views.QuestionViewSet, basename='question')
# router.register(r'mult4eXVyOW', views.MultipleChoiceViewSet, basename='multiple-choice')
# router.register(r'todVyM3EyOT', views.TodoViewSet, basename='todo')
# router.register(r'notlvd2F1an', views.NoteViewSet, basename='note')
# router.register(r'stuF3ZWZ3C/sessions', views.StudySessionViewSet, basename='study-session')
# router.register(r'stuF3ZWZ3C/records', views.StudyRecordViewSet, basename='study-record')


urlpatterns = [
    path('hello/', HelloWorldAPIView.as_view(), name='hello_world'),
    path('', include(router.urls)),
    path('search/', views.SearchView.as_view(), name='search'),
    path('YmFzZTY0/', include('dj_rest_auth.urls')),    # Add the members API URLs
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Moved endpoints from main urls.py
    path('YXBpL3VwbG9hZC8/', FileUploadView.as_view(), name='file_upload'),
    path('YXBpL2ZpbGVzLw/', FileListView.as_view(), name='file_list'),
    path('upVGVtcGxh/', TemplateView.as_view(template_name='upload_test.html'), name='test_upload'),
    path('updGVWaWV3/', TemplateView.as_view(template_name='login_upload.html'), name='login_upload'),
    path('YmFja3VwLWRiLw/', TemplateView.as_view(template_name='backup_db.html'), name='backup_db_page'),
    path('backup-db-file/', backup_database, name='backup_database'),
    path('backup-db-list/', list_database_backups, name='list_database_backups'),
]
