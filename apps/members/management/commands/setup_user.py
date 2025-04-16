from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.members.models import Tag, Section, Element

class Command(BaseCommand):
    help = 'Sets up initial data for a user'
    
    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user to set up')
    
    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" does not exist'))
            return
        
        # Create default tags
        default_tags = [
            {'name': 'Important', 'color': '#FF5733'},
            {'name': 'Work', 'color': '#33A8FF'},
            {'name': 'Personal', 'color': '#33FF57'},
            {'name': 'Study', 'color': '#D433FF'},
            {'name': 'Reference', 'color': '#FFD700'},
        ]
        
        created_tags = []
        for tag_data in default_tags:
            tag, created = Tag.objects.get_or_create(
                name=tag_data['name'],
                user=user,
                defaults={'color': tag_data['color']}
            )
            created_tags.append(tag)
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f"{status}: Tag '{tag.name}'")
        
        # Create default sections
        default_sections = [
            {'title': 'Work', 'description': 'Work-related items', 'color': '#33A8FF'},
            {'title': 'Personal', 'description': 'Personal items', 'color': '#33FF57'},
            {'title': 'Study', 'description': 'Study materials', 'color': '#D433FF'},
        ]
        
        # Create main sections first
        section_map = {}
        for section_data in default_sections:
            section, created = Section.objects.get_or_create(
                title=section_data['title'],
                user=user,
                defaults={
                    'description': section_data['description'],
                    'color': section_data['color']
                }
            )
            section_map[section_data['title']] = section
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f"{status}: Section '{section.title}'")
        
        # Create subsections
        subsections = [
            {
                'title': 'Programming',
                'description': 'Programming notes and resources',
                'color': '#FF5733',
                'parent_title': 'Study'
            },
            {
                'title': 'Languages',
                'description': 'Language learning materials',
                'color': '#33A8FF',
                'parent_title': 'Study'
            },
        ]
        
        for subsection_data in subsections:
            parent = section_map.get(subsection_data['parent_title'])
            if parent:
                subsection, created = Section.objects.get_or_create(
                    title=subsection_data['title'],
                    user=user,
                    defaults={
                        'description': subsection_data['description'],
                        'color': subsection_data['color'],
                        'parent': parent
                    }
                )
                status = 'Created' if created else 'Already exists'
                self.stdout.write(f"{status}: Subsection '{subsection.title}' under '{parent.title}'")
        
        # Optional: Create some example elements
        study_section = section_map.get('Study')
        if study_section and not Element.objects.filter(user=user).exists():
            # Create a sample note
            note = Element.objects.create(
                type=Element.NOTE,
                title="Welcome Note",
                content="# Welcome to Your Study App\n\nUse this app to organize your:\n- Notes\n- Flashcards\n- Questions\n- Todo items",
                user=user,
                section=study_section,
                is_favorite=True
            )
            note.tags.add(created_tags[0])  # Add "Important" tag
            self.stdout.write(f"Created: Welcome Note")
            
            # Create a sample todo
            todo = Element.objects.create(
                type=Element.TODO,
                title="Get Started",
                content="Explore your new study and productivity app",
                user=user,
                is_favorite=True
            )
            todo.tags.add(created_tags[0])  # Add "Important" tag
            self.stdout.write(f"Created: Todo Item")
            
            # Create a sample flashcard
            flashcard = Element.objects.create(
                type=Element.FLASHCARD,
                title="Sample Flashcard",
                content="What does API stand for?",
                additional_content="Application Programming Interface",
                user=user,
                section=study_section
            )
            self.stdout.write(f"Created: Sample Flashcard")
        
        self.stdout.write(self.style.SUCCESS(f'Successfully set up initial data for user "{username}"'))
