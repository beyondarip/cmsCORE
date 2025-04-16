import os
import logging
from PIL import Image
from django.conf import settings
from django.template import Library
from django.core.files.storage import default_storage
from pathlib import Path

register = Library()
print(__name__)

# Constants
WEBP_QUALITY = 85
JPEG_QUALITY = 85
MAX_WIDTH = 1920  # Maximum width for large images
THUMBNAIL_SIZES = {
    'small': 300,
    'medium': 800,
    'large': 1200
}

def optimize_image(image_path, max_width=MAX_WIDTH, quality=WEBP_QUALITY, preserve_transparency=True):
    """Optimize image by resizing and compressing while maintaining aspect ratio and transparency by default"""
    try:
        img = Image.open(image_path)
        
        # By default we preserve transparency, only convert to RGB if specifically requested
        if not preserve_transparency and img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background

        # Resize if width exceeds max_width
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        return img
    except Exception as e:
        print(f"Error optimizing image {image_path}: {e}")
        return None

def convert_to_webp(image_path, quality=WEBP_QUALITY):
    """Convert image to WebP format with optimization"""
    webp_path = str(Path(image_path).with_suffix('.webp'))
    
    if os.path.exists(webp_path):
        return webp_path
    
    try:
        img = optimize_image(image_path)
        if img:
            img.save(webp_path, 'WEBP', quality=quality)
            print(f"Successfully converted {image_path} to WebP")
            return webp_path
    except Exception as e:
        print(f"Error converting {image_path} to WebP: {e}")
    
    return image_path

def get_image_path(img_url):
    """Get the full path for both static and media files"""
    if not img_url:
        return None
        
    # Clean the URL path and remove potential double static references
    img_url = img_url.lstrip('/')
    if img_url.startswith('static/'):
        img_url = img_url[7:]  # Remove 'static/' prefix
    # print(img_url)
    
    # Try multiple possible locations
    possible_paths = [
        # Static root path
        os.path.join(settings.STATIC_ROOT, img_url) if settings.STATIC_ROOT else None,
        # Media root path 
        os.path.join(settings.MEDIA_ROOT, img_url) if settings.MEDIA_ROOT else None,
        # Direct static folder path
        os.path.join(settings.BASE_DIR, 'static', img_url) if settings.BASE_DIR else None,
        # App static folder path
        os.path.join(settings.BASE_DIR, 'apps', 'pages', 'static', img_url) if settings.BASE_DIR else None
    ]
    
    # Filter out None values
    possible_paths = [p for p in possible_paths if p is not None]
    
    # Try each possible path
    for path in possible_paths:
        if os.path.exists(path):
            # print(path)
            return path
            
    # If image not found, log and return None
    print(f"Image not found in any location: {img_url}")
    return None

def convert_path_to_url(path):
    """Convert filesystem path to URL"""
    path = str(path)
    if settings.STATIC_ROOT and settings.STATIC_URL:
        path = path.replace(str(settings.STATIC_ROOT), settings.STATIC_URL)
    if settings.MEDIA_ROOT and settings.MEDIA_URL:
        path = path.replace(str(settings.MEDIA_ROOT), settings.MEDIA_URL)
    if settings.BASE_DIR:
        # Handle app static folders
        static_indicator = os.path.join('static', '')
        if static_indicator in path:
            path_parts = path.split(static_indicator)
            if len(path_parts) > 1:
                path = settings.STATIC_URL + path_parts[1]
    
    # Fix double slashes issue
    path = path.replace('\\', '/')
    # Replace any double slashes with single slash (except for http:// or https://)
    while '//' in path and not (path.startswith('http://') or path.startswith('https://')):
        path = path.replace('//', '/')
    
    return path

@register.simple_tag(takes_context=True)
def optimized_image(context, img_url, size=None):
    """
    Template tag to serve optimized images in WebP format with fallback
    Usage: {% optimized_image image_url [size] %}
    tetapi jika sudah ada yang dioptimasi maka tidak perlu dioptimasi lagi
    """
    if not img_url:
        return ''
    # jika sudah ada yang dioptimasi maka tidak perlu dioptimasi lagi
    if img_url.endswith('.webp'):
        return img_url
    

    try:
        request = context['request']
        supports_webp = 'image/webp' in request.META.get('HTTP_ACCEPT', '')
        
        # Handle both static and media URLs
        original_path = get_image_path(img_url)
        # print( "ORIGNINLA PATH = ",original_path)
        if not original_path:
            # If path not found, try to construct URL with static prefix
            if not img_url.startswith(settings.STATIC_URL):
                print("OR  ", f"{settings.STATIC_URL}{img_url.lstrip('/')}")
                return f"{settings.STATIC_URL}{img_url.lstrip('/')}"
            print("THIS OR ",img_url)
            return img_url
        
        # Convert WindowsPath to string if needed
        original_path = str(original_path)
        
        # Apply size constraint if specified
        if size and size in THUMBNAIL_SIZES:
            img = optimize_image(original_path, max_width=THUMBNAIL_SIZES[size])
            if img:
                try:
                    # Create size-specific filename
                    path_obj = Path(original_path)
                    sized_path = str(path_obj.parent / f"{path_obj.stem}_{size}{path_obj.suffix}")
                    img.save(sized_path, quality=JPEG_QUALITY)
                    original_path = sized_path
                except Exception as e:
                    print(f"Error saving sized image {sized_path}: {e}")
                    # Continue with original path if sizing fails
        
        if supports_webp:
            try:
                webp_path = convert_to_webp(original_path)
                if webp_path and webp_path != original_path:
                    return convert_path_to_url(webp_path)
            except Exception as e:
                print(f"Error converting to WebP {original_path}: {e}")
                # Fall back to original URL if WebP conversion fails
        
        # Convert the original path to URL before returning
        return convert_path_to_url(original_path)
        
    except Exception as e:
        print(f"Error processing image {img_url}: {e}")
        return img_url

@register.simple_tag
def get_thumbnail(image_field, size='medium'):
    """
    Template tag for model-based images with thumbnails
    Usage: {% get_thumbnail product.image 'small' %}
    """
    if not image_field:
        return ''
        
    try:
        if hasattr(image_field, 'url'):
            image_url = image_field.url
            return optimized_image({'request': {'META': {'HTTP_ACCEPT': 'image/webp'}}}, 
                                 image_url, 
                                 size)
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return ''
