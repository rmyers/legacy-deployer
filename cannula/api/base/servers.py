
from logging import getLogger

from cannula.api import DuplicateObject
from cannula.api import UnitDoesNotExist
from cannula.api import BaseAPI
from cannula.conf import api


log = getLogger('api')

class ServerAPIBase(BaseAPI):
    
    
    def _get(self, server):
        "Subclasses must define this"
        raise NotImplementedError()
    
    
    def get(self, server):
        try:
            server = self._get(server)
            return server
        except:
            raise UnitDoesNotExist('Server does not exist')
    
    
    def _list(self, user=None):
        "Subclasses must define this"
        raise NotImplementedError()
    
    
    def list(self, user=None):
        if user:
            user = api.users.get(user)
        return self._list(user)
    
    
    def _create(self, server, **kwargs):
        "Subclasses must define this"
        raise NotImplementedError()
    
    
    def create(self, server, ipaddr='127.0.0.1', port=22, 
               platform_class='cannula.platform.POSIX',
               root_path=None, admin_only=False, crediential=None):
        try:
            self.get(server)
            raise DuplicateObject("Server already exists")
        except UnitDoesNotExist:
            server = self._create(server, ipaddr, port, 
               platform_class,root_path, admin_only, crediential)
            log.info("Server created: %s" % server)
            return server