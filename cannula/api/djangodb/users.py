
from django.db.models.loading import get_model

from cannula.api.base.users import UserAPIBase

User = get_model('auth', 'user')

class UserAPI(UserAPIBase):
    
    
    def _get(self, username, **kwargs):
        if isinstance(username, User):
            return username
        return User.objects.get(username=username)

    
    def _create(self, username, **kwargs):
        email = kwargs.get('email', '%s@localhost.com' % username)
        password = kwargs.get('password', '!')
        new_user = User.objects.create_user(username, email, password)
        self.update(new_user)
        return new_user
    
    
    def update(self, user):
        """Hook for updating user information. (LDAP, external DB, etc.)"""