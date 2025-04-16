from django.contrib import admin
from .models import Tag, Section, Element, StudySession, StudyRecord

class BaseAdminModel(admin.ModelAdmin):
    """Base admin class with permission control"""
    
    def has_module_permission(self, request):
        # Only user "admin2" can see these admin modules
        if request.user.username == "admin2":
            return super().has_module_permission(request)
        return False
    
    def has_view_permission(self, request, obj=None):
        # Only user "admin2" can view these objects
        if request.user.username == "admin2":
            return super().has_view_permission(request, obj)
        return False
    
    def has_change_permission(self, request, obj=None):
        # Only user "admin2" can change these objects
        if request.user.username == "admin2":
            return super().has_change_permission(request, obj)
        return False

@admin.register(Tag)
class TagAdmin(BaseAdminModel):
    list_display = ('name', 'color', 'user')
    search_fields = ('name',)
    list_filter = ('user',)

@admin.register(Section)
class SectionAdmin(BaseAdminModel):
    list_display = ('title', 'parent', 'user', 'order')
    search_fields = ('title',)
    list_filter = ('user',)

@admin.register(Element)
class ElementAdmin(BaseAdminModel):
    list_display = ('title', 'type', 'user', 'section', 'is_completed', 'created_at')
    list_filter = ('type', 'user', 'is_completed', 'is_archived', 'is_favorite')
    search_fields = ('title', 'content')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(StudySession)
class StudySessionAdmin(BaseAdminModel):
    list_display = ('user', 'started_at', 'ended_at', 'section')
    list_filter = ('user',)

@admin.register(StudyRecord)
class StudyRecordAdmin(BaseAdminModel):
    list_display = ('element', 'session', 'result', 'studied_at')
    list_filter = ('result', 'session')