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


def protected_serve(request, path):
    """
    View untuk melayani file media dengan proteksi login.
    Hanya user yang sudah login yang bisa mengakses file media.
    
    Args:
        request: HTTP request
        path: Path file di dalam MEDIA_ROOT
    
    Returns:
        FileResponse jika user sudah login
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
    
    # Dapatkan mimetype
    content_type, encoding = mimetypes.guess_type(file_path)
    if content_type is None:
        content_type = 'application/octet-stream'
    
    # Return file response
    response = FileResponse(open(file_path, 'rb'), content_type=content_type)
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