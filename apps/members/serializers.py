from rest_framework import serializers


class HelloWorldSerializer(serializers.Serializer):
    """
    A simple serializer for our hello world API endpoint
    """
    message = serializers.CharField(read_only=True)
    your_name = serializers.CharField(required=False, max_length=100)


from rest_framework import serializers
from .models import Tag, Section, Element, StudySession, StudyRecord
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        # Add the current user to the tag
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ['id', 'title', 'description', 'color', 'icon', 'parent', 'order']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        # Add the current user to the section
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class ElementSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source='tags'
    )
    
    class Meta:
        model = Element
        fields = [
            'id', 'type', 'title', 'content', 'additional_content', 'data',
            'created_at', 'updated_at', 'section', 'tags', 'tag_ids',
            'order', 'is_archived', 'is_favorite', 'is_completed',
            'completed_at', 'due_date'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tags']
    
    def create(self, validated_data):
        # Add the current user to the element
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class ElementDetailSerializer(ElementSerializer):
    section = SectionSerializer(read_only=True)
    section_id = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(),
        write_only=True,
        required=False,
        source='section'
    )
    
    class Meta(ElementSerializer.Meta):
        fields = ElementSerializer.Meta.fields + ['section_id']

class StudySessionSerializer(serializers.ModelSerializer):
    duration = serializers.DurationField(read_only=True)
    
    class Meta:
        model = StudySession
        fields = ['id', 'started_at', 'ended_at', 'section', 'duration']
        read_only_fields = ['id', 'started_at', 'duration']
    
    def create(self, validated_data):
        # Add the current user to the study session
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class StudyRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyRecord
        fields = ['id', 'session', 'element', 'result', 'time_spent', 'studied_at', 'notes']
        read_only_fields = ['id', 'studied_at']



class FlashcardSerializer(ElementSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['front'] = serializers.CharField(source='content', required=True)
        self.fields['back'] = serializers.CharField(source='additional_content', required=True)
    
    def create(self, validated_data):
        validated_data['type'] = Element.FLASHCARD
        return super().create(validated_data)

class QuestionSerializer(ElementSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['question'] = serializers.CharField(source='content', required=True)
        self.fields['answer'] = serializers.CharField(source='additional_content', required=True)
    
    def create(self, validated_data):
        validated_data['type'] = Element.QUESTION
        return super().create(validated_data)
class MultipleChoiceSerializer(ElementSerializer):
    # Define these as regular fields but make them not required for GET requests
    choices = serializers.ListField(
        child=serializers.CharField(),
        required=False  # This is important
    )
    correct_answer = serializers.CharField(required=False)  # This is important
    
    class Meta:
        model = Element
        fields = [
            'id', 'type', 'title', 'content', 'additional_content', 'data',
            'created_at', 'updated_at', 'section', 'tags', 'tag_ids',
            'order', 'is_archived', 'is_favorite', 'is_completed',
            'completed_at', 'due_date', 'choices', 'correct_answer'  # Include the new fields
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tags']
    
    def to_representation(self, instance):
        # First get the standard representation
        rep = super().to_representation(instance)
        
        # Then safely add the choices and correct_answer if they exist
        if instance.data and isinstance(instance.data, dict):
            rep['choices'] = instance.data.get('choices', [])
            rep['correct_answer'] = instance.data.get('correct_answer', '')
        else:
            rep['choices'] = []
            rep['correct_answer'] = ''
            
        return rep
    
    def create(self, validated_data):
        # Extract choices and correct_answer if present
        choices = validated_data.pop('choices', [])
        correct_answer = validated_data.pop('correct_answer', None)
        
        # Set the type
        validated_data['type'] = Element.MULTIPLE_CHOICE
        
        # Initialize data if not present
        if 'data' not in validated_data:
            validated_data['data'] = {}
        
        # Add choices and correct_answer to data
        if choices:
            validated_data['data']['choices'] = choices
        if correct_answer:
            validated_data['data']['correct_answer'] = correct_answer
        
        # Create the instance
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Extract choices and correct_answer if present
        choices = validated_data.pop('choices', None)
        correct_answer = validated_data.pop('correct_answer', None)
        
        # Initialize data if not present
        if not instance.data:
            instance.data = {}
        
        # Update choices and correct_answer in data if provided
        if choices is not None:
            instance.data['choices'] = choices
        if correct_answer is not None:
            instance.data['correct_answer'] = correct_answer
        
        # Update data in validated_data
        validated_data['data'] = instance.data
        
        # Update the instance
        return super().update(instance, validated_data)

class TodoSerializer(ElementSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['task'] = serializers.CharField(source='content', required=True)
    
    def create(self, validated_data):
        validated_data['type'] = Element.TODO
        return super().create(validated_data)

class NoteSerializer(ElementSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'] = serializers.CharField(required=True)
    
    def create(self, validated_data):
        validated_data['type'] = Element.NOTE
        return super().create(validated_data)
    
from .models import NoteImage
# Add to serializers.py

class NoteImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteImage
        fields = ['id', 'image', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']