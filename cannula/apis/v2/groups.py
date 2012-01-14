from logging import getLogger

from django.db.models.loading import get_model

from cannula.apis import ApiError, DuplicateObject, BaseAPI, PermissionError
from cannula.api import api

log = getLogger('api')

class GroupAPI(BaseAPI):
    
    model = get_model('cannula', 'projectgroup')  
    
    def _create(self, name, user, description, **kwargs):
        if not user.has_perm('add_projectgroup'):
            raise PermissionError("You are not allowed to add Groups!")
        group, created = self.model.objects.get_or_create(name=name, 
            defaults={'description':description})
        if not created:
            raise DuplicateObject('Group already exists!')
        return group
    
    
    def _list(self, user=None, perm=None, **kwargs):
        if user:
            user = api.users.get(user)
            groups = user.projectgroup_set.all()
            if perm is not None:
                if not perm in ['add', 'modify', 'delete']:
                    raise ApiError("Permission must be one of 'add', 'modify', or 'delete'")
                kwargs = {
                    'groupmembership__%s' % perm: True
                }
                groups = groups.filter(**kwargs)
        else:
            groups = self.model.objects.all()
        return groups.order_by('name').distinct()
    
    
    def create(self, name, user, description='', **kwargs):
        user = api.users.get(user)
        # create group
        group = self._create(name, user, description, **kwargs)
        api.permissions.grant_admin(user, group)
        msg = 'Creating new group: %s' % name
        log.info(msg)
        api.log.create(message=msg, user=user, group=group)
        return group
    
    
    def list(self, user=None, perm=None, **kwargs):
        """
        Return a list of all groups.

        If user is given, then filter the list of groups to only those that
        the user has membership too (any permission).

        If perm is given, then filter the list of groups to only
        those that the user has the given permission to.
        """
        return self._list(user=user, perm=perm, **kwargs)
