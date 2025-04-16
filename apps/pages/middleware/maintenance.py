from django.shortcuts import render
from django.core.cache import cache
from django.conf import settings
from django.urls import reverse
from apps.pages.models import MaintenanceMode

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Paths that should always be accessible
        exempt_paths = [
            reverse('admin:index'),
            '/admin/login/',
            '/static/',
            '/media/',
        ]
        
        # Check if current path is exempt
        if any(request.path.startswith(path) for path in exempt_paths):
            return self.get_response(request)

        # Get maintenance status from cache
        maintenance_mode = cache.get('maintenance_mode')
        if not maintenance_mode:
            try:
                mode = MaintenanceMode.objects.first()
                if mode:
                    maintenance_mode = {
                        'is_active': mode.is_active,
                        'message': mode.message,
                        'allowed_ips': [ip.strip() for ip in mode.allowed_ips.split(',') if ip.strip()]
                    }
                    cache.set('maintenance_mode', maintenance_mode)
            except:
                return self.get_response(request)

        if maintenance_mode and maintenance_mode.get('is_active'):
            # Allow admin access
            if request.path.startswith('/admin/'):
                return self.get_response(request)
                
            # Allow staff members
            if request.user.is_staff:
                # Add maintenance mode banner for staff
                response = self.get_response(request)
                if hasattr(response, 'content'):
                    banner = '''
                        <div style="position:fixed;top:0;left:0;right:0;background:#DC2626;color:white;text-align:center;padding:10px;z-index:9999;">
                            Maintenance Mode Active - Only Staff Can View Site
                            <a href="/admin/maintenance/" style="color:white;text-decoration:underline;margin-left:10px;">
                                Disable Maintenance Mode
                            </a>
                        </div>
                    '''
                    response.content = response.content.decode('utf-8').replace('</body>', f'{banner}</body>')
                return response

            # Check allowed IPs
            client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
            # print(client_ip)
            if client_ip in maintenance_mode.get('allowed_ips', []):
                return self.get_response(request)

            context = {
                'maintenance_message': maintenance_mode.get('message'),
                'estimated_duration': maintenance_mode.get('estimated_duration'),
                'contact_email': maintenance_mode.get('contact_email', 'support@matanauniversity.ac.id'),
                'start_time': maintenance_mode.get('start_time'),
            }
            return render(request, 'maintenance.html', context, status=503)

        return self.get_response(request) 