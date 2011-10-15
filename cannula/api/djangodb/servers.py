
from logging import getLogger

from django.db.models.loading import get_model

from cannula.api.base.servers import ServerAPIBase

Server = get_model('cannula', 'server')

log = getLogger('api')

class ServerAPI(ServerAPIBase):
    
    
    def _get(self, server):
        if isinstance(server, Server):
            return server
        return Server.objects.get(name=server)
    
    
    def _list(self, user=None):
        return Server.objects.filter(active=True)
 
    
    def _create(self, server, **kwargs):
        server = Server.objects.create(name=server, **kwargs)
        return server