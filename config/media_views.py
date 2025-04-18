from django.http import FileResponse, HttpResponseForbidden, JsonResponse
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
import os
import mimetypes
import json
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
import datetime
from django.utils.decorators import method_decorator
import re
import logging
import unicodedata
import uuid

# Configuration from settings instead of hardcoding
REMOVE_FILE_EXTENSIONS = getattr(settings, 'REMOVE_FILE_EXTENSIONS', True)

# Import Python's magic module if available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

class ProtectedMediaView(APIView):
    """
    Class-based API view for serving protected media files.
    Supports both session and token authentication.
    Handles HTTP Range Requests for streaming video with adjustable position.
    
    This replaces the previous function-based view to provide more consistent
    authentication support, especially for API clients.
    
    Authentication methods:
    1. Standard DRF authentication (token in header, session)
    2. Token in query parameter: ?auth_token=<token>
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    
    def get_user_from_token(self, token_key):
        """
        Get user from token key.
        
        Args:
            token_key: The token key string
            
        Returns:
            User instance or None if token is invalid
        """
        try:
            token = Token.objects.get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return None
    
    def initial(self, request, *args, **kwargs):
        """
        Perform authentication using query param if needed before regular authentication.
        """
        # Check for auth_token in query parameters
        auth_token = request.query_params.get('auth_token')
        
        # If auth_token provided and user is not already authenticated
        if auth_token and (not request.user or not request.user.is_authenticated):
            user = self.get_user_from_token(auth_token)
            if user:
                # Manually set authenticated user
                request.user = user
                return
        
        # Fall back to regular authentication
        super().initial(request, *args, **kwargs)
    
    def get(self, request, path, format=None):
        """
        Serves the requested media file with authentication checks.
        Supports HTTP Range Requests for streaming.
        
        Args:
            request: HTTP request
            path: Path to the file in MEDIA_ROOT
            
        Returns:
            FileResponse if authenticated, with range request support
            Response with error details if not authenticated or file not found
        """
        # Path file lengkap
        file_path = os.path.join(settings.MEDIA_ROOT, path)
        
        # Log file access attempt
        logger = logging.getLogger('apps')
        logger.info(f"Media access attempt: {path} by user {request.user}")
        
        # Cek apakah file ada
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            if 'application/json' in request.META.get('HTTP_ACCEPT', ''):
                return Response({
                    'error': 'Not Found', 
                    'message': 'File tidak ditemukan.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Kembalikan halaman 404
            return render(request, '404.html', status=404)
        
        # Dapatkan ukuran file
        file_size = os.path.getsize(file_path)
        
        # Log file size for debugging
        logger.info(f"Serving file: {path}, size: {file_size} bytes")
        
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
        
        # Check if this is a video file for special handling
        is_video = content_type and content_type.startswith('video/')
        
        # Cek apakah ada header Range untuk permintaan sebagian file
        range_header = request.META.get('HTTP_RANGE', '').strip()
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        
        if range_match:
            # Log range request
            logger.info(f"Range request received: {range_header}")
            
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
            # Log full content request
            logger.info(f"Full content request for: {path}")
            
            # Check file size for chunked response
            if file_size > 10 * 1024 * 1024 and is_video:  # > 10MB and is video
                # For large video files, it's better to encourage range requests
                response = FileResponse(open(file_path, 'rb'), content_type=content_type)
                response['Content-Length'] = str(file_size)
                response['Accept-Ranges'] = 'bytes'
                logger.info("Serving large video with Accept-Ranges header")
            else:
                # Ini permintaan konten lengkap untuk file kecil
                response = FileResponse(open(file_path, 'rb'), content_type=content_type)
                response['Content-Length'] = str(file_size)
                response['Accept-Ranges'] = 'bytes'
        
        # Add CORS headers to support cross-origin video playback
        if getattr(settings, 'MEDIA_CORS_ALLOW_ALL', False):
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        # Set different Content-Disposition based on file type and settings
        if is_video and getattr(settings, 'MEDIA_FORCE_DOWNLOAD_VIDEOS', False):
            # For videos, attachment often works better in problematic environments
            # Note the "attachment" instead of "inline" - this can help with certain browser/server combinations
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            logger.info(f"Set Content-Disposition: attachment for video file")
        else:
            # For non-video files, use inline to display in browser
            response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
        
        # Set Cache-Control for better performance
        response['Cache-Control'] = 'max-age=86400, public'  # 1 day cache
        
        return response

# Legacy function for backward compatibility - redirects to the class-based view
def protected_serve(request, path):
    """
    Legacy function that delegates to ProtectedMediaView class.
    Kept for backward compatibility.
    """
    view = ProtectedMediaView.as_view()
    return view(request, path=path)

@method_decorator(csrf_exempt, name='dispatch')
class FileDeleteView(APIView):
    """
    API view for deleting uploaded files.
    Only authenticated users can delete files.
    Accepts JSON requests with 'filename' parameter.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    
    def delete(self, request, format=None):
        """
        Delete a specific file specified in the JSON body
        """
        # Get filename from request data
        try:
            data = request.data
            filename = data.get('filename')
            
            if not filename:
                return Response(
                    {'error': 'Filename is required in request body'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Validate filename to prevent directory traversal
            if '..' in filename or filename.startswith('/'):
                return Response(
                    {'error': 'Invalid filename'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Construct file path
            file_path = os.path.join(settings.MEDIA_ROOT, filename)
            
            # Check if file exists
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                return Response(
                    {'error': 'File not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Delete the file
            os.remove(file_path)
            return Response(
                {'message': f'File {filename} deleted successfully'}, 
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {'error': f'Failed to delete file: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
        logger = logging.getLogger('apps')  # Use the configured logger
        
        try:
            file_obj = request.FILES.get('file')
            
            if not file_obj:
                return Response({'error': 'No file found'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Log file information for debugging
            logger.info(f"Uploading file: {file_obj.name}, Size: {file_obj.size} bytes, Content-Type: {file_obj.content_type}")
            
            # Get the original file name
            original_filename = file_obj.name
            
            # Stronger filename sanitization to remove ALL non-ASCII characters
            # This is more aggressive but prevents encoding issues
            
            # First normalize unicode characters where possible
            normalized = unicodedata.normalize('NFKD', original_filename)
            # Strip accents and convert to ASCII, ignoring errors
            ascii_name = normalized.encode('ascii', 'ignore').decode('ascii')
            # Replace any remaining problematic characters with underscores
            sanitized_name = re.sub(r'[^a-zA-Z0-9._-]', '_', ascii_name)
            
            # If empty after sanitization (e.g., all characters were non-ASCII)
            # generate a default name based on content type
            if not sanitized_name or sanitized_name == '_':
                content_type = file_obj.content_type or 'application/octet-stream'
                if content_type.startswith('image/'):
                    sanitized_name = 'image'
                elif content_type.startswith('video/'):
                    sanitized_name = 'video'
                elif content_type.startswith('audio/'):
                    sanitized_name = 'audio'
                else:
                    sanitized_name = 'file'
            
            logger.info(f"Sanitized name: {sanitized_name}")
            
            # If configured to remove extensions, strip the extension
            if REMOVE_FILE_EXTENSIONS:
                # Split the filename into base and extension
                base_name, ext = os.path.splitext(sanitized_name)
                # Use just the base name without extension
                save_filename = base_name
                # Keep original extension for content type detection
                content_type, _ = mimetypes.guess_type(original_filename)
            else:
                # Use the sanitized filename with extension
                save_filename = sanitized_name
                content_type = file_obj.content_type or None
            
            # Create a unique filename using timestamp and random component
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            unique_id = str(uuid.uuid4())[:8]  # Use part of a UUID for uniqueness
            unique_filename = f"{save_filename}_{timestamp}_{unique_id}"
            
            # Ensure the filename doesn't exceed filesystem limits (typically 255 chars)
            if len(unique_filename) > 200:  # Being more conservative
                unique_filename = unique_filename[:200]
            
            # Log the processed filename
            logger.info(f"Final filename: {unique_filename}")
            
            # Path file lengkap - ensure it's properly encoded for filesystem
            file_path = os.path.join(settings.MEDIA_ROOT, unique_filename)
            
            # Pastikan direktori ada
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            
            # Try to determine if we need special handling for video files
            is_video = False
            if hasattr(file_obj, 'content_type') and file_obj.content_type and file_obj.content_type.startswith('video/'):
                is_video = True
                logger.info(f"Handling video file: {file_obj.content_type}")
            
            # Tulis file with chunking to handle large files better
            try:
                # Use binary mode and handle filesystem encoding properly
                with open(file_path, 'wb') as destination:
                    for chunk in file_obj.chunks(chunk_size=1024 * 1024):  # 1MB chunks
                        destination.write(chunk)
                        
                logger.info(f"File successfully written to {file_path}")
            except Exception as e:
                logger.error(f"Error writing file: {str(e)}")
                raise
            
            # Return URL with the new filename - Using Django's settings instead of hardcoding
            media_url = settings.MEDIA_URL.rstrip('/')
            file_url = f"{request.scheme}://{request.get_host()}{media_url}/{unique_filename}"
            
            # Ensure the file exists before returning success
            if not os.path.exists(file_path):
                logger.error(f"File was not successfully saved: {file_path}")
                return Response({
                    'error': 'Failed to save file'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'message': 'File uploaded successfully',
                'file_name': unique_filename,
                'original_name': original_filename,
                'url': file_url,
                'size': file_obj.size,
                'content_type': content_type or 'application/octet-stream'
            }, status=status.HTTP_201_CREATED)
            
        except UnicodeEncodeError as ue:
            # Specific handling for Unicode errors
            logger.error(f"Unicode encoding error: {str(ue)}", exc_info=True)
            return Response({
                'error': 'File name contains unsupported characters',
                'detail': 'Please rename your file using only English letters, numbers, and basic symbols'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            # Log the detailed error
            logger.error(f"File upload error: {str(e)}", exc_info=True)
            
            # Return a generic error message to the client
            return Response({
                'error': 'Server error during file upload',
                'detail': str(e) if settings.DEBUG else 'Contact administrator for details'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
                
                # Get URL using Django's settings
                media_url = settings.MEDIA_URL.rstrip('/')
                file_url = f"{request.scheme}://{request.get_host()}{media_url}/{rel_path}"
                print(file_url)
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