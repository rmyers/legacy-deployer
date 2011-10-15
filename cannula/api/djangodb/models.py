from __future__ import with_statement

from datetime import datetime
import logging

from django.db import models, IntegrityError
from django.contrib.auth.models import User

from cannula.fields import EncryptedCharField, EncryptedTextField
from cannula.utils import import_object
from cannula.api.base import models as ApiModels
from cannula.conf import VCS_CHOICES, METHOD_CHOICES, PACKAGE_CHOICES


log = logging.getLogger('cannula')

STATUS_CHOICES = (
    ('active', 'Active'),
    ('inactive', 'Inactive'),
    ('dep', 'Deprecated'),
    ('pend', 'Pending Deprecation'),
    ('pre', 'Pre-release'),
    ('admin', 'Admin only'),
)


class Group(models.Model, ApiModels.BaseGroup):
    """
    Project Group

    Collection of projects that users have access to. Users can belong to multiple
    groups. But usually there is one group per department.

    The project group defines the main url and the username that the code is owned
    by and the wsgi process runs as.
    """
    name = models.CharField(max_length=100, help_text="Verbose Name")
    abbr = models.CharField(max_length=50,
        help_text="This is used as the username, keep it short and all lower case (its, hr, hrms, etc..)",
        unique=True, db_index=True)
    desc = models.TextField(blank=True, null=True)
    members = models.ManyToManyField(User, through="GroupMembership")
    date_created = models.DateField(default=datetime.now)

    class Meta:
        app_label = "cannula"
        ordering = ('abbr',)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.abbr)

    def admins(self):
        """
        Return a list of admins for the group.
        """
        return self.members.filter(groupmembership__permission__perm='admin')
    
    @property
    def members_list(self):
        return self.members.all()
    
    @property
    def projects(self):
        return self.project_set.all()

#class Status(models.Model):
#    slug = models.SlugField()
#    display_name = models.CharField(max_length=100, blank=True)
#
#    def __unicode__(self):
#        if self.display_name:
#            return self.display_name
#        return self.slug


class Package(models.Model, ApiModels.BasePackage):
    """
    An implementation of a deployment strategy for a particular package.
    """
    name = models.CharField(max_length=50, unique=True)
    tool_class =  models.CharField(max_length=255, choices=PACKAGE_CHOICES,
        help_text="Dotted path notation to tools class.")
    deploy_strategy = models.CharField(max_length=255, choices=METHOD_CHOICES,
        help_text="Dotted path notation to deploy strategy class.")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        app_label = "cannula"
        ordering = ('-name',)


class Permission(models.Model, ApiModels.BasePermission):
    """
    Permissions for groups/projects.  Available perms and descriptions:

    * ``admin``: Ability to edit the group details and memberships.
    * ``create``: Ability to create projects.
    * ``deploy``: Ability to deploy and start/stop applications.
    * ``write``: Ability to read/write code.
    * ``read``: Ability to see the group/project.
    """
    perm = models.CharField(max_length=20, db_index=True,
        help_text="Action allowed: read, write, create, admin")
    default = models.BooleanField(default=True)
    active = models.BooleanField(default=True)

    class Meta:
        app_label = "cannula"
        ordering = ('perm',)

    def __unicode__(self):
        return self.perm.title()


class GroupMembership(models.Model):
    """
    Many to Many relationship for the Project Group membership. This holds a
    little information about the user, such as the date added and the
    permission level they have.
    """
    user = models.ForeignKey(User)
    group = models.ForeignKey(Group)
    permission = models.ForeignKey(Permission)
    date_joined = models.DateField(default=datetime.now)

    def __unicode__(self):
        return u"%s(%s)" % (self.user, self.permission)

    class Meta:
        app_label = "cannula"
        ordering = ('user', 'permission')


class Repository(models.Model, ApiModels.BaseRepository):
    """
    Represents a repository on a given server with a given VCS backend.

    VCS backends should be configured in the settings file::

        CANNULA_VCS_ENABLED = ('svn', 'git', 'hg', 'bzr')
        
    """
    url = models.CharField("URL", max_length=255,
                           help_text="The base url for the repo.")
    vcs_abbr = models.CharField(max_length=20, choices=VCS_CHOICES,
        default='pythonsvn', help_text="VCS abbr used in config file.")
    server = models.ForeignKey("Server", blank=True, null=True)

    class Meta:
        app_label = "cannula"
        verbose_name_plural = "repositories"


class Project(models.Model, ApiModels.BaseProject):
    """
    Actual Web project, gets its own repo and url.
    """
    group = models.ForeignKey(Group)
    name = models.CharField(max_length=50)
    abbr = models.CharField(max_length=50, db_index=True)
    desc = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    settings = models.TextField(blank=True)
    url = models.CharField(max_length=255, blank=True,
                           help_text="Default URL to use when deploying.")
    repo = models.CharField(max_length=512)
    repo_type = models.CharField(max_length=20, choices=VCS_CHOICES)
    members = models.ManyToManyField(User, through="ProjectMembership")
    date_created = models.DateField(default=datetime.now)

    class Meta:
        app_label = "cannula"
        unique_together = (("group", "abbr"))
        ordering = ('group', 'abbr')


class ProjectMembership(models.Model):
    """
    ProjectMembership

    Many to Many relationship for the "Project". Setting this overrides the Project
    Group membership settings. This holds a little information
    about the user such as the date added and the permission level they have. Currently
    there are four permission levels:

      * ``Admin``: Admin users have full access to edit the project group add/delete users.
      * ``Developers``: Developers can start/stop application and push code to various servers.
      * ``Writers``: Writers have access to the code base but are unable to push changes.
      * ``Readers``: Readers can only check out the code.
    """
    user = models.ForeignKey(User)
    project = models.ForeignKey(Project)
    permission = models.ForeignKey(Permission)
    date_joined = models.DateField(default=datetime.now)

    def __unicode__(self):
        return u"%s(%s)" % (self.user, self.permission)

    class Meta:
        app_label = "cannula"
        ordering = ('user', 'permission')


class Server(models.Model, ApiModels.BaseServer):
    name = models.CharField(max_length=255)
    cluster = models.ForeignKey("Cluster", related_name='servers')
    ipaddr = models.CharField(max_length=255)
    port = models.IntegerField(default=22)
    platform_class = models.CharField(max_length=255,
        help_text="Dotted path to system platform type")
    admin_only = models.NullBooleanField(default=False)
    active = models.NullBooleanField(default=True)
    class Meta:
        app_label = "cannula"

class Cluster(models.Model, ApiModels.BaseCluster):
    """
    A cluster of servers.

    Useful for logically grouping a set of servers for deployment.

    Clusters can have a parent cluster which allows us to group
    clusters together and manage them the same.
    """
    parent = models.ForeignKey('self', blank=True, null=True)
    name = models.CharField(max_length=255)
    abbr = models.CharField(max_length=30, unique=True)
    order = models.IntegerField(default=1,
        help_text="Sorting order of this cluster.")
    deployable = models.NullBooleanField(default=True)
    admin_only = models.NullBooleanField(default=False)
    production = models.NullBooleanField(default=False,
        help_text="Is this cluster a production (non-staging) cluster.")

    class Meta:
        app_label = "cannula"
        ordering = ('order',)

class Deployment(models.Model, ApiModels.BaseDeployment):
    """
    An instance of a deployed project.
    """
    project = models.ForeignKey(Project)
    cluster = models.ForeignKey(Cluster)
    url = models.CharField(max_length=255,
        help_text="Absolute URL to deploy project to ie. '/', '/myapp'")
    package = models.ForeignKey(Package)
    repo_path = models.CharField(max_length=512,
        help_text="ie. branch/name, trunk, tag/number, tip, etc...")
    revision = models.CharField(max_length=100, default="HEAD")
    date_stamp = models.DateTimeField(default=datetime.now)
    active = models.BooleanField(default=False)
    status = models.CharField(max_length=50, default="Down")
    settings = models.TextField(blank=True)
    requirements = models.TextField(blank=True,
        help_text="override the project default requirements")
    
    class Meta:
        app_label = "cannula"

class Log(models.Model, ApiModels.BaseLog):
    """
    Logs for group/project actions.
    """
    user = models.ForeignKey(User, blank=True, null=True)
    group = models.ForeignKey(Group, blank=True, null=True)
    project = models.ForeignKey(Project, blank=True, null=True)
    cluster = models.ForeignKey(Cluster, blank=True, null=True)
    message = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=datetime.now)

    class Meta:
        app_label = "cannula"
        ordering = ('-timestamp',)
        get_latest_by = ('timestamp')


class UnixIDManager(models.Manager):

    def generate_id(self, project, cluster):
        """Generate a unique Unix ID for this project, as serves a 'get' function
        as it returns the existing object if found.

        This looks at the cluster and finds the root cluster,
        then uses the MIN/MAX uid and gid to generate a unique id
        in the correct range for this cluster.

        """
        root_cluster = cluster.root
        try:
            obj = self.get(project=project, cluster=root_cluster)
            return obj
        except:
            # Race conditions are possible here, we loop through until we find
            # free ids that are unique when saved.
            uid, gid = self.free_ids(root_cluster)
            while True:
                if uid > root_cluster.max_uid or gid > root_cluster.max_gid:
                    log.error('Max UID(%s) or GID(%s) reached' % (uid, gid))
                    # TODO: Look for free IDs
                    raise IndexError("UID and/or GID out of range")
                try:
                    new_id = self.create(project=project,cluster=root_cluster,
                                         uid=uid, gid=gid)
                except IntegrityError:
                    log.debug("UnixID duplicate, uid: %s gid: %s, retrying"
                              % (uid, gid))
                    uid += 1
                    gid += 1
                    continue
                else:
                    log.debug("UnixID created: %s" % new_id)
                    return new_id

    def free_ids(self, root_cluster):
        """
        Return the next uid and gid available on the given root_cluster.
        """
        cluster_ids = self.filter(cluster=root_cluster)
        max_values = cluster_ids.aggregate(models.Max('uid'), models.Max('gid'))
        uid = (max_values['uid__max'] or root_cluster.min_uid) + 1
        gid = (max_values['gid__max'] or root_cluster.min_gid) + 1
        return uid, gid

    def unlink(self, project, cluster):
        """
        Remove the association of this project. But leave the record to
        'hold' the ID from being re-used.
        """
        try:
            obj = self.get(project=project, cluster=cluster.root)
            obj.project = None
            obj.cluster = None
            obj.save(using=self._db)
            log.debug("UnixID unlinked: %s" % obj)
        except:
            # no record found
            pass


class UnixID(models.Model, ApiModels.BaseUnixID):
    """
    This model holds the current UID/GID pair so
    we can reference this when adding a new project.

    When the project is deleted this record should stay in the
    database to hold the uid and gid.
    """
    uid = models.IntegerField(db_index=True)
    gid = models.IntegerField(db_index=True)
    project = models.ForeignKey(Project, blank=True, null=True)
    cluster = models.ForeignKey(Cluster, blank=True, null=True)

    objects = UnixIDManager()

    class Meta:
        app_label = "cannula"
        unique_together = (('project', 'cluster'), ('cluster', 'uid'), ('cluster', 'gid'))
