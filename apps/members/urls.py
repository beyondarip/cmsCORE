from django.urls import path
from .views import HelloWorldAPIView

app_name = 'members'

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.conf import settings


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
router.register(r'tags', views.TagViewSet, basename='tag')
router.register(r'sections', views.SectionViewSet, basename='section')
router.register(r'elements', views.ElementViewSet, basename='element')
router.register(r'flashcards', views.FlashcardViewSet, basename='flashcard')
router.register(r'questions', views.QuestionViewSet, basename='question')
router.register(r'multiple-choice', views.MultipleChoiceViewSet, basename='multiple-choice')
router.register(r'todos', views.TodoViewSet, basename='todo')
router.register(r'notes', views.NoteViewSet, basename='note')
router.register(r'study/sessions', views.StudySessionViewSet, basename='study-session')
router.register(r'study/records', views.StudyRecordViewSet, basename='study-record')


urlpatterns = [
    path('hello/', HelloWorldAPIView.as_view(), name='hello_world'),
    path('', include(router.urls)),
    path('search/', views.SearchView.as_view(), name='search'),
    path('auth/', include('dj_rest_auth.urls')),    # Add the members API URLs
  path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
   path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
  
]
