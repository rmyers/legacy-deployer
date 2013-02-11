"""
GAE Models for Cannula

@author: rmyers
"""

from google.appengine.ext import ndb
from webapp2_extras.appengine.auth.models import User as BaseUser
from webapp2_extras import security
from webapp2_extras import auth

class User(BaseUser):

    first_name = ndb.StringProperty()
    last_name = ndb.StringProperty()
    
    @property
    def email(self):
        return self._grab_auth_id('email')
        
    def _grab_auth_id(self, kind):
        """helper method to return the first auth_id of a certain kind"""
        uid = None
        for auth in self.auth_ids:
            if auth.startswith('%s:' % kind):
                _, uid = auth.split(':')
                break
        return uid
    
    def update_password(self, password, new_password):
        """Update the password for the user if the existing password matches."""
        if not security.check_password_hash(password, self.password):
            raise auth.InvalidPasswordError()
        
        self.password = security.generate_password_hash(new_password, length=12)
        self.put()
    