import posixpath
import os, sys
import re
from shutil import rmtree
from itertools import chain

from django.template.loader import render_to_string

# Handle windows paths special
if sys.platform == 'win32':
    SEP = re.compile('^%s' % os.path.sep * 2)
else:
    SEP = re.compile('^%s' % os.path.sep)
WINDOWS_DRIVE = re.compile('^[a-zA-Z]:')


def join(*args):
    """Our version of os.path.join which handles multiple absolute paths
    
    >>> join('/tmp/tempfolder', '/root/files')
    '/tmp/tempfolder/root/files'
    >>> join('/tmp/tempfolder', 'C:/root/files')
    '/tmp/tempfolder/root/files'
    """
    root, _args = args[0], args[1:]
    bits = [root]
    for arg in _args:
        arg = WINDOWS_DRIVE.sub('', arg, count=1)
        arg = SEP.sub('', arg, count=1)
        bits.append(arg)
    return os.path.join(*bits)

def dereference(cls, attr_name, match=True):
    """
    Takes a attribute name in the form ``$attribute`` and 
    returns the attribute that matches on the class 'cls'.
    
    If match is set to True then only return if an attribute is
    found.
    """
    if not isinstance(attr_name, basestring):
        if match:
            return None
        return attr_name
    if not attr_name.startswith('$'):
        if match:
            return None
        return attr_name
    ref = getattr(cls, attr_name.strip('$'))
    return ref

class Node(object):
    """Base Node"""
    
    def __init__(self, parent, name=None, mode='0644', template=None):
        self._parent = parent
        self.name = name
        self.attr_name = None
        self.mode = mode
        self._template = template
        self.template_dir = None
        self._cls = None
        self.parent = None
        self.parent_object = None
        self._tempdir = None

    def __repr__(self):
        return "<Node %s>" % self.path
        
    def __str__(self):
        return self.path 
       
    def add_to_class(self, cls, attr_name):
        """
        This method is called by the constructor to add itself
        to the list of nodes. It also allows us to grab the defaults
        from the attribute name of the parent class.
        """
        if self.name is not None:
            self.attr_name = attr_name
        else:
            self.name = attr_name
            self.attr_name = attr_name
        
        # set template name if needed.
        if not self._template:
            self._template = self.name
        
        cls._nodes[self.attr_name] = self
        setattr(cls, self.attr_name, self)
        
    def setup(self, parent_object, template_dir):
        self.parent_object = parent_object
        parent = dereference(self.parent_object, self._parent)
        if parent:
            if not isinstance(parent, Directory):
                raise AttributeError("Parent node must be a Directory")
            parent.add(self)
            self.parent = parent
        self.template_dir = template_dir
        
    @property
    def path(self):
        name = dereference(self.parent_object, self.name, match=False)
        if callable(name):
            name = name()
        if not self.parent:
            return os.path.join(self._parent, name)
        else:
            return os.path.join(self.parent.path, name)
    
    @property
    def local_path(self):
        if self._tempdir:
            return join(self._tempdir, self.path)
    
    def create(self, *args, **kwargs):
        raise NotImplementedError()
    
        
class Directory(Node):
    """Directory node.
    
    Subclasses should define the following properties.
    
    * parent: Parent directory can be a file system path eg. ('/tmp')
              otherwise it should be the attribute name of the parent.
    * name: name of the directory (default is name of attribute)
    * mode: permission mode of the directory 
    """
    
    def __init__(self, parent, name=None, mode='0755'):
        self._files = {}
        self._directories = {}
        super(Directory, self).__init__(parent, name, mode)
    
    def __iter__(self):
        """Iterates through all nodes under this Directory."""
        return chain(self.directories.itervalues(), self.files.itervalues())
    
    def add(self, obj):
        """Add a File or Directory object to this directories hierarchy."""
        if isinstance(obj, Directory):
            self._directories[obj.attr_name] = obj
        elif isinstance(obj, File):
            self._files[obj.attr_name] = obj
        else:
            raise TypeError("Expecting a File or Directory object")
    
    def create(self, context={}):
        """Create this directory in the temporary location
        
        * context is ignored when creating directories.
        """
        if self.parent:
            self.parent.create()
        if not self._tempdir:
            raise Exception("No temporary directory! Must be used in 'with' statement")
        if not os.path.isdir(self.path):
            os.makedirs(self.path)
    
    def destroy(self):
        """Destroy local temporary directory and contents."""
        if os.path.isdir(self.local_path):
            rmtree(self.local_path)

class File(Node):
    """File node.
    
    Subclasses should define the following properties.
    
    * parent: Parent directory, it should be the attribute name of the parent.
    * name: name of the file (default is name of attribute)
    * mode: permission mode of the directory 
    """
    
    @property
    def template(self):
        temp = dereference(self.parent_object, self._template, match=False)
        if callable(temp):
            temp = temp()
        # Django templates should always be referenced in 'unix' style paths.
        return posixpath.join(self.template_dir, temp)
    
    def content(self, context):
        return render_to_string(self.template, context)
        
    def create(self, context):
        """Create this file in the local temporary directory.
        
        * context should be a dictionary for the Django template.
        """
        # create the parent directory first
        self.parent.create()
        if not self._tempdir:
            raise Exception("No temporary directory! Must be used in 'with' statement")
        with open(self.path, 'wb') as fh:
            fh.write(self.content(context)) 
    
    def destroy(self):
        """Destroy local temporary file."""
        if os.path.isfile(self.path):
            os.unlink(self.path)