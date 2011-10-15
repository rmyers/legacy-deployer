from __future__ import with_statement

from datetime import datetime
import logging

from cannula.utils import import_object

log = logging.getLogger('cannula')

STATUS_CHOICES = (
    ('active', 'Active'),
    ('inactive', 'Inactive'),
    ('dep', 'Deprecated'),
    ('pend', 'Pending Deprecation'),
    ('pre', 'Pre-release'),
    ('admin', 'Admin only'),
)


class BaseGroup(object):
    """
    Project Group

    Collection of projects that users have access to. Users can belong to multiple
    groups. But usually there is one group per department.

    The project group defines the main url and the username that the code is owned
    by and the wsgi process runs as.
    
    Models should define:
     * name: verbose name
     * abbr: abbreviation
     * desc: description
     * members: list of members and roles
     * date_created
    """

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.abbr)

    def admins(self):
        """
        Return a list of admins for the group.
        """
        raise NotImplementedError()
    
    @property
    def members_list(self):
        raise NotImplementedError()


class BasePackage(object):
    """
    An implementation of a deployment strategy for a particular package.
    
    Models should define the fields like::
    
        name = models.CharField(max_length=50, unique=True)
        tool_class =  models.CharField(max_length=255,
            help_text="Dotted path notation to tools class.")
        deploy_strategy = models.CharField(max_length=255,
            help_text="Dotted path notation to deploy strategy class.")
        status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    """

    def __unicode__(self):
        return self.name

    @property
    def tools(self):
        return import_object(self.tool_class)()

    @property
    def method(self):
        return import_object(self.deploy_strategy)()


PERMISSIONS = (
    ('admin', 'Admin'),
    ('create', 'Create'),
    ('deploy', 'Deploy'),
    ('write', 'Write'),
    ('read', 'Read'),
)

class BasePermission(object):
    """
    Permissions for groups/projects.  Available perms and descriptions:

    * ``admin``: Ability to edit the group details and memberships.
    * ``create``: Ability to create projects.
    * ``deploy``: Ability to deploy and start/stop applications.
    * ``write``: Ability to read/write code.
    * ``read``: Ability to see the group/project.

    Models should define:
        perm = models.CharField(max_length=20, db_index=True, choices=PERMISSIONS,
            help_text="Action allowed: read, write, create, admin")
        active = models.BooleanField(default=True)
    """

    def __unicode__(self):
        return self.permission


# Version control systems should be set up in the config file.
#VCS_CHOICES = repos.backend_choices()

class BaseRepository(object):
    """
    Represents a repository on a given server with a given VCS backend.

    VCS backends should be configured in the config file::

        [vcs]
        enabled=svn,git
        [svn]
        name=Subversion
        class=cannula.repos.svn
        [git]
        name=GIT
        class=cannula.repos.git
        
    Models should define:
        url = models.CharField("URL", max_length=255,
                               help_text="The base url for the repo.")
        vcs_abbr = models.CharField(max_length=20, choices=VCS_CHOICES,
            default='pythonsvn', help_text="VCS abbr used in config file.")
        server = models.ForeignKey("Server", blank=True, null=True)
    """

    def __unicode__(self):
        return u"(%s) %s" % (self.vcs_abbr, self.url)

    def _get_path(self, path):
        if not path.startswith(self.url):
            if not path.startswith('/'):
                path = '/%s' % path
            path = '%s%s' % (self.url, path)
        return path

    def path_exists(self, path, revision=None, username=None, password=None):
        """Pass along to the VCS backend."""
        path = self._get_path(path)
        return self.vcs.path_exists(path, revision, username, password)

    def checkout(self, path="", revision=None, dest=None,
                 username=None, password=None):
        """Pass along to the VCS backend."""
        path = self._get_path(path)
        return self.vcs.checkout(path, revision, dest, username, password)

    def export(self, path="", revision=None, dest=None,
                 username=None, password=None):
        """Pass along to the VCS backend."""
        path = self._get_path(path)
        return self.vcs.export(path, revision, dest, username, password)

    def checkin(self, path, username=None, password=None, message=""):
        """Pass along to the VCS backend."""
        return self.vcs.checkin(path, username, password, message)

    def add(self, path):
        """Pass along to the VCS backend."""
        return self.vcs.add(path)

    def head(self, username=None, password=None):
        """Returns the latest revision for the repository"""
        return self.vcs.head(self.url, username, password)

    def delete_project(self, user):
        if not self.server:
            return
        connection = self.server.connect()
        with connection:
            connection.delete_project(self.url, user.username)


class BaseProject(object):
    """
    Actual Web project, gets its own repo and url.
    
    Models should define:
        group = models.ForeignKey(Group)
        name = models.CharField(max_length=50)
        abbr = models.CharField(max_length=50, db_index=True)
        desc = models.TextField(blank=True, null=True)
        url = models.CharField(max_length=255, blank=True,
                               help_text="Default URL to use when deploying.")
        repo = models.ForeignKey(Repository, blank=True, null=True,
                                 help_text="Default repository when deploying.")
        members = models.ManyToManyField(User, through="ProjectMembership")
        date_created = models.DateField(default=datetime.now)
    """

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.abbr)

    @property
    def unix_group(self):
        return "%s.%s" % (self.group.abbr, self.abbr)

    @property
    def unix_user(self):
        return "%s.%s" % (self.group.abbr, self.abbr)


class BaseCredential(object):
    """
    A system credential for a host or set of hosts.

    Stores username, certfile, and password. The later
    two are stored encrypted.

    Models should define:
        username = models.CharField(max_length=100)
        certfile = EncryptedTextField(blank=True, null=True,
            help_text="The contents of the private key.")
        password = EncryptedCharField(max_length=255, blank=True, null=True,
            help_text="The password for the username or private key.")
    """

    def __unicode__(self):
        return self.username

    @property
    def token(self):
        """
        Return the authentication 'token'.  If no certfile is used, then return
        a string containing the password.  If a certfile is used, then return a
        2-tuple of the contents of the certfile and the password.
        """
        if self.certfile:
            return (self.certfile, self.password)
        else:
            return self.password


class BaseServer(object):
    """
    Base Server
    
    Models should define:
        name = models.CharField(max_length=255)
        ipaddr = models.CharField(max_length=255)
        port = models.IntegerField(default=22)
        platform_class = models.CharField(max_length=255,
            help_text="Dotted path to system platform type")
        root_path = models.CharField(max_length=512,
            blank=True, null=True,
            help_text="Base path where projects are deployed to.")
        admin_only = models.NullBooleanField(default=False)
        credential = models.ForeignKey(Credential, blank=True, null=True)
    """
    
    def __unicode__(self):
        return self.name

    @property
    def platform(self):
        if getattr(self, '_platform', None):
            return self._platform
        self._platform = import_object(self.platform_class)()
        return self._platform

    # TODO: Add logic for message queues
#    @property
#    def connection(self):
#        """Initializes the connection to this server."""
#        if self.ipaddr == '127.0.0.1' and not self.credential:
#            # No IP address will make OS connection.
#            return CONNECTION_POOL.get()
#        else:
#            if not self.credential:
#                raise Exception("System must have a credential to connect.")
#            return CONNECTION_POOL.get(self.ipaddr, self.credential.username,
#                                       self.credential.token, self.port)
#
#    def connect(self):
#        """Establishes a connection to this server."""
#        return Connector(self, self.connection)


class BaseCluster(object):
    """
    A cluster of servers.

    Useful for logically grouping a set of servers for deployment.

    Clusters can have a parent cluster which allows us to group
    clusters together and manage them the same.
    
    Models should define:
        parent = models.ForeignKey('self', blank=True, null=True)
        name = models.CharField(max_length=255)
        abbr = models.CharField(max_length=30, unique=True)
        hostname = models.CharField(max_length=100, blank=True,
            help_text="The host name that will refer to this cluster for when the"
                      " cluster is behind a load balancer.  E.g. www.example.com"
                      " load balances between www1, www2, etc.")
    
        servers = models.ManyToManyField(Server, through='ClusterServer')
        min_uid = models.IntegerField(blank=True, null=True)
        max_uid = models.IntegerField(blank=True, null=True)
        min_gid = models.IntegerField(blank=True, null=True)
        max_gid = models.IntegerField(blank=True, null=True)
        order = models.IntegerField(default=1,
            help_text="Sorting order of this cluster.")
        deployable = models.NullBooleanField(default=True)
        admin_only = models.NullBooleanField(default=False)
        production = models.NullBooleanField(default=False,
            help_text="Is this cluster a production (non-staging) cluster.")
        jump_host = models.ForeignKey(Server, blank=True, null=True,
            related_name="jumphost",
            help_text="Server that can connect to this cluster.")
    """

    def __unicode__(self):
        return self.name

    @property
    def servers_display(self):
        """Property for listing servers in the admin interface."""
        return ', '.join(map(str, self.servers.all()))

    @property
    def root(self):
        """
        Property for accessing this Cluster's root cluster.

        Root Cluster object is obtained by traversing up the parent
        relationships.  If the object has no parent, then the root cluster is
        itself.
        """
        root_cluster = self
        while root_cluster.parent:
            root_cluster = root_cluster.parent
        return root_cluster

    def list_servers(self):
        """
        Return a list of servers for the cluster.

        If the cluster has a jump host, then it is the only server returned,
        otherwise all servers in the cluster are returned.
        """
        if self.jump_host:
            servers = [self.jump_host]
        else:
            servers = list(self.servers.all())
        return servers


class BaseDeployment(object):
    """
    An instance of a deployed project.

    Models should define:
        project = models.ForeignKey(Project)
        cluster = models.ForeignKey(Cluster)
        url = models.CharField(max_length=255,
            help_text="Absolute URL to deploy project to.")
        package = models.ForeignKey(Package)
        # TODO: we might want to also allow an optional repo object to override
        # the project's default one.
        #repo = models.ForeignKey(Repository, blank=True, null=True,
        #                         help_text="Override repository.")
        repo_path = models.CharField(max_length=512,
            help_text="ie. branch/name, trunk, tag/number, etc...")
        revision = models.CharField(max_length=100, default="HEAD")
        # TODO: what are we defaulting num_processes to for prod deployments?
        num_processes = models.IntegerField(default=1)
        date_stamp = models.DateTimeField(default=datetime.now)
        active = models.BooleanField(default=True)
        status = models.CharField(max_length=50, default="Up")
    """

    def __unicode__(self):
        return "%s: %s (%s)" % (self.cluster, self.repo_path, self.revision)

    @property
    def folder_name(self):
        """Returns a unique folder name for this deployment."""
        stamp = self.date_stamp.strftime('%Y%m%d%H%M%S')
        return "%s_%s" % (self.project.abbr, stamp)

    @property
    def strategy(self):
        return self.package.method

    @property
    def last_update(self):
        from cannula.conf import api
        return api.log.get(self.project.group, self.project, self.cluster)

    @property
    def remote_url(self):
        """The actual url this deployment lives at."""
        return "https://%s%s" % (self.cluster.hostname, self.url)

    def deploy_project(self):
        log.debug("Strategy: %s" % self.strategy)
        return self.strategy.deploy_project(self)

    def delete_deployment(self):
        """Deletes this deployment according to the strategy."""
        log.debug('Deleting deployment: %s' % self)
        return self.strategy.delete_deployment(self)

    def modify_deployment(self, action, user, **kwargs):
        """Modifies this deployment according to the strategy and action."""
        log.debug('%s Executing %r on deployment: %s' % (user, action, self))
        return self.strategy.modify_deployment(self, action, user, **kwargs)


class BaseLog(object):
    """
    Logs for group/project actions.

    Models should define:
        user = models.ForeignKey(User, blank=True, null=True)
        group = models.ForeignKey(Group, blank=True, null=True)
        project = models.ForeignKey(Project, blank=True, null=True)
        cluster = models.ForeignKey(Cluster, blank=True, null=True)
        message = models.CharField(max_length=255)
        timestamp = models.DateTimeField(default=datetime.now)
    """

    def __unicode__(self):
        user_str = self.user and u" by %s" % self.user or u""
        date_str = self.timestamp.strftime('on %B %d, %Y at %l:%M %p')
        return u"%s %s%s" % (self.message, date_str, user_str)


class BaseUnixID(object):
    """
    This model holds the current UID/GID pair so
    we can reference this when adding a new project.

    When the project is deleted this record should stay in the
    database to hold the uid and gid.
    
    Models should define:
        uid = models.IntegerField(db_index=True)
        gid = models.IntegerField(db_index=True)
        project = models.ForeignKey(Project, blank=True, null=True)
        cluster = models.ForeignKey(Cluster, blank=True, null=True)
    
        objects = UnixIDManager()
    """
    def __unicode__(self):
        if self.project:
            return "%s(%s) %s:%s" % (self.project, self.cluster, self.uid, self.gid)
        else:
            return "Defunct %s:%s" % (self.uid, self.gid)

    @property
    def username(self):
        if self.project:
            return self.project.unix_user

    @property
    def groupname(self):
        if self.project:
            return self.project.unix_group

    def unsync(self):
        """Delete the user account that was created on the servers."""
        if not self.project or not self.cluster:
            raise Exception("No project to sync")
        if not self.cluster.jump_host:
            # TODO: Run on all machines?
            raise Exception("No jumphost on cluster")

        conn = self.cluster.jump_host.connect()
        with conn:
            conn.userdel(self.username)
            conn.groupdel(self.groupname)
            conn.updateaccounts()
        log.debug("UnixID unlinked: %s" % self)
        self.project = None
        self.cluster = None
        self.save()

    def sync(self):
        """This should create/delete users groups on the cluster."""
        if not self.project or not self.cluster:
            raise Exception("No project to sync")
        if not self.cluster.jump_host:
            # TODO: Run on all machines?
            raise Exception("No jumphost on cluster")

        # Else we need to create the user
        conn = self.cluster.jump_host.connect()
        with conn:
            group_changed = conn.groupsync(self.groupname, self.gid)
            user_changed = conn.usersync(self.username, self.uid, self.groupname)
            if group_changed or user_changed:
                # We only need to update accounts if something actually changed.
                conn.updateaccounts()
        return True
