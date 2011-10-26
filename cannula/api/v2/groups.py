from logging import getLogger

from django.db.models.loading import get_model

from cannula.api import DuplicateObject, UnitDoesNotExist, BaseAPI, PermissionError
from cannula.conf import api

ProjectGroup = get_model('cannula', 'projectgroup')
GroupMembership = get_model('cannula', 'groupmembership')

log = getLogger('api')

class GroupAPI(BaseAPI):
    
    
    def _get(self, groupname):
        if isinstance(groupname, ProjectGroup):
            return groupname
        return ProjectGroup.objects.get(name=groupname)
    
    
    def _create(self, name, description, **kwargs):
        group, created = ProjectGroup.objects.get_or_create(name=name, 
            defaults={'description':description})
        if not created:
            raise DuplicateObject('Group already exists!')
        return group
    
    
    def _list(self, user=None, perm=None, **kwargs):
        if user:
            user = api.users.get(user)
            groups = user.projectgroup_set.all()
            if perm == 'add':
                groups = groups.filter(groupmembership__can_add=True)
            elif perm == 'delete':
                groups = groups.filter(groupmembership__can_delete=True)
            elif perm == 'modify':
                groups = groups.filter(groupmembership__can_modify=True)
            if user.is_superuser:
                groups = ProjectGroup.objects.all()
        else:
            user = None
            groups = ProjectGroup.objects.all()
        return groups.order_by('name').distinct()
    
    def get(self, groupname):
        try:
            return self._get(groupname)
        except:
            raise UnitDoesNotExist("Group does not exist")
    
    
    def create(self, name, description='', user=None, **kwargs):
        req_user = api.users.get(user)
        if not req_user.has_perm('add_projectgroup'):
            raise PermissionError("You are not allowed to add Groups!")
        # create group
        group = self._create(name, description, **kwargs)
        self.add_member(group, req_user, add=True, modify=True, delete=True)
        msg = 'Creating new group: %s' % name
        log.info(msg)
        api.log.create(message=msg, user=req_user, group=group)
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

    
    def members(self, groupname):
        log.debug("Looking up users in group: %s" % groupname)
        group = self.get(groupname)
        return group.members_list
    
    def _add_member(self, group, user, add, modify, delete):
        member, created = GroupMembership.objects.get_or_create(
            user=user, group=group, defaults={
                'can_add': add, 
                'can_modify': modify,
                'can_delete': delete,
            })
        return member
    
    def add_member(self, groupname, user, add=False, modify=False, delete=False):
        group = self.get(groupname)
        user = api.users.get(user)
        return self._add_member(group, user, add, modify, delete)