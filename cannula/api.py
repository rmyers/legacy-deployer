
from cannula.utils import import_object
from cannula.conf import CANNULA_API

class LazyAPI(object):
    
    def __init__(self, dotted_path):
        self._dotted_path = dotted_path
        self._api = None
    
    def __getattr__(self, attr):
        if not self._api:
            klass = import_object(self._dotted_path)
            self._api = klass()
        return getattr(self._api, attr)
    
class API:
    
    #clusters = LazyAPI(CANNULA_API['clusters'])
    deploy = LazyAPI(CANNULA_API['deploy'])
    groups = LazyAPI(CANNULA_API['groups'])
    keys = LazyAPI(CANNULA_API['keys'])
    log = LazyAPI(CANNULA_API['log'])
    permissions = LazyAPI(CANNULA_API['permissions'])
    proc = LazyAPI(CANNULA_API['proc'])
    projects = LazyAPI(CANNULA_API['projects'])
    proxy = LazyAPI(CANNULA_API['proxy'])
    #servers = LazyAPI(CANNULA_API['servers'])
    users = LazyAPI(CANNULA_API['users'])
    #unix_ids = LazyAPI(CANNULA_API['unix_ids'])

api = API()