import re
from markupsafe import Markup
from typing import Callable, Dict, Any, Optional


class FontAwesomeFixMiddleware:
    """
    WSGI middleware to fix double-encoded Font Awesome icons in CKAN templates.
    
    This middleware intercepts the response and fixes any double-encoded
    Font Awesome icons in the HTML content.
    """
    
    def __init__(self, app: Callable) -> None:
        """
        Initialize the middleware.
        
        Args:
            app: The WSGI application
        """
        self.app = app
        
        # Regular expression to match double-encoded Font Awesome icons
        # This pattern matches strings like:
        # &amp;lt;i class=&amp;quot;fa fa-icon&amp;quot;&amp;gt;&amp;lt;/i&amp;gt;
        self.pattern = re.compile(
            r'&amp;lt;i\s+class=&amp;quot;fa\s+fa-([a-z0-9-]+)&amp;quot;&amp;gt;&amp;lt;/i&amp;gt;'
        )
    
    def __call__(self, environ: Dict[str, Any], start_response: Callable) -> Any:
        """
        Call the middleware.
        
        Args:
            environ: The WSGI environment
            start_response: The WSGI start_response function
            
        Returns:
            The response from the application
        """
        # Create a response interceptor
        def custom_start_response(status, headers, exc_info=None):
            self.status = status
            self.headers = headers
            self.exc_info = exc_info
            return start_response(status, headers, exc_info)
        
        # Get the response from the application
        app_iter = self.app(environ, custom_start_response)
        
        # Check if the response is HTML
        is_html = False
        for name, value in self.headers:
            if name.lower() == 'content-type' and 'text/html' in value.lower():
                is_html = True
                break
        
        # If not HTML, return the response as is
        if not is_html:
            return app_iter
        
        # Collect the response body
        response_body = b''
        for chunk in app_iter:
            if isinstance(chunk, str):
                response_body += chunk.encode('utf-8')
            else:
                response_body += chunk
        
        # Close the app_iter if it has a close method
        if hasattr(app_iter, 'close'):
            app_iter.close()
        
        # Fix double-encoded Font Awesome icons
        response_text = response_body.decode('utf-8')
        
        def replace_icon(match):
            icon_name = match.group(1)
            return f'<i class="fa fa-{icon_name}"></i>'
        
        fixed_response = self.pattern.sub(replace_icon, response_text)
        
        # Return the fixed response
        return [fixed_response.encode('utf-8')]


def make_middleware(app: Callable, config: Optional[Dict[str, Any]] = None) -> Callable:
    """
    Factory function to create the middleware.
    
    Args:
        app: The WSGI application
        config: The configuration dictionary
        
    Returns:
        The middleware
    """
    return FontAwesomeFixMiddleware(app)
