from collections import defaultdict, deque, namedtuple
from logging import getLogger
from os.path import split as pathsplit
import posixpath

from cannula.utils import shell_escape
from cannula.platform import Platform, PlatformError, CompileError


log = getLogger('cannula.platform')

group_struct = namedtuple('group', 'name gid members')
user_struct = namedtuple('user', 'name uid gid group groups comment home shell')


class POSIX(Platform):
    """Base POSIX platform.
    
    This should work for most unix-like systems the *_cmd attributes
    should be adjusted to make the locations on the various systems.
    """

    # Commands that should be run using sudo.  Can be used by subclasses.
    sudo_commands = ()

    # filesystem operations
    chgrp_cmd = '/bin/chgrp %s %s %s'
    chmod_cmd = '/bin/chmod %s %s %s'
    chown_cmd = '/bin/chown %s %s %s'
    df_cmd = '/bin/df -T'
    ln_cmd = '/bin/ln -fs %s %s'
    mkdir_cmd = '/bin/mkdir %s %s'
    mv_cmd = '/bin/mv %s %s'
    rm_cmd = '/bin/rm %s %s -- %s'
    rmdir_cmd = '/bin/rmdir %s'
    rel_ln_cmd = 'cd %s && /bin/ln -fs %s %s'
    test_cmd = '/usr/bin/test -e %s'
    touch_cmd = '/bin/touch %s'
    untar_cmd = '/bin/tar -x%sf %s -C %s'
    sudo_cmd = '/usr/bin/sudo %s'
    byte_compile_cmd = '%s -m compileall %s'

    # user and group operations
    groupadd_cmd = '/usr/sbin/groupadd -g %d %s'
    groupdel_cmd = '/usr/sbin/groupdel %s'
    groupget_cmd = '/bin/grep ^%s: /etc/group'
    groupmod_cmd = '/usr/sbin/groupmod -g %d %s'
    groups_cmd = '/bin/cat /etc/group'
    useradd_cmd = '/usr/sbin/useradd -u %d -m %s %s'
    userdel_cmd = '/usr/sbin/userdel -r %s'
    userget_cmd = '/bin/grep ^%s: /etc/passwd'
    userget_groups_cmd = '/usr/bin/id -Gn %s'
    usermod_cmd = '/usr/sbin/usermod %s %s'
    users_cmd = '/bin/cat /etc/passwd'

    def __getattribute__(self, name):
        """
        Prepend sudo statement to commands listed in sudo_commands.
        """
        value = super(POSIX, self).__getattribute__(name)
        if name in super(POSIX, self).__getattribute__('sudo_commands'):
            return self.sudo_cmd % value
        return value
    
    def sudo(self, channel, cmd):
        """
        Run an arbitrary command with sudo
        """
        self.execute(channel, self.sudo_cmd % cmd)
        
    
    def chgrp(self, channel, path, gid, recursive=False):
        """Changes the group owner of the specified filesystem path."""

        recursive = ('-R' if recursive else '')
        self.execute(channel, self.chgrp_cmd % (recursive, gid, shell_escape(path)))

    def chmod(self, channel, path, mode, recursive=False):
        """Changes the permission mode of the specified filesystem path."""

        recursive = ('-R' if recursive else '')
        # mode can be an int or symbolic mode representation (e.g. g+rw).
        # If we get an int, turn it into octal representation.
        if isinstance(mode, int):
            mode = oct(mode)
        self.execute(channel, self.chmod_cmd % (recursive, mode, shell_escape(path)))

    def chown(self, channel, path, uid, gid=None, recursive=False):
        """
        Changes the user and possibly the group owner of the specified 
        filesystem path.
        """
        user = ('%s:%s' % (uid, gid) if gid else uid)
        recursive = ('-R' if recursive else '')
        self.execute(channel, self.chown_cmd % (recursive, user, shell_escape(path)))

    def link(self, channel, target, path, absolute=False):
        """Creates the specified symbolic link."""

        if absolute:
            self.execute(channel, self.ln_cmd % (shell_escape(target),
                                                   shell_escape(path)))
        else:
            head, tail = pathsplit(target)
            self.execute(channel, self.rel_ln_cmd % (shell_escape(head),
                                                       shell_escape(tail),
                                                       shell_escape(path)))

    def mkdir(self, channel, path, parents=False):
        """Creates the specified directory."""
        parents = parents and '-p' or ''
        self.execute(channel, self.mkdir_cmd % (parents, shell_escape(path)))

    def move(self, channel, path, target):
        """Moves the specified filesystem path to the specified target."""

        self.execute(channel, self.mv_cmd % (shell_escape(path),
                                               shell_escape(target)))

    def remove(self, channel, path, recursive=False, force=False):
        """Removes the specified filesystem path."""

        status = channel.execute(self.test_cmd % shell_escape(path), True)
        if status == 0:
            recursive, force = ('-r' if recursive else ''), ('-f' if force else '')
            self.execute(channel, self.rm_cmd % (recursive, force, shell_escape(path)))

    def rmdir(self, channel, path):
        """Removes the directory at path."""
        self.execute(channel, self.rmdir_cmd % shell_escape(path))
    
    def test(self, channel, path):
        self.execute(channel, self.test_cmd % shell_escape(path))
    
    def touch(self, channel, path):
        """Touches the specified filesystem path."""
        self.execute(channel, self.touch_cmd % shell_escape(path))

    def untar(self, channel, file, path=None, zip=True):
        """Untar a file into path. If Path is None will untar in place."""

        if not path:
            path = posixpath.dirname(file)
            
        zip = zip and 'z' or ''
        
        self.execute(channel, self.untar_cmd % (zip, shell_escape(file), shell_escape(path)))
        
    def byte_compile(self, channel, python_exe, path):
        """Byte compile all the python code in a directory."""
        status, content = channel.execute(self.byte_compile_cmd % (shell_escape(python_exe), shell_escape(path)))
        if status != 0:
            print status
            raise CompileError()
        

    def _attrs_incorrect(self, obj, new_attrs):
        """
        A helper method for testing attrs of a user/group.

        new_attrs should be a dictionary mapping attribute names to values.
        If an attribute's value is None, then checking of that attribute will
        be skipped.

        Return a dictionary of attributes that are not correct and the
        corresponding value the attribute should be changed to.  If all
        attributes are correct, then return an empty dictionary.
        """
        # Attributes that need to have sorted() called on them when comparing.
        needs_sort = set(['groups', 'members'])
        details_incorrect = {}

        for attr, new_value in new_attrs.iteritems():
            if new_value is None:
                continue
            current_value = getattr(obj, attr)
            if attr in needs_sort:
                current_value = sorted(current_value)
                new_value = sorted(new_value)
            if new_value != current_value:
                log.debug('%s incorrect, current: %r new: %r'
                          % (attr, current_value, new_value))
                details_incorrect[attr] = new_value
        return details_incorrect

    #
    # Group methods.
    #

    def groupadd(self, channel, name, gid, members=None):
        """Creates the specified system group."""
        if members is not None:
            raise NotImplementedError("Specifing members for groupadd on the"
                                      " POSIX platform class in not yet"
                                      " supported.")
        self.execute(channel, self.groupadd_cmd % (gid, name))

    def groupdel(self, channel, name):
        """Destroys the specified system group."""

        self.execute(channel, self.groupdel_cmd % name)

    def groupget(self, channel, name):
        """Gets information on the specified system group."""

        status, content = channel.execute(self.groupget_cmd % name)
        if status == 0:
            name, _, gid, users = content.strip().split(':')
            return group_struct(name, int(gid), users.split(',') if users else [])
        elif status == 1:
            return None
        else:
            raise PlatformError(status, content)

    def groupmod(self, channel, name, gid):
        """Modifies the specified system group."""

        self.execute(channel, self.groupmod_cmd % (gid, name))

    def group_incorrect(self, channel, group, name, **new_attrs):
        """Determine which group attributes given are not correct.

        group should be the object returned by a groupget() call.
        name is required.  gid and members are optional and will only be
        checked for out-of-sync'ness if given and not None.

        Return a dictionary of attributes that are not correct and the
        corresponding value the attribute should be changed to.  If all
        attributes are correct, then return an empty dictionary.
        """
        details_incorrect = self._attrs_incorrect(group, new_attrs)
        return details_incorrect

    def groupsync(self, channel, name, gid, members=None):
        """Sync the given system group, creating or modifying if needed.

        If members is given, then the group's members will also be checked and
        corrected.  Otherwise if not given, the group's members will not be
        checked or synced.

        Return True if the group needed to be created or modified, and False
        if no action was needed.
        """
        log.debug("syncing system group: %s, gid: %s" % (name, gid))
        group = self.groupget(channel, name)
        if not group:
            log.info('syncing system group, group: %s not found, creating'
                     % name)
            self.groupadd(channel, name, gid, members)
            return True

        details_incorrect = self.group_incorrect(channel, group, name,
                                                 gid=gid, members=members)
        if details_incorrect:
            log.info('syncing system group, group: %s has incorrect data,'
                     ' correcting' % name)
            self.groupmod(channel, name, **details_incorrect)
            return True
        return False

    def groups(self, channel):
        """Return a dict of all groups: groupname -> [group_struct, ...]"""
        status, content = channel.execute(self.groups_cmd)
        if status != 0:
            raise PlatformError(status, content)

        groups = defaultdict(list)
        for line in content.splitlines():
            name, _, gid, member_string = line.strip().split(':')
            users = set(member_string.split(',')) if member_string else set()
            group = group_struct(name, int(gid), users)
            groups[name].append(group)
        return groups

    #
    # User methods.
    #

    def useradd(self, channel, name, uid, group=None, groups=None, home=None, shell=None, comment=None):
        """Creates the specified system user."""

        options = []
        if group:
            options.append('-g %s' % group)
        if groups:
            options.append('-G %s' % ','.join(groups))
        if home:
            options.append('-d %s' % home)
        if shell:
            options.append('-s %s' % shell)
        if comment:
            options.append('-c "%s"' % comment)
        self.execute(channel, self.useradd_cmd % (uid, ' '.join(options), name))

    def userdel(self, channel, name):
        """Destroys the specified system user."""

        self.execute(channel, self.userdel_cmd % name)

    def userget(self, channel, name):
        """Gets information on the specified system user."""

        status, content = channel.execute(self.userget_cmd % name)
        if status == 0:
            name, _, uid, gid, comment, home, shell = content.strip().split(':')
            status, content = channel.execute(self.userget_groups_cmd % name)
            if status == 0:
                content = content.strip().split(' ')
                group, groups = content[ 0 ], set(content[ 1: ])
            else:
                raise PlatformError(status, content)
            return user_struct(name, int(uid), int(gid), group, groups, comment, home, shell)
        elif status == 1:
            return None
        else:
            raise PlatformError(status, content)

    def usermod(self, channel, name, uid=None, group=None, groups=None, home=None, shell=None, comment=None):
        """Modifies the specified system user."""

        options = []
        if uid:
            options.append('-u %d' % uid)
        if group:
            options.append('-g %s' % group)
        if home:
            options.append('-m -d %s' % home)
        if shell:
            options.append('-s %s' % shell)
        if comment:
            options.append('-c "%s"' % comment)
        if groups is not None:
            if groups:
                options.append('-G %s' % ','.join(groups))
            else:
                options.append('--groups= --')
        if options:
            self.execute(channel, self.usermod_cmd % (' '.join(options), name))

    def user_incorrect(self, channel, user, name, **new_attrs):
        """Determine which user attributes given are not correct.

        user should be the object returned by a userget() call.
        name is required.  uid, group, groups, home, shell, and comment are all
        optional and will only be checked for out-of-sync'ness if given and not
        None.

        Return a dictionary of attributes that are not correct and the
        corresponding value the attribute should be changed to.  If all
        attributes are correct, then return an empty dictionary.
        """
        details_incorrect = self._attrs_incorrect(user, new_attrs)
        return details_incorrect

    def usersync(self, channel, name, uid=None, group=None, groups=None,
                 home=None, shell=None, comment=None):
        """Sync the given system user, creating or modifying if needed.

        name is required.  uid, group, groups, home, shell, and comment are all
        optional and will only be checked for out-of-sync'ness if given.

        Return True if the user needed to be created or modified, and False if
        no action was needed.
        """
        user = self.userget(channel, name)
        log.debug("syncing system user: %s" % str(user))
        if not user:
            log.info('syncing system user, user: %s not found, creating' % name)
            self.useradd(channel, name, uid, group, groups, home, shell, comment)
            return True
        details_incorrect = self.user_incorrect(channel, user, name,
                uid=uid, group=group, groups=groups, home=home, shell=shell,
                comment=comment)
        if details_incorrect:
            log.info('syncing system user, user: %s has incorrect data,'
                     ' correcting' % name)
            self.usermod(channel, name, **details_incorrect)
            return True
        return False

    def users(self, channel, min_uid=None, max_uid=None):
        """Return a dict of all users: username -> [user_struct, ...]"""
        status, content = channel.execute(self.users_cmd)
        if status != 0:
            raise PlatformError(status, content)

        users = defaultdict(list)
        for line in content.splitlines():
            name, _, uid, gid, comment, home, shell = line.strip().split(':')
            uid = int(uid)
            # Skip over users outside specified min/max uid.
            if min_uid is not None and uid < min_uid:
                continue
            if max_uid is not None and uid > max_uid:
                continue
            status, content = channel.execute(self.userget_groups_cmd % name)
            if status != 0:
                raise PlatformError(status, content)
            content = content.strip().split(' ')
            group, groups = content[0], set(content[1:])
            user = user_struct(name, uid, int(gid), group, groups, comment, home, shell)
            users[name].append(user)
        return users
