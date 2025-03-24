import json
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class RequestDebugMiddleware(MiddlewareMixin):
    """
    Middleware to debug search endpoint issues.
    """
    def process_request(self, request):
        """
        Process the request by ensuring search endpoints don't require authentication.
        """
        # Check if this is a search request
        if request.path == '/search/' or request.path.startswith('/search/?'):
            # Fix accepted_renderer issue by setting it if missing
            if not hasattr(request, 'accepted_renderer'):
                request.accepted_renderer = None
            
            logger.debug(f"Search request: {request.path}, Headers: {request.headers}")
        return None

    def process_response(self, request, response):
        """
        Process the response for debugging.
        """
        # Debug search responses
        if request.path == '/search/' or request.path.startswith('/search/?'):
            logger.debug(f"Search response: {response.status_code}")
            
        return response 