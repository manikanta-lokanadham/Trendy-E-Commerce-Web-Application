from rest_framework.views import exception_handler
from django.shortcuts import redirect

def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF.
    Redirects search requests to products list instead of showing API errors.
    """
    response = exception_handler(exc, context)
    
    # Check if it's a search request
    request = context.get('request')
    if request and (request.path == '/search/' or request.path.startswith('/search/?q=')):
        # For search requests with errors, redirect to products list
        return redirect('products_list')
    
    return response 