
from django.db.models.loading import get_model

from cannula.api.base.groups import GroupAPIBase
from cannula.conf import api

Group = get_model('cannula', 'group')

class GroupAPI(GroupAPIBase):
    
    
    def _get(self, groupname):
        if isinstance(groupname, Group):
            return groupname
        return Group.objects.get(abbr=groupname)
    
    
    def _create(self, abbr, name, description, **kwargs):
        return Group.objects.create(abbr=abbr, name=name, desc=description)
    
    
    def _list(self, user=None, perm=None, **kwargs):
        if user:
            user = api.users.get(user)
            groups = user.group_set.all()
            if perm:
                groups = groups.filter(groupmembership__permission__perm=perm)
            if user.is_superuser:
                groups = Group.objects.all()
        else:
            user = None
            groups = Group.objects.all()
        return groups.order_by('abbr').distinct()