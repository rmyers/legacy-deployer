from logging import getLogger



from cannula.api import UnitDoesNotExist
from cannula.api import ApiError
from cannula.api import BaseAPI
from cannula.conf import api
from cannula.api.exceptions import PermissionError

log = getLogger('api')

class PermissionAPI(BaseAPI):
    
    def has_perm(self, user, perm, group=None, project=None):
        user = api.users.get(user)
        if group:
            obj = api.groups.get(group)
        elif project:
            obj = api.projects.get(project)
        else:
            raise ApiError("has_perm must be called with either a project or group.")
        return user.has_perm(perm, obj=obj)
    
    
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

    def _grant(self, user, perms, group, req_user):
        #TODO: code this!
        raise NotImplementedError()
    
    def grant(self, user, perms, group, req_user):
        """
        Grant permissions to user. If project is specified, grant 
        permissions only to that project, otherwise by default it 
        will grant permissions for the group.
        """
        user = api.users.get(user)
        req_user = api.users.get(req_user)
        group = api.groups.get(group)
        perms = set([self.get(perm) for perm in perms])
        return self._grant(user, perms, group, req_user)

    def _revoke(self, user, group, req_user, perm):
        if not req_user.has_perm('can_modify', group):
            raise PermissionError("Insufficient permissions.")
        
        if perm is None:
            # Revoke all perms (delete group membership)
            # TODO: do it!
            return True
        
        # TODO: remove single permission
        return True 
    
    def revoke(self, user, group, req_user, perm=None):
        """Revoke one or all perms for a user in a group.
        
        * user: user whose permissions are to be modified
        * group: name of group.
        * req_user: user that has group 'modify' perm.
        * perm (optional): perm to revoke
        """
        user = api.users.get(user)
        req_user = api.users.get(req_user)
        group = api.groups.get(group)
        if perm is not None:
            perm = self.get(perm)
        return self._revoke(user, group, req_user, perm)
    
    
    def is_admin(self, username):
        user = api.users.get(username)
        return user.is_superuser()