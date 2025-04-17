from django.shortcuts import render

def page_not_found(request, exception):
    """
    Custom 404 error handling view.
    
    This view is called when a page is not found. It renders the 404.html template
    with a 404 status code.
    
    Args:
        request: The HTTP request object
        exception: The exception that was raised
        
    Returns:
        HttpResponse with 404.html template and 404 status code
    """
    return render(request, '404.html', status=404)
