from django.core.management.base import BaseCommand
from apps.pages.models import Page, ContentBlock
from apps.pages.views import create_default_profile_page

class Command(BaseCommand):
    help = 'Reset profile page and its content blocks'

    def handle(self, *args, **options):
        # Delete existing profile page
        Page.objects.filter(slug='profil-matana').delete()
        
        # Create new profile page
        page = create_default_profile_page()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully reset profile page "{page.title}"')
        ) 