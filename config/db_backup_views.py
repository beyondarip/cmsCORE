import os
import datetime
import shutil
import logging
import glob
from django.http import FileResponse, HttpResponseForbidden, JsonResponse, HttpResponse
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from django.shortcuts import redirect

logger = logging.getLogger(__name__)

# @login_required
def backup_database(request):
    """
    View untuk backup database SQLite dan menyimpannya di MEDIA_ROOT.
    
    Args:
        request: HTTP request
    
    Returns:
        JsonResponse dengan info file yang di-backup
    """
    # Jika ini HEAD request, hanya kembalikan response OK
    if request.method == "HEAD":
        return HttpResponse(status=200)
    
    try:
        # Path ke file database
        db_path = settings.DATABASES['default']['NAME']
        logger.info(f"Attempting to backup database at {db_path}")
        
        # Pastikan ini adalah database SQLite
        if not os.path.exists(db_path):
            logger.error(f"Database file not found at {db_path}")
            return HttpResponseForbidden("Database tidak ditemukan.")
        
        # Buat nama file yang akan dibackup
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backup_db_{timestamp}.sqlite3"
        
        # Path tujuan di MEDIA_ROOT
        media_path = os.path.join(settings.MEDIA_ROOT, filename)
        
        # Pastikan direktori MEDIA_ROOT ada
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        
        # Copy database ke MEDIA_ROOT
        shutil.copy2(db_path, media_path)
        logger.info(f"Database backup created at {media_path}")
        
        # URL untuk mengakses file (full URL dengan scheme dan host)
        media_url = settings.MEDIA_URL.rstrip('/')
        server_prefix = getattr(settings, 'SERVER_PREFIX', '')
        file_url = f"{request.scheme}://{request.get_host()}{server_prefix}{media_url}/{filename}"
        
        # Kembalikan data sebagai JSON daripada redirect
        return JsonResponse({
            'success': True,
            'filename': filename,
            'file_url': file_url,
            'timestamp': timestamp,
            'full_path': media_path
        })
        
    except Exception as e:
        logger.error(f"Error during database backup: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def list_database_backups(request):
    """
    View untuk mendapatkan daftar backup database yang tersedia.
    
    Args:
        request: HTTP request
        
    Returns:
        JsonResponse dengan daftar file backup
    """
    try:
        # Path pattern untuk file backup
        backup_pattern = os.path.join(settings.MEDIA_ROOT, 'backup_db_*.sqlite3')
        
        # Dapatkan semua file yang cocok dengan pattern
        backup_files = glob.glob(backup_pattern)
        
        # Urutkan berdasarkan waktu modifikasi (terbaru dulu)
        backup_files.sort(key=os.path.getmtime, reverse=True)
        
        # Siapkan data untuk respons
        backups = []
        for file_path in backup_files:
            filename = os.path.basename(file_path)
            # URL lengkap dengan scheme dan host
            media_url = settings.MEDIA_URL.rstrip('/')
            server_prefix = getattr(settings, 'SERVER_PREFIX', '')
            file_url = f"{request.scheme}://{request.get_host()}{server_prefix}{media_url}/{filename}"
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
            
            backups.append({
                'filename': filename,
                'file_url': file_url,
                'file_size': round(file_size, 2),
                'created_at': datetime.datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return JsonResponse({
            'success': True,
            'backups': backups
        })
        
    except Exception as e:
        logger.error(f"Error listing database backups: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500) 