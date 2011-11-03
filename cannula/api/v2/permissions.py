from logging import getLogger

from django.db.models.loading import get_model

from cannula.api import UnitDoesNotExist
from cannula.api import ApiError
from cannula.api import BaseAPI
from cannula.api import PermissionError
from cannula.conf import api


log = getLogger('api')

class PermissionAPI(BaseAPI):
    
    model = get_model('cannula', 'groupmembership')
    # models used for permission checking
    project = get_model('cannula', 'project')
    group = get_model('cannula', 'projectgroup')
    
    def has_perm(self, user, perm, group=None, project=None, obj=None):
        if not perm in ['add', 'modify', 'delete']:
            # Bail early!
            return False

        user = api.users.get(user)
        
        if group:
            group = api.groups.get(group)
        elif project:
            project = api.projects.get(project)
            group = project.group
        else:
            # Else check for project/group permissions
            if isinstance(obj, self.project):
                group = obj.group
            elif isinstance(obj, self.group):
                group = object
            else:
                # We do not handle anything else
                return False
        
        # Else check the group membership
        kwargs = {
            'user': user,
            'group': group,
            perm: True,
        }
        return self.model.objects.filter(**kwargs).count()
    
    
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
        if self.model.objects.filter(group=group).count():
            raise ApiError("Grant admin only allowed on new group instances.")
        log.info("Granting admin permissions to %s on %s", user, group)
        self._grant(user, ['add', 'modify', 'delete'], group)

    def _grant(self, user, perms, group):
        perm_model, _ = self.model.objects.get_or_create(user=user, group=group)
        [setattr(perm_model, p, True) for p in perms]
        perm_model.save()
    
    def grant(self, user, perms, group, req_user):
        """
        Grant permissions to user. If project is specified, grant 
        permissions only to that project, otherwise by default it 
        will grant permissions for the group.
        """
        user = api.users.get(user)
        req_user = api.users.get(req_user)
        group = api.groups.get(group)
        if not self.has_perm(user, 'modify', group=group):
            raise PermissionError("You don't have permission to modify this group!")
        perms = set([self.get(perm) for perm in perms])
        return self._grant(user, perms, group)

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