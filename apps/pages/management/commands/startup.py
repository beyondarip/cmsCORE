from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Initialize application with all necessary setup'

    def handle(self, *args, **options):
        try:
            # 1. Run automigrations
            self.stdout.write('Running automigrations...')
            call_command('automigrate')
            
            # 2. Collect static files
            if not settings.DEBUG:
                self.stdout.write('\nCollecting static files...')
                call_command('collectstatic', '--noinput')
            
            # 3. Create necessary directories
            media_root = settings.MEDIA_ROOT
            dirs_to_create = [
                media_root,
                os.path.join(media_root, 'uploads'),
                os.path.join(media_root, 'thumbnails'),
                'logs'
            ]
            
            for dir_path in dirs_to_create:
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                    self.stdout.write(f'Created directory: {dir_path}')
            
            # 4. Generate sample content if in development
            if settings.DEBUG:
                self.stdout.write('\nGenerating sample content...')
                call_command('generate_articles', 5)  # Create 5 sample articles
            
            # 5. Clear cache
            self.stdout.write('\nClearing cache...')
            call_command('clear_cache')
            
            self.stdout.write(self.style.SUCCESS('\nStartup completed successfully!'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\nError during startup: {str(e)}')
            ) 