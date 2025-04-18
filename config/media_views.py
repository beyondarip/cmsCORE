from django.http import FileResponse, HttpResponseForbidden, JsonResponse
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
import os
import mimetypes
import json
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
import datetime

# Import Python's magic module if available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False


from django.http import FileResponse, HttpResponseForbidden, JsonResponse, HttpResponse
from django.conf import settings
import os
import mimetypes
import re

def protected_serve(request, path):
    """
    View untuk melayani file media dengan proteksi login.
    Mendukung HTTP Range Requests untuk streaming video dengan posisi yang bisa diatur.
    
    Args:
        request: HTTP request
        path: Path file di dalam MEDIA_ROOT
    
    Returns:
        FileResponse jika user sudah login, dengan dukungan range requests
        HttpResponseForbidden jika user belum login
    """
    # Cek apakah user sudah login
    if not request.user.is_authenticated:
        # Jika request minta JSON (API), kembalikan JSON
        if 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            return JsonResponse({
                'error': 'Unauthorized', 
                'message': 'Anda harus login untuk mengakses file ini.'
            }, status=403)
        
        # Jika bukan JSON, kembalikan halaman 404
        return render(request, '404.html', status=404)
    
    # Path file lengkap
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    
    # Cek apakah file ada
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        if 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            return JsonResponse({
                'error': 'Not Found', 
                'message': 'File tidak ditemukan.'
            }, status=404)
        
        # Kembalikan halaman 404
        return render(request, '404.html', status=404)
    
    # Dapatkan ukuran file
    file_size = os.path.getsize(file_path)
    
    # Tentukan content type
    content_type, encoding = mimetypes.guess_type(file_path)
    
    # If content_type is not determined by extension, try using magic module
    if not content_type and MAGIC_AVAILABLE:
        try:
            mime = magic.Magic(mime=True)
            content_type = mime.from_file(file_path)
        except Exception:
            pass
            
    content_type = content_type or 'application/octet-stream'
    
    # Cek apakah ada header Range untuk permintaan sebagian file
    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
    
    if range_match:
        # Ini adalah permintaan range (partial content)
        start = int(range_match.group(1))
        end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
        
        # Pastikan end tidak melebihi ukuran file
        end = min(end, file_size - 1)
        
        # Ukuran konten yang akan dikirim
        content_length = end - start + 1
        
        # Buka file dan posisikan ke start byte
        file_obj = open(file_path, 'rb')
        file_obj.seek(start)
        
        # Buat response
        response = FileResponse(file_obj, content_type=content_type, status=206)
        response['Content-Length'] = str(content_length)
        response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
        response['Accept-Ranges'] = 'bytes'
    else:
        # Ini permintaan konten lengkap
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        response['Content-Length'] = str(file_size)
        response['Accept-Ranges'] = 'bytes'
    
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
    return response

class FileUploadView(APIView):
    """
    API view untuk upload file.
    Hanya user yang sudah login yang bisa mengupload file.
    File langsung disimpan ke MEDIA_ROOT tanpa database.
    """
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    
    def head(self, request, format=None):
        """
        Handle HEAD requests to check authentication status.
        """
        return Response(status=status.HTTP_200_OK)
    
    def post(self, request, format=None):
        file_obj = request.FILES.get('file')
        
        if not file_obj:
            return Response({'error': 'No file found'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Simpan file dengan nama asli
        file_path = os.path.join(settings.MEDIA_ROOT, file_obj.name)
        
        # Pastikan direktori ada
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        
        # Tulis file
        with open(file_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)
        
        # Return URL
        file_url = f"{request.scheme}://{request.get_host()}/fjowejao/{file_obj.name}"
        
        return Response({
            'message': 'File uploaded successfully',
            'file_name': file_obj.name,
            'url': file_url
        }, status=status.HTTP_201_CREATED)


class FileListView(APIView):
    """
    API view untuk mendapatkan daftar semua file yang telah diunggah.
    Hanya user yang sudah login yang bisa mengakses daftar file.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    
    def get(self, request, format=None):
        """
        Return a list of all uploaded files
        """
        files = []
        
        # Pastikan MEDIA_ROOT ada
        if not os.path.exists(settings.MEDIA_ROOT):
            return Response(files, status=status.HTTP_200_OK)
        
        # Iterate through all files in MEDIA_ROOT
        for root, dirs, filenames in os.walk(settings.MEDIA_ROOT):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, settings.MEDIA_ROOT)
                
                # Get file stats
                file_stat = os.stat(file_path)
                size_bytes = file_stat.st_size
                modified_time = datetime.datetime.fromtimestamp(file_stat.st_mtime)
                
                # Use a more compact date format (YYYY-MM-DD)
                modified_date = modified_time.strftime("%Y-%m-%d")
                
                # Determine file type
                content_type, _ = mimetypes.guess_type(file_path)
                
                # If content_type is not determined by extension, try using magic module
                if not content_type and MAGIC_AVAILABLE:
                    try:
                        mime = magic.Magic(mime=True)
                        content_type = mime.from_file(file_path)
                        # print(file_path, "content_type :",content_type)
                    except Exception:
                        pass
                
                content_type = content_type or 'application/octet-stream'
                
                # Extract file type category from content_type
                file_type = "other"
                if content_type:
                    if content_type.startswith('image/'):
                        file_type = "image"
                    elif content_type.startswith('video/'):
                        file_type = "video"
                    elif content_type.startswith('audio/'):
                        file_type = "audio"
                    elif (content_type.startswith('application/pdf') or
                          content_type.startswith('application/msword') or
                          'officedocument' in content_type):
                        file_type = "document"
                
                # Get URL
                file_url = f"{request.scheme}://{request.get_host()}/fjowejao/{rel_path}"
                
                # Add file info to list with more compact representation
                files.append({
                    'name': filename,
                    'path': rel_path,
                    'url': file_url,
                    'size': self._format_file_size(size_bytes),
                    'type': file_type,
                    'content_type': content_type,  # Include actual content type for debugging
                    'modified': modified_date
                })
        
        # Sort files by modified date (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return Response(files, status=status.HTTP_200_OK)
    
    def _format_file_size(self, size_bytes):
        """Format file size in a human-readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB" 