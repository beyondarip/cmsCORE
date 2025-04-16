from django.apps import AppConfig


class MembersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.members'  # This should match your app's full Python path
    verbose_name = 'Members Management'