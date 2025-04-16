from django.core.management.base import BaseCommand
from axes.models import AccessAttempt
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Deletes all access attempts and effectively unbans all IPs'

    def handle(self, *args, **options):
        try:
            count = AccessAttempt.objects.count()
            AccessAttempt.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {count} access attempts. All IPs are now unbanned.')
            )
            logger.info(f'Unbanned {count} IPs via management command')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error unbanning IPs: {str(e)}')
            )
            logger.error(f'Failed to unban IPs: {str(e)}', exc_info=True) 