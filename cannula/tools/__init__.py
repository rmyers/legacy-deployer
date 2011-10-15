from threading import Lock

from cannula.tools.base import BaseTool

class AlreadyRegistered(Exception):
    pass

class RegistryException(Exception):
    pass

class Registry(object):
    
    def __init__(self):
        self.lock = Lock()
        self._registry = {}
        self._tags = {}
    
    def register(self, klass, tags=[]):
        try:
            good_klass = issubclass(klass, BaseTool)
        except:
            good_klass = False
        if not good_klass:
            raise RegistryException('Incorrect Type: %s' % type(klass))
        
        self.lock.acquire()
        if hasattr(klass, 'NAME'):
            name = klass.NAME
        else:
            name = klass.__name__
        
        if self._registry.get(name):
            raise AlreadyRegistered('Class %r already registered' % name)
        self._registry[name] = klass
        
        for tag in tags:
            tagged = self._tags.get(tag, [])
            if klass not in tagged:
                tagged.append(klass)
                tagged.sort()
            self._tags[tag] = tagged
        self.lock.release()
    
    def unregister(self, klass):
        self.lock.acquire()
        if hasattr(klass, 'NAME'):
            name = klass.NAME
        else:
            name = klass.__name__
        
        if self._registry.get(name):
            del self._registry[name]
        self.lock.release()

tool = Registry()
