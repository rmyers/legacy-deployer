class PlatformError(Exception):
    """A platform error."""

class CompileError(Exception):
    """A problem compiling a python project."""

class Platform(object):
    """
    Base Platform class.  Subclasses must implement this API.

    Represents a system platform, e.g. Linux, Solaris, or some other related
    operating system.
    """
    
    name = 'Platform'
    version = None

    def execute(self, channel, command, threshold = 1):
        """Executes the specified command over the specified channel."""

        status, content = channel.execute(command)
        if status >= threshold:
            raise PlatformError(status, content)

    def get(self, channel, path):
        """Gets the content of the specified filesystem path."""

        return channel.get(path)

    def put(self, channel, local_path, remote_path, content=None):
        """Puts the specified content into the specified filesystem path."""

        channel.put(local_path, remote_path, content)

    def bootstrap(self, channel, *args, **kwargs):
        """Setup a new host so that it can deploy."""
        raise NotImplementedError
    
    def make_init_script(self, channel, *args, **kwargs):
        """Generate a project startup script for this platform type."""
        raise NotImplementedError