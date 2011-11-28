
from django.http import Http404
from django.shortcuts import render_to_response
from django.template import RequestContext

from exceptions import ApiError
from exceptions import PermissionError
from exceptions import UnitDoesNotExist
from exceptions import DuplicateObject

class BaseAPI(object):
    
    model = None
    lookup_field = 'name'
    
    def get_object(self, name):
        """Get an object by the default lookup field name. Should be unique."""
        if isinstance(name, self.model):
            return name
        kwargs = {self.lookup_field: name}
        return self.model.objects.get(**kwargs)
    
    def get(self, name):
        try:
            return self.get_object(name)
        except self.model.DoesNotExist:
            raise UnitDoesNotExist
        
    def get_or_404(self, *args, **kwargs):
        try:
            return self.get(*args, **kwargs)
        except UnitDoesNotExist:
            raise Http404
    
    def respond(self, request, templates, context):
        """Wrapper for render_to_response logic."""
        req = RequestContext(request, context)
        return render_to_response(templates, context_instance=req)
    
    def _send(self, *args, **kwargs):
        """Send a command to the remote cannula server."""
        