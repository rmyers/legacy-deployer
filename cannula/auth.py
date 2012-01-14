
from django.contrib.auth.backends import ModelBackend

from cannula.api import api

class CannulaBackend(ModelBackend):
    
    supports_object_permissions = True
    supports_anonymous_user = True
    supports_inactive_user = True
    
    def has_perm(self, user_obj, perm, obj=None):
        if obj is None:
            return super(CannulaBackend, self).has_perm(user_obj, perm)
        
        return api.permissions.has_perm(user_obj, perm, obj=obj)