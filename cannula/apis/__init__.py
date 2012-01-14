

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
    
    def _send(self, *args, **kwargs):
        """Send a command to the remote cannula server."""