from logging import getLogger

from cannula.api import DuplicateObject
from cannula.api import UnitDoesNotExist
from cannula.api import PermissionError
from cannula.api import ApiError
from cannula.api import BaseAPI

from cannula.conf import api

log = getLogger('api')

class PermissionAPIBase(BaseAPI):
    
    
    def _get(self, perm):
        """Subclasses should define this."""
        raise NotImplementedError()
    
    
    def get(self, perm):
        try:
            return self._get(perm)
        except:
            raise UnitDoesNotExist('Permission does not exist')
        
    
    def _list(self, active, user, group, project):
        """Subclasses should define this."""
        raise NotImplementedError()
        
    
    def list(self, active=True, user=None, group=None, project=None):
        if user:
            user = api.users.get(user)
        if group and not user:
            raise ApiError('Must pass a user with the group argument')
        else:
            group = api.groups.get(group)
        if project and not group:
            raise ApiError('Must pass a group with the project argument')
        else:
            project = api.projects.get(group, project)
        return self._list(active, user, group, project)
    
    
    def _has_perm(self, user, perm, group, project, obj):
        """Subclasses should define this."""
        raise NotImplementedError()
    
    
    def has_perm(self, user, perm, group=None, project=None, obj=None):
        if not (group or project or obj):
            raise ApiError("Must pass either group, project, or obj")
        user = api.users.get(user)
        if group:
            group = api.groups.get(group)
        if project and not group:
            raise ApiError('Must pass a group with the project argument')
        elif project:
            project = api.projects.get(group, project)
        perm = self.get(perm)
        return self._has_perm(user, perm, group, project, obj)
    
    
    def grant_admin(self, user, group, project=None, req_user=None):
        """
        Grant admin permission to user and any other permissions required.
        If project is specified, grant permissions only to that project,
        otherwise by default it will grant all permissions for the group.
        """
        user = api.users.get(user)
        if not req_user:
            raise ApiError('req_user keyword argument is required')
        req_user = api.users.get(req_user)
        perms = [perm for perm in self.list()]
        group = api.groups.get(group)
        if project:
            project = api.projects.get(group, project)
        self.grant(user, perms, group, project, req_user)

    def _grant(self, user, perms, group, project, req_user):
        """Subclasses should define this."""
        raise NotImplementedError()
    
    def grant(self, user, perms, group, project=None, req_user=None):
        """
        Grant permissions to user. If project is specified, grant 
        permissions only to that project, otherwise by default it 
        will grant permissions for the group.
        """
        user = api.users.get(user)
        if not req_user:
            raise ApiError('req_user keyword argument is required')
        req_user = api.users.get(req_user)
        group = api.groups.get(group)
        if project:
            project = api.projects.get(group, project)
        perms = set([self.get(perm) for perm in perms])
        return self._grant(user, perms, group, project, req_user)

    def _revoke(self, user, group, project, req_user, perm):
        """Subclasses should define this."""
        raise NotImplementedError()
    
    def revoke(self, user, group, project=None, req_user=None, perm=None):
        user = api.users.get(user)
        if not req_user:
            raise ApiError('req_user keyword argument is required')
        req_user = api.users.get(req_user)
        group = api.groups.get(group)
        if project:
            project = api.projects.get(group, project)
        if perm:
            perm = self.get(perm)
        return self._revoke(user, group, project, req_user, perm)
    
    
    def is_admin(self, username):
        user = self.get_user(username)
        return user.is_superuser