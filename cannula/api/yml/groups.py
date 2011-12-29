from logging import getLogger

from cannula.api import BaseYamlAPI, PermissionError, messages
from cannula.conf import api
from cannula.api.exceptions import ApiError
import os

log = getLogger('api')

class GroupAPI(BaseYamlAPI):
    
    model = messages.Group
    base_dir = 'groups'
      
    def create(self, name, user, description=''):
        user = api.users.get(user)
        if not user.is_admin:
            raise PermissionError("You are not allowed to add Groups!")
        
        return super(GroupAPI, self).create(name, user=user, description=description)
    
    def post_create(self, group, name, **kwargs):
        user = kwargs.get('user')
        api.permissions.grant_admin(user, group)
        msg = 'Creating new group: %s' % name
        log.info(msg)
        
    
    def list(self, user=None):
        """
        Return a list of all groups.

        If user is given, then filter the list of groups to only those that
        the user has membership too (any permission).
        """
        if user is not None:
            # check the group membership api
            return api.permissions.list_groups(user)
        
        else: 
            # return the list of groups on filesystem
            groups = os.listdir(self.pd_dir)
            return [g.replace('.pb', '') for g in groups]
        
    def delete(self, name, user):
        group = self.get(name)
        user = api.users.get(user)
        
        if not user.has_perm('delete', group=group):
            raise PermissionError("You do not have permission to delete groups")
        
        return super(GroupAPI, self).delete(name)