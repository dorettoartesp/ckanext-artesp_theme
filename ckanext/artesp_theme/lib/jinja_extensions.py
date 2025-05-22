import re
from jinja2 import nodes
from jinja2.ext import Extension
from markupsafe import Markup


class FontAwesomeIconExtension(Extension):
    """
    Jinja2 extension to fix double-encoded Font Awesome icons.
    
    This extension provides a {% fa_icon %} tag that renders a Font Awesome icon
    that won't be double-encoded.
    
    Example usage:
        {% fa_icon "plus-square" %} Add Dataset
    """
    
    tags = {'fa_icon'}
    
    def __init__(self, environment):
        super(FontAwesomeIconExtension, self).__init__(environment)
        
        # Add the extension to the environment
        environment.extend(
            fa_icon=self._fa_icon,
        )
    
    def _fa_icon(self, icon_name):
        """
        Create a Font Awesome icon that won't be double-encoded.
        
        Args:
            icon_name: The name of the Font Awesome icon (without the 'fa-' prefix)
            
        Returns:
            A Markup object containing the Font Awesome icon HTML
        """
        return Markup(f'<i class="fa fa-{icon_name}"></i> ')
    
    def parse(self, parser):
        """
        Parse the {% fa_icon %} tag.
        
        Args:
            parser: The Jinja2 parser
            
        Returns:
            A node that renders a Font Awesome icon
        """
        lineno = next(parser.stream).lineno
        
        # Get the icon name
        args = [parser.parse_expression()]
        
        # Return a node that calls the _fa_icon method
        return nodes.CallBlock(
            self.call_method('_render_fa_icon', args),
            [], [], []
        ).set_lineno(lineno)
    
    def _render_fa_icon(self, icon_name, caller):
        """
        Render a Font Awesome icon.
        
        Args:
            icon_name: The name of the Font Awesome icon (without the 'fa-' prefix)
            caller: The caller
            
        Returns:
            A Markup object containing the Font Awesome icon HTML
        """
        return self._fa_icon(icon_name)
