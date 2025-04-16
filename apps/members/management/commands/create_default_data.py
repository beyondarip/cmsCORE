import random
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from apps.members.models import Tag, Section, Element, StudySession, StudyRecord

class Command(BaseCommand):
    help = 'Creates default data for the members app'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=5,
            help='Number of users to create'
        )

    def handle(self, *args, **options):
        num_users = options['users']
        
        self.stdout.write(self.style.SUCCESS(f'Creating {num_users} users with default data...'))
        
        # Use transaction to ensure data consistency
        with transaction.atomic():
            # Create users
            users = self._create_users(num_users)
            
            # Create data for each user
            for user in users:
                self.stdout.write(f'Creating data for user: {user.username}')
                self._create_user_data(user)
        
        self.stdout.write(self.style.SUCCESS('Successfully created default data!'))

    def _create_users(self, num_users):
        """Create sample users"""
        users = []
        
        # Create or get admin user
        try:
            admin = User.objects.get(username='admin')
            self.stdout.write('Admin user already exists')
        except User.DoesNotExist:
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpassword'
            )
            self.stdout.write('Created admin user')
        users.append(admin)
        
        # Create regular users
        domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'example.com']
        first_names = ['John', 'Jane', 'Michael', 'Sara', 'David', 'Lisa', 'Robert', 'Emily', 'William', 'Olivia']
        last_names = ['Smith', 'Johnson', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Wilson', 'Taylor', 'Anderson']
        
        for i in range(1, num_users):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f"{first_name.lower()}{last_name.lower()}{random.randint(1, 99)}"
            email = f"{username}@{random.choice(domains)}"
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )
            
            if created:
                user.set_password(f"password{i}")
                user.save()
                self.stdout.write(f'Created user: {username}')
            else:
                self.stdout.write(f'User {username} already exists')
                
            users.append(user)
            
        return users

    def _create_user_data(self, user):
        """Create data for a specific user"""
        # Create tags
        tags = self._create_tags(user)
        
        # Create sections
        sections = self._create_sections(user)
        
        # Create elements
        elements = self._create_elements(user, sections, tags)
        
        # Create study sessions and records
        self._create_study_data(user, sections, elements)
        
    def _create_tags(self, user):
        """Create sample tags"""
        tag_data = [
            {'name': 'Important', 'color': '#FF0000'},
            {'name': 'Review', 'color': '#FFA500'},
            {'name': 'Easy', 'color': '#00FF00'},
            {'name': 'Difficult', 'color': '#0000FF'},
            {'name': 'Exam', 'color': '#800080'},
            {'name': 'Urgent', 'color': '#FF00FF'},
            {'name': 'Reference', 'color': '#008080'},
            {'name': 'Need Help', 'color': '#FF4500'},
            {'name': 'Favorite', 'color': '#FFD700'},
            {'name': 'New Material', 'color': '#32CD32'},
        ]
        
        tags = []
        for item in tag_data:
            tag, created = Tag.objects.get_or_create(
                user=user,
                name=item['name'],
                defaults={'color': item['color']}
            )
            tags.append(tag)
            
            if created:
                self.stdout.write(f'  Created tag: {item["name"]}')
                
        return tags
        
    def _create_sections(self, user):
        """Create sample sections with hierarchy"""
        # Main sections (parents)
        main_sections_data = [
            {'title': 'Mathematics', 'description': 'All math related content', 'color': '#FFD700', 'icon': 'calculator'},
            {'title': 'Physics', 'description': 'Physics concepts and problems', 'color': '#1E90FF', 'icon': 'atom'},
            {'title': 'Computer Science', 'description': 'CS theory and practice', 'color': '#32CD32', 'icon': 'laptop-code'},
            {'title': 'Languages', 'description': 'Language learning materials', 'color': '#FF69B4', 'icon': 'language'},
            {'title': 'Personal Projects', 'description': 'My personal project notes', 'color': '#9370DB', 'icon': 'project-diagram'},
        ]
        
        all_sections = []
        parent_sections = []
        
        # Create parent sections
        for i, item in enumerate(main_sections_data):
            section, created = Section.objects.get_or_create(
                user=user,
                title=item['title'],
                defaults={
                    'description': item['description'],
                    'color': item['color'],
                    'icon': item['icon'],
                    'order': i
                }
            )
            parent_sections.append(section)
            all_sections.append(section)
            
            if created:
                self.stdout.write(f'  Created section: {item["title"]}')
        
        # Sub-sections
        sub_sections_data = {
            'Mathematics': ['Algebra', 'Calculus', 'Statistics', 'Geometry'],
            'Physics': ['Mechanics', 'Electromagnetism', 'Thermodynamics', 'Quantum Physics'],
            'Computer Science': ['Algorithms', 'Data Structures', 'Programming Languages', 'Machine Learning'],
            'Languages': ['English', 'Spanish', 'French', 'Japanese'],
            'Personal Projects': ['Website', 'Mobile App', 'Game Development', 'Data Analysis']
        }
        
        # Create sub-sections
        for parent in parent_sections:
            if parent.title in sub_sections_data:
                sub_titles = sub_sections_data[parent.title]
                for j, sub_title in enumerate(sub_titles):
                    sub_section, created = Section.objects.get_or_create(
                        user=user,
                        title=sub_title,
                        parent=parent,
                        defaults={
                            'description': f'Sub-section of {parent.title}',
                            'color': parent.color,
                            'icon': 'folder',
                            'order': j
                        }
                    )
                    all_sections.append(sub_section)
                    
                    if created:
                        self.stdout.write(f'    Created sub-section: {sub_title} (under {parent.title})')
        
        return all_sections
        
    def _create_elements(self, user, sections, tags):
        """Create various elements for each section"""
        all_elements = []
        
        for section in sections:
            # Create flashcards
            flashcards = self._create_flashcards(user, section, tags)
            all_elements.extend(flashcards)
            
            # Create questions
            questions = self._create_questions(user, section, tags)
            all_elements.extend(questions)
            
            # Create multiple choice questions
            mc_questions = self._create_multiple_choice(user, section, tags)
            all_elements.extend(mc_questions)
            
            # Create todos
            todos = self._create_todos(user, section, tags)
            all_elements.extend(todos)
            
            # Create notes
            notes = self._create_notes(user, section, tags)
            all_elements.extend(notes)
            
        return all_elements
            
    def _create_flashcards(self, user, section, tags):
        """Create flashcards for a section"""
        flashcard_data = [
            {
                'title': f'Flashcard 1 - {section.title}',
                'front': 'What is the capital of France?',
                'back': 'Paris',
            },
            {
                'title': f'Flashcard 2 - {section.title}',
                'front': 'What is the formula for water?',
                'back': 'H₂O',
            },
            {
                'title': f'Flashcard 3 - {section.title}',
                'front': 'Who wrote "Romeo and Juliet"?',
                'back': 'William Shakespeare',
            }
        ]
        
        flashcards = []
        for i, data in enumerate(flashcard_data):
            # Pick 1-3 random tags
            selected_tags = random.sample(tags, random.randint(1, min(3, len(tags))))
            
            element, created = Element.objects.get_or_create(
                user=user,
                section=section,
                title=data['title'],
                type=Element.FLASHCARD,
                defaults={
                    'content': data['front'],
                    'additional_content': data['back'],
                    'is_favorite': random.choice([True, False]),
                    'is_completed': random.choice([True, False]),
                    'order': i
                }
            )
            
            if created:
                element.tags.set(selected_tags)
                if element.is_completed:
                    element.completed_at = timezone.now() - datetime.timedelta(days=random.randint(1, 30))
                    element.save()
                self.stdout.write(f'    Created flashcard: {data["title"]}')
            
            flashcards.append(element)
            
        return flashcards

    def _create_questions(self, user, section, tags):
        """Create questions for a section"""
        question_data = [
            {
                'title': f'Question 1 - {section.title}',
                'question': 'Explain the concept of gravity',
                'answer': 'Gravity is a force that attracts objects with mass toward each other. The more mass an object has, the stronger its gravitational pull.',
            },
            {
                'title': f'Question 2 - {section.title}',
                'question': 'What are the main principles of object-oriented programming?',
                'answer': 'Encapsulation, inheritance, polymorphism, and abstraction are the four main principles of object-oriented programming.',
            },
            {
                'title': f'Question 3 - {section.title}',
                'question': 'How does photosynthesis work?',
                'answer': 'Photosynthesis is the process by which plants use sunlight, water, and carbon dioxide to create oxygen and energy in the form of sugar.',
            }
        ]
        
        questions = []
        for i, data in enumerate(question_data):
            # Pick 1-2 random tags
            selected_tags = random.sample(tags, random.randint(1, min(2, len(tags))))
            
            element, created = Element.objects.get_or_create(
                user=user,
                section=section,
                title=data['title'],
                type=Element.QUESTION,
                defaults={
                    'content': data['question'],
                    'additional_content': data['answer'],
                    'is_favorite': random.choice([True, False]),
                    'is_completed': random.choice([True, False]),
                    'order': i + 3  # continuing from flashcards
                }
            )
            
            if created:
                element.tags.set(selected_tags)
                if element.is_completed:
                    element.completed_at = timezone.now() - datetime.timedelta(days=random.randint(1, 30))
                    element.save()
                self.stdout.write(f'    Created question: {data["title"]}')
            
            questions.append(element)
            
        return questions

    def _create_multiple_choice(self, user, section, tags):
        """Create multiple choice questions for a section"""
        mc_data = [
            {
                'title': f'MC Question 1 - {section.title}',
                'content': 'Which planet is closest to the Sun?',
                'choices': ['Venus', 'Mercury', 'Earth', 'Mars'],
                'correct_answer': 'Mercury',
            },
            {
                'title': f'MC Question 2 - {section.title}',
                'content': 'What is the largest mammal?',
                'choices': ['Elephant', 'Giraffe', 'Blue Whale', 'Hippopotamus'],
                'correct_answer': 'Blue Whale',
            },
            {
                'title': f'MC Question 3 - {section.title}',
                'content': 'Which language is not object-oriented?',
                'choices': ['Java', 'Python', 'C', 'C++'],
                'correct_answer': 'C',
            }
        ]
        
        mc_questions = []
        for i, data in enumerate(mc_data):
            # Pick 1-3 random tags
            selected_tags = random.sample(tags, random.randint(1, min(3, len(tags))))
            
            element, created = Element.objects.get_or_create(
                user=user,
                section=section,
                title=data['title'],
                type=Element.MULTIPLE_CHOICE,
                defaults={
                    'content': data['content'],
                    'data': {'choices': data['choices'], 'correct_answer': data['correct_answer']},
                    'is_favorite': random.choice([True, False]),
                    'is_completed': random.choice([True, False]),
                    'order': i + 6  # continuing from questions
                }
            )
            
            if created:
                element.tags.set(selected_tags)
                if element.is_completed:
                    element.completed_at = timezone.now() - datetime.timedelta(days=random.randint(1, 30))
                    element.save()
                self.stdout.write(f'    Created MC question: {data["title"]}')
            
            mc_questions.append(element)
            
        return mc_questions

    def _create_todos(self, user, section, tags):
        """Create todos for a section"""
        todo_data = [
            {
                'title': f'Todo 1 - {section.title}',
                'task': f'Complete assignment for {section.title}',
                'due_date': timezone.now() + datetime.timedelta(days=random.randint(1, 14)),
            },
            {
                'title': f'Todo 2 - {section.title}',
                'task': f'Review notes on {section.title}',
                'due_date': timezone.now() + datetime.timedelta(days=random.randint(1, 7)),
            }
        ]
        
        todos = []
        for i, data in enumerate(todo_data):
            # Pick 1-2 random tags
            selected_tags = random.sample(tags, random.randint(1, min(2, len(tags))))
            
            element, created = Element.objects.get_or_create(
                user=user,
                section=section,
                title=data['title'],
                type=Element.TODO,
                defaults={
                    'content': data['task'],
                    'due_date': data.get('due_date'),
                    'is_completed': random.choice([True, False]),
                    'order': i + 9  # continuing from MC questions
                }
            )
            
            if created:
                element.tags.set(selected_tags)
                if element.is_completed:
                    element.completed_at = timezone.now() - datetime.timedelta(days=random.randint(1, 5))
                    element.save()
                self.stdout.write(f'    Created todo: {data["title"]}')
            
            todos.append(element)
            
        return todos

    def _create_notes(self, user, section, tags):
        """Create notes for a section"""
        note_data = [
            {
                'title': f'Note 1 - {section.title}',
                'content': f'This is an important note about {section.title}. It contains key information that I need to remember for future reference.',
            },
            {
                'title': f'Note 2 - {section.title}',
                'content': f'Key points about {section.title}:\n- Point 1\n- Point 2\n- Point 3\n\nRemember to review these regularly.',
            }
        ]
        
        notes = []
        for i, data in enumerate(note_data):
            # Pick 1-3 random tags
            selected_tags = random.sample(tags, random.randint(1, min(3, len(tags))))
            
            element, created = Element.objects.get_or_create(
                user=user,
                section=section,
                title=data['title'],
                type=Element.NOTE,
                defaults={
                    'content': data['content'],
                    'is_favorite': random.choice([True, False]),
                    'order': i + 11  # continuing from todos
                }
            )
            
            if created:
                element.tags.set(selected_tags)
                self.stdout.write(f'    Created note: {data["title"]}')
            
            notes.append(element)
            
        return notes

    def _create_study_data(self, user, sections, elements):
        """Create study sessions and records"""
        # Create 3-5 study sessions for each user
        num_sessions = random.randint(3, 5)
        
        for i in range(num_sessions):
            # Choose a random section
            section = random.choice(sections)
            
            # Create a study session
            start_time = timezone.now() - datetime.timedelta(days=random.randint(1, 30))
            end_time = start_time + datetime.timedelta(minutes=random.randint(30, 120))
            
            session = StudySession.objects.create(
                user=user,
                section=section,
                started_at=start_time,
                ended_at=end_time,
            )
            
            self.stdout.write(f'  Created study session for {section.title}')
            
            # Create study records for this session
            # Get elements from the same section
            section_elements = [e for e in elements if e.section == section]
            
            if section_elements:
                # Choose 3-10 elements (or fewer if not enough)
                num_records = min(len(section_elements), random.randint(3, 10))
                study_elements = random.sample(section_elements, num_records)
                
                for element in study_elements:
                    # Create study record
                    result = random.choice(['correct', 'incorrect', 'partial', 'skipped'])
                    # Fix: Convert integer seconds to a proper timedelta object
                    time_spent = datetime.timedelta(seconds=random.randint(30, 300))
                    studied_at = start_time + datetime.timedelta(seconds=random.randint(0, int((end_time - start_time).total_seconds())))
                    
                    StudyRecord.objects.create(
                        session=session,
                        element=element,
                        result=result,
                        time_spent=time_spent,
                        studied_at=studied_at,
                        notes=f'Study note for {element.title}' if random.choice([True, False]) else ''
                    )
