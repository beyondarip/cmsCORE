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
import urllib.parse

# Configuration from settings instead of hardcoding
REMOVE_FILE_EXTENSIONS = getattr(settings, 'REMOVE_FILE_EXTENSIONS', True)

# Import Python's magic module if available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

def is_video_file(path):
    """Helper function to check if a file is a video based on extension"""
    video_extensions = ('.mp4', '.webm', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.m4v', '.3gp', '.ogg')
    return path.lower().endswith(video_extensions)


def is_media_file(path):
    """Helper function to check if a file is media (video or audio)"""
    audio_extensions = ('.mp3', '.wav', '.ogg', '.m4a', '.aac')
    return is_video_file(path) or path.lower().endswith(audio_extensions)

def protected_serve(request, path):
    """
    Function-based view for serving protected media files.
    
    Key features:
    - ALL files (including media) require authentication (session or token)
    - Uses Django's native static serving for media files to ensure full playback
    - Uses regular serve for other files
    
    This ensures that videos/audio files play completely without interruption
    while still requiring authentication for all file types.
    
    Args:
        request: HTTP request
        path: Path to the file in MEDIA_ROOT
        
    Returns:
        Django's static.serve response for authenticated users
        403 Forbidden if not authenticated
    """
    logger = logging.getLogger('apps')
    logger.info(f"Media request: {path}")
    
    # URL-decode the path to handle spaces and special characters
    path = urllib.parse.unquote(path)
    logger.info(f"Decoded path: {path}")
    
    # Check if user is authenticated via session
    authenticated = request.user.is_authenticated
    
    # If not, check for token authentication
    if not authenticated:
        auth_token = request.GET.get('auth_token')
        if auth_token:
            try:
                token = Token.objects.get(key=auth_token)
                # Token is valid, consider the user authenticated
                authenticated = True
                logger.info(f"Token auth successful for: {path}")
            except Token.DoesNotExist:
                authenticated = False
                logger.warning(f"Invalid token attempt for: {path}")
    
    # Require authentication for ALL files
    if not authenticated:
        logger.warning(f"Unauthorized access attempt for: {path}")
        # Return 403 or redirect to login
        if 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            return JsonResponse({
                'error': 'Unauthorized', 
                'message': 'Anda harus login untuk mengakses file ini.'
            }, status=403)
        return render(request, '404.html', status=404)
    
    # Check if this is a media file (video/audio)
    is_media = is_media_file(path)
    
    # File path for checking existence
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    
    # Check if file exists
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        logger.warning(f"File not found: {file_path}")
        if 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            return JsonResponse({
                'error': 'Not Found', 
                'message': 'File tidak ditemukan.'
            }, status=404)
        return render(request, '404.html', status=404)
    
    # For media files (video/audio): Use Django's static approach for full playback
    if is_media:
        logger.info(f"Serving media file using FileResponse: {path}")
        
        # Open the file in binary mode
        file_handle = open(file_path, 'rb')
        
        # Get the content type based on file extension
        content_type, encoding = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'
        
        # Create FileResponse that handles range requests
        response = FileResponse(file_handle, content_type=content_type)
        
        # Set the filename and content-disposition
        filename = os.path.basename(file_path)
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        
        # Add cache headers suitable for media files
        response['Cache-Control'] = 'public, max-age=43200'  # 12 hours for media
        
        # Get file size for Content-Length header
        response['Content-Length'] = os.path.getsize(file_path)
        
        # Support for range requests (important for video playback)
        response['Accept-Ranges'] = 'bytes'
        
        return response
    
    # For authenticated users accessing non-media files, use FileResponse
    try:
        logger.info(f"Serving protected non-media file: {path}")
        
        # Open the file in binary mode
        file_handle = open(file_path, 'rb')
        
        # Get the content type based on file extension
        content_type, encoding = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'
            
        # Create FileResponse
        response = FileResponse(file_handle, content_type=content_type)
        
        # Set the filename and content disposition
        filename = os.path.basename(file_path)
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        
        # Add cache headers
        response['Cache-Control'] = 'public, max-age=3600'  # 1 hour for non-media files
        
        # Set Content-Length header
        response['Content-Length'] = os.path.getsize(file_path)
        
        return response
        
    except Exception as e:
        logger.error(f"Error serving file {path}: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'Error serving file',
            'detail': str(e) if settings.DEBUG else 'Contact administrator for details'
        }, status=500)


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
            
            # First try to transliterate non-ASCII characters to ASCII equivalents
            # This helps with accented characters (é->e, ñ->n, etc.)
            normalized = unicodedata.normalize('NFKD', original_filename)
            transliterated = ''
            for char in normalized:
                # If character can be encoded as ASCII, use it
                try:
                    char.encode('ascii')
                    transliterated += char
                except UnicodeEncodeError:
                    # For non-ASCII that couldn't be transliterated, use a placeholder
                    # This preserves the character position and gives some indication of the original
                    if ord(char) >= 0x3040 and ord(char) <= 0x30FF:  # Hiragana/Katakana range
                        transliterated += 'j'  # Japanese character
                    elif ord(char) >= 0xAC00 and ord(char) <= 0xD7A3:  # Hangul syllables
                        transliterated += 'k'  # Korean character
                    elif ord(char) >= 0x4E00 and ord(char) <= 0x9FFF:  # CJK Unified Ideographs
                        transliterated += 'c'  # Chinese character
                    elif ord(char) >= 0x0600 and ord(char) <= 0x06FF:  # Arabic
                        transliterated += 'a'  # Arabic character
                    elif ord(char) >= 0x0900 and ord(char) <= 0x097F:  # Devanagari
                        transliterated += 'd'  # Devanagari character
                    elif ord(char) >= 0x0400 and ord(char) <= 0x04FF:  # Cyrillic
                        transliterated += 'r'  # Russian/Cyrillic character
                    else:
                        transliterated += 'x'  # Other non-ASCII character
            
            # Now remove characters that are invalid for Linux filesystems
            invalid_chars = r'[/\x00\\\*\?\[\]\(\)\;\&\|\<\>\$\`\'\":=]'
            sanitized_name = re.sub(invalid_chars, '_', transliterated)
            
            # Replace consecutive underscores with a single one
            sanitized_name = re.sub(r'_+', '_', sanitized_name)
            
            # Preserve spaces but remove leading/trailing whitespace and periods
            sanitized_name = sanitized_name.strip(' .')
            
            # If empty after sanitization, generate a default name
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
            
            logger.info(f"Original filename: {original_filename}")
            logger.info(f"Sanitized name: {sanitized_name}")
            
            # Check if query parameter overrides default behavior
            # 'keep_extension=true' means don't remove the extension (override REMOVE_FILE_EXTENSIONS=True)
            # 'keep_extension=false' means remove the extension (override REMOVE_FILE_EXTENSIONS=False)
            keep_extension_param = request.query_params.get('keep_extension', None)
            
            # Determine whether to remove extensions based on parameter or default setting
            remove_extensions = REMOVE_FILE_EXTENSIONS  # Default from settings
            
            if keep_extension_param is not None:
                # Override based on query parameter
                keep_extension = keep_extension_param.lower() in ('true', 't', 'yes', 'y', '1')
                remove_extensions = not keep_extension
                logger.info(f"Extension removal overridden by query parameter: remove_extensions={remove_extensions}")
            
            # If configured to remove extensions, strip the extension
            if remove_extensions:
                # Split the filename into base and extension
                base_name, ext = os.path.splitext(sanitized_name)
                # Use just the base name without extension
                unique_filename = base_name
                # Keep original extension for content type detection
                content_type, _ = mimetypes.guess_type(original_filename)
            else:
                # Use the sanitized filename directly
                unique_filename = sanitized_name
                content_type = file_obj.content_type or None
            
            # Handle filename conflicts by adding a number suffix if file already exists
            file_path = os.path.join(settings.MEDIA_ROOT, unique_filename)
            counter = 1
            
            # If file already exists, add a numeric suffix to avoid overwriting
            name_base, ext = os.path.splitext(unique_filename)
            while os.path.exists(file_path):
                unique_filename = f"{name_base}_{counter}{ext}"
                file_path = os.path.join(settings.MEDIA_ROOT, unique_filename)
                counter += 1
                
            # Ensure the filename doesn't exceed filesystem limits (typically 255 chars)
            if len(unique_filename) > 200:  # Being more conservative
                unique_filename = unique_filename[:200]
            
            # Log the processed filename
            logger.info(f"Final filename: {unique_filename}")
            
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
            
            # Get the base URL and server prefix for full URL construction
            base_url = f"{request.scheme}://{request.get_host()}"
            server_prefix = getattr(settings, 'SERVER_PREFIX', '')  # Get from settings with fallback
            media_url = settings.MEDIA_URL.rstrip('/')
            
            # URL encode the filename to handle spaces and special characters
            encoded_filename = urllib.parse.quote(unique_filename)
            
            # Construct the complete URL with all required path components
            file_url = f"{base_url}{server_prefix}{media_url}/{encoded_filename}"
            logger.info(f"Generated file URL: {file_url}")
            
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
        logger = logging.getLogger('apps')
        
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
                
                # Get the correct complete URL with full path
                base_url = f"{request.scheme}://{request.get_host()}"
                
                # Add the full path including server/2/fjoejoj prefix
                # This ensures the complete path is included in the URL
                server_prefix = getattr(settings, 'SERVER_PREFIX', '')  # Get from settings with fallback
                media_url = settings.MEDIA_URL.rstrip('/')
                
                # URL encode the path to handle spaces and special characters
                encoded_path = urllib.parse.quote(rel_path)
                
                # Construct the full URL with all path components
                file_url = f"{base_url}{server_prefix}{media_url}/{encoded_path}"
                
                logger.info(f"Generated file URL: {file_url}")
                
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