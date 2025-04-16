from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.apps import apps
import os
import time

class Command(BaseCommand):
    help = 'Automatically detect model changes and apply migrations'

    def handle(self, *args, **options):
        try:
            # 1. Run makemigrations for all apps
            self.stdout.write('Checking for model changes in all apps...')
            call_command('makemigrations')
            
            # 2. Run specific makemigrations for media app
            self.stdout.write('\nChecking for model changes in media app...')
            call_command('makemigrations', 'media')
            
            # 3. Show pending migrations
            self.stdout.write('\nPending migrations:')
            call_command('showmigrations')
            
            # 4. Apply migrations for all apps
            self.stdout.write('\nApplying all migrations...')
            call_command('migrate')
            
            # 5. Apply specific migrations for media app
            self.stdout.write('\nApplying media app migrations...')
            call_command('migrate', 'media')
            
            # 6. Create media directories
            media_paths = [
                'media',
                'media/uploads',
                'media/thumbnails',
                'media/images',
                'media/documents',
                'media/videos',
            ]
            
            for path in media_paths:
                if not os.path.exists(path):
                    os.makedirs(path)
                    self.stdout.write(f'Created directory: {path}')
            
            # 7. Create default superuser if not exists
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            if not User.objects.filter(username='admin').exists():
                self.stdout.write('\nCreating default superuser...')
                User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin'
                )
                self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
            
            # 8. Create default homepage if not exists
            from apps.pages.models import Page
            if not Page.objects.filter(is_homepage=True).exists():
                self.stdout.write('\nCreating default homepage...')
                Page.objects.create(
                    title="Homepage",
                    slug="home",
                    template="home.html",
                    is_homepage=True,
                    status="published"
                )
                self.stdout.write(self.style.SUCCESS('Homepage created successfully'))

            # 9. Initialize media library if needed
            try:
                from apps.media.models import MediaLibrary
                MediaLibrary.objects.get_or_create(
                    name="Default Library",
                    defaults={
                        'description': 'Default media library for the system'
                    }
                )
                self.stdout.write(self.style.SUCCESS('Media library initialized successfully'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Note: Media library initialization skipped: {str(e)}'))

            self.stdout.write(self.style.SUCCESS('\nAll migrations and setup completed successfully!'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\nError during migration process: {str(e)}')
            )
            raise e

    def create_media_folders(self):
        """Create necessary media folders if they don't exist"""
        media_structure = {
            'uploads': ['images', 'documents', 'videos'],
            'thumbnails': ['small', 'medium', 'large'],
            'temp': []
        }
        
        for main_dir, subdirs in media_structure.items():
            main_path = os.path.join('media', main_dir)
            if not os.path.exists(main_path):
                os.makedirs(main_path)
                self.stdout.write(f'Created directory: {main_path}')
            
            for subdir in subdirs:
                sub_path = os.path.join(main_path, subdir)
                if not os.path.exists(sub_path):
                    os.makedirs(sub_path)
                    self.stdout.write(f'Created directory: {sub_path}') 