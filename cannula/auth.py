
from django.contrib.auth.backends import ModelBackend
from django.db.models.loading import get_model

ProjectGroup = get_model('cannula', 'projectgroup')
Project = get_model('cannula', 'project')

class CannulaBackend(ModelBackend):
    
    supports_object_permissions = True
    supports_anonymous_user = True
    supports_inactive_user = True
    
    def has_perm(self, user_obj, perm, obj=None):
        if obj is None:
            return super(CannulaBackend, self).has_perm(user_obj, perm)
        
        # Else check for project/group permissions
        if isinstance(obj, Project):
            group = obj.group
        elif isinstance(obj, ProjectGroup):
            group = object
        else:
            # We do not handle anything else
            return False
        
        if perm == 'add':
            qs = user_obj.groupmembership_set.filter(group=group, can_add=True)
        elif perm == 'modify':
            qs = user_obj.groupmembership_set.filter(group=group, can_modify=True)
        elif perm == 'delete':
            qs = user_obj.groupmembership_set.filter(group=group, can_delete=True)
        else:
            return False
        
        return bool(qs.count())