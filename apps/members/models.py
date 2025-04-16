from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone

class Tag(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=20, default="#3498db")  # Hex color code
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tags", null=True, blank=True)
    
    def __str__(self):
        return self.name


class Section(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=20, default="#3498db")  # Hex color code
    icon = models.CharField(max_length=50, blank=True)  # For frontend icon selection
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sections")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name="subsections")
    order = models.IntegerField(default=0)
    
    def __str__(self):
        return self.title

class Element(models.Model):
    # Element types
    FLASHCARD = 'flashcard'
    QUESTION = 'question'
    MULTIPLE_CHOICE = 'multiple_choice'
    TODO = 'todo'
    NOTE = 'note'
    
    ELEMENT_TYPES = [
        (FLASHCARD, 'Flashcard'),
        (QUESTION, 'Question and Answer'),
        (MULTIPLE_CHOICE, 'Multiple Choice Question'),
        (TODO, 'Todo Item'),
        (NOTE, 'Note'),
    ]
    
    # Basic fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=20, choices=ELEMENT_TYPES)
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="elements")
    
    # Organization
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True, related_name="elements")
    tags = models.ManyToManyField(Tag, blank=True, related_name="elements")
    order = models.IntegerField(default=0)
    is_archived = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    
    # Content fields based on element type
    content = models.TextField(blank=True)  # Main content (note text, question text, flashcard front)
    additional_content = models.TextField(blank=True)  # Additional content (answer, flashcard back)
    
    # For more complex data structures (multiple choice options, relationships, metadata)
    data = models.JSONField(default=dict, blank=True)
    
    # Tracking for todos and study items
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['order', '-updated_at']
    
    def __str__(self):
        return f"{self.get_type_display()}: {self.title}"
    
    def mark_as_complete(self):
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()
    
    def mark_as_incomplete(self):
        self.is_completed = False
        self.completed_at = None
        self.save()
    
    # Helper methods for relationship management
    def add_related_element(self, element, relationship_type="related"):
        """Add a relationship to another element"""
        if 'relationships' not in self.data:
            self.data['relationships'] = []
        
        self.data['relationships'].append({
            'element_id': str(element.id),
            'type': relationship_type,
            'added_at': timezone.now().isoformat()
        })
        self.save()
    
    def get_related_elements(self, relationship_type=None):
        """Get all related elements, optionally filtered by relationship type"""
        if 'relationships' not in self.data:
            return Element.objects.none()
        
        relationship_ids = []
        for relation in self.data['relationships']:
            if relationship_type is None or relation['type'] == relationship_type:
                relationship_ids.append(relation['element_id'])
        
        return Element.objects.filter(id__in=relationship_ids)
    

class StudySession(models.Model):
    """Track study sessions for analytics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="study_sessions")
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True)
    
    def end_session(self):
        self.ended_at = timezone.now()
        self.save()
    
    @property
    def duration(self):
        end = self.ended_at or timezone.now()
        return end - self.started_at

class StudyRecord(models.Model):
    """Track performance on individual elements during study"""
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE)
    element = models.ForeignKey(Element, on_delete=models.CASCADE)
    result = models.CharField(max_length=20, choices=[
        ('correct', 'Correct'),
        ('incorrect', 'Incorrect'),
        ('hard', 'Difficult'),
        ('easy', 'Easy'),
    ], null=True, blank=True)
    time_spent = models.DurationField(null=True, blank=True)
    studied_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)


# Add to models.py

class NoteImage(models.Model):
    """Store images for notes"""
    note = models.ForeignKey(Element, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='notes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.note.title}"
