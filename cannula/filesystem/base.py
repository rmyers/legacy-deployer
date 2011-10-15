from shutil import rmtree
import tempfile
import os
import logging

logger = logging.getLogger('cannula.filesystem')

class FileSystemBase(type):
    """FileSystem base metaclass"""
    
    def __new__(cls, name, bases, attrs):
        super_new = super(FileSystemBase, cls).__new__
        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})
        
        new_class._nodes = {}
        
        # Set up the new class with all the attributes.
        for obj_name, obj in attrs.items():
            if hasattr(obj, 'add_to_class'):
                if obj_name == 'sync':
                    raise AttributeError("The attribute 'sync' is a reserved word, please use another name")
                obj.add_to_class(new_class, obj_name)
            else:
                setattr(new_class, obj_name, obj)

        return new_class

class FileSystem(object):
    """
    File System object, this is what you subclass.
    
    Example::
     
        class Apache(FileSystem):
            root = Directory('/usr/local/apache')
            conf = File(parent='$root', name='httpd.conf')
    
    Usage::
       
        context = {'title': 'example', 'variable': 'foo'}
        with Apache() as apache_files:
            apache_files.sync(context)
            for server in cluster:
                with server.connection as conn:
                    apache_files.sync_remote(conn)
    """
    
    __metaclass__ = FileSystemBase
    
    template_base = 'filesystem/%s'
    template_dir = ''
    
    def __init__(self, deployment=None):
        self.deployment = deployment
        self._tempdir = None
        self._orig_cwd = os.getcwd()
        if self.template_dir:
            self._template_dir = self.template_dir
        else:
            self._template_dir = self.template_base % self.__class__.__name__.lower()
        for node in self._nodes.itervalues():
            node.setup(self, self._template_dir)
    
    def __str__(self):
        return self.__class__.__name__.lower()
    
    def __enter__(self):
        self._tempdir = tempfile.mkdtemp('-fstemp', 'cannula-')
        logger.debug("Created temp directory for %s: %s" % (self, self._tempdir))
        for node in self._nodes.values():
            node._tempdir = self._tempdir
        return self

    def __exit__(self, *args, **kwargs):
        if self._tempdir:
            if os.getcwd() == self._tempdir:
                # some os's don't like you deleting the current directory
                os.chdir(self._orig_cwd)
            rmtree(self._tempdir)
            self._tempdir = None
            self._connection = None
    
    @property
    def deployment_name(self):
        """Convience property for a unique name."""
        if self.deployment:
            group = self.deployment.project.group.abbr
            project = self.deployment.project.abbr
            return "%s.%s" % (group, project)
    
    def sync(self, context):
        for node in self._nodes.itervalues():
            node.create(context) 
    
    def sync_remote(self, connection, *args, **kwargs):
        raise NotImplementedError()