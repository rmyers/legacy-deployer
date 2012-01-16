from logging import getLogger

from django.db.models.loading import get_model

from cannula.apis import DuplicateObject
from cannula.apis import UnitDoesNotExist
from cannula.apis import PermissionError
from cannula.apis import BaseAPI
from cannula.api import api

log = getLogger('api.users')

class UserAPI(BaseAPI):
    
    model = get_model('auth', 'user')
    lookup_field = 'username'
      
    def _create(self, username, **kwargs):
        email = kwargs.get('email', '%s@localhost.com' % username)
        password = kwargs.get('password', '!')
        new_user = self.model.objects.create_user(username, email, password)
        self.update(new_user)
        return new_user
    
    def create(self, username, request_user=None, **kwargs):
        req_user = None
        if request_user:
            req_user = self.get(request_user)
        try:
            self.get(username)
            raise DuplicateObject("User already exists.")
        except UnitDoesNotExist:
            # create user
            user = self._create(username, **kwargs)
            msg = "User: %s created" % username
            log.info(msg)
            api.log.create(message=msg, user=req_user)
            return user
    
    
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
            output += " - %s:\n" % group
            for project in group.projects:
                output += "\t- %s\n" % project
        
        return output
    
    def update(self, user):
        """Hook for updating user information. (LDAP, external DB, etc.)"""