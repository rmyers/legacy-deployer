from logging import getLogger

from cannula.api import BaseYamlAPI, PermissionError, messages
from cannula.conf import api
from cannula.api.exceptions import ApiError
import os

logger = getLogger('api')

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
        logger.info(msg)
        
    
    def list(self, user=None):
        """
        Return a list of all groups.

        If user is given, then filter the list of groups to only those that
        the user has membership too (any permission).
        """
        if user is not None:
            # check the group membership api
            return [self.get(g) for g in api.permissions.list_groups(user)]
        
        else: 
            # return the list of groups on filesystem
            groups = os.listdir(self.pd_dir)
            return [g.replace('.pb', '') for g in groups]
    
    def add_project(self, name, project_name):
        group = self.get(name)
        group.projects.append(project_name)
        self.write(name, group)
    
    def delete_project(self, name, project_name):
        group = self.get(name)
        if project_name in group.projects:
            group.projects.remove(project_name)
            self.write(name, group)
            return True
        return False
    
    def list_projects(self, name, fetch=False):
        group = self.get(name)
        if fetch:
            return [api.projects.get(p) for p in group.projects]
        return group.projects
        
    def delete(self, name, user):
        group = self.get(name)
        user = api.users.get(user)
        
        if not user.has_perm('delete', group=group):
            raise PermissionError("You do not have permission to delete groups")
        
        logger.info("Deleting permissions for group: %s", group)
        for perm in api.permissions.for_group(group):
            api.permissions.delete(perm)
        
        return super(GroupAPI, self).delete(name)