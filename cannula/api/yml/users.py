from logging import getLogger

from cannula.api import DuplicateObject
from cannula.api import UnitDoesNotExist
from cannula.api import PermissionError
from cannula.api import BaseYamlAPI, messages
from cannula.conf import api

log = getLogger('api.users')

class UserAPI(BaseYamlAPI):
    
    model = messages.User
    base_dir = 'users'
    
    
    def delete(self, username, request_user, perm='user.delete'):
        req_user = self.get(request_user)
        if not req_user.has_perm(perm):
            raise PermissionError("User: %s, does not have perm: %s" % (req_user, perm))
        user = self.get(username)
        user.delete()
    
    def info(self, username):
        user = self.get(username)
        #TODO: make version live
        output = "Cannula Version: 0.1\n"
        output += "-------------------------------------------\n"
        output += "Your Groups and Projects\n"
        groups = [g.group for g in user.groupmembership_set.all()]
        for group in groups:
            output += " - %s" % group
            for project in group.projects:
                output += "\t%s" % project
        
        return output
    
    def update(self, user):
        """Hook for updating user information. (LDAP, external DB, etc.)"""