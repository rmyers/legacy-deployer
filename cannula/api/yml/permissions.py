import os

from logging import getLogger

from cannula.api import ApiError, BaseYamlAPI, PermissionError, messages
from cannula.conf import api
from cannula.api.exceptions import UnitDoesNotExist


logger = getLogger('api')

class PermissionAPI(BaseYamlAPI):
    
    model = messages.GroupMembership
    base_dir = "permissions"
    
    def obj_name(self, group, user):
        group = api.groups.get(group)
        user = api.users.get(user)
        return '%s:%s' % (group.name, user.name)
    
    def list_members(self, group):
        group = api.groups.get(group)
        
        members = []
        
        for m in self.list_all():
            g, u = m.split(':')
            if g == group.name:
                members.append(u)
        
        return members
                
    def list_groups(self, user):
        user = api.users.get(user)
        groups = []
        
        for m in self.list_all():
            g, u = m.split(':')
            if u == user.name:
                groups.append(g)
        
        return groups
    
    def for_group(self, group):
        group = api.groups.get(group)
        
        perms = []
        
        for m in self.list_all():
            g, _ = m.split(':')
            if g == group.name:
                perms.append(m)
        
        return perms
    
    def has_perm(self, user, perm, group=None, project=None, obj=None):
        if not perm in ['add', 'modify', 'delete']:
            # Bail early!
            return False

        user = api.users.get(user)
        
        if user.is_admin:
            return True
        
        if group:
            group = api.groups.get(group)
        elif project:
            project = api.projects.get(project)
            group = api.groups.get(project.group)
        else:
            # Else check for project/group permissions
            if isinstance(obj, messages.Project):
                group = obj.group
            elif isinstance(obj, messages.Group):
                group = obj
            else:
                # We do not handle anything else
                return False
        
        # Else check the group membership
        try:
            gm = self.get(self.obj_name(group, user))
            if gm is None:
                return False
            return getattr(gm, perm)
        except UnitDoesNotExist:
            return False
    
    
    def grant_admin(self, user, group):
        """
        Grant admin permission to user and any other permissions required.
        If project is specified, grant permissions only to that project,
        otherwise by default it will grant all permissions for the group.
        
        This is only run to create the initial group admin and only works 
        if no members allready exist. IE just after group creation.
        """
        user = api.users.get(user)
        group = api.groups.get(group)
        if self.list_members(group):
            raise ApiError("Grant admin only allowed on new group instances.")
        logger.info("Granting admin permissions to %s on %s", user, group)
        self.create(self.obj_name(group, user), perms=['add', 'modify', 'delete'], force=True)
    
    def create_message(self, name, **kwargs):
        obj = self.model(name)
        for perm in kwargs.get('perms', []):
            setattr(obj, perm, True)
        return obj
    
    def is_admin(self, username):
        user = api.users.get(username)
        return user.is_admin()