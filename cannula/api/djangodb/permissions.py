from logging import getLogger

from django.db.models.loading import get_model

from cannula.api.base.permissions import PermissionAPIBase
from cannula.conf import api

GroupMembership = get_model('cannula', 'groupmembership')
ProjectMembership = get_model('cannula', 'projectmembership')
Group = get_model('cannula', 'group')
Project = get_model('cannula', 'project')
Permission = get_model('cannula', 'permission')

log = getLogger('api')

class PermissionAPI(PermissionAPIBase):
    
    
    def _get(self, perm):
        if isinstance(perm, Permission):
            return perm
        return Permission.objects.get(perm__iexact=perm)
    
    
    def _list(self, active, user, group, project):
        if active:
            perms = Permission.objects.filter(active=True)
        else:
            perms = Permission.objects.filter(active=False)
        if group:
            perms = GroupMembership.objects.filter(user=user, group=group).values('permission')
        if project:
            proj_perms = set(ProjectMembership.objects.filter(user=user, project=project).values('permission'))
            group_perms = set(perms)
            perms = proj_perms.union(group_perms)
        return list(perms)
            
            

    def _has_perm(self, user, perm, group, project, obj):
        if user.is_superuser:
            return True
        group_count = 0
        project_count = 0
        if obj:
            if isinstance(obj, Group):
                group = obj
            elif isinstance(obj, Project):
                project = obj
        if group:
            gm = GroupMembership.objects.filter(user=user, group=group, permission=perm)
            group_count = gm.count()
        if project:
            pm = ProjectMembership.objects.filter(user=user, project=project, permission=perm)
            project_count = pm.count()
        return group_count or project_count
    
    def _revoke(self, user, group, project, req_user, perm):
        """Subclasses should define this."""
        if project:
            # TODO: implement it!!
            raise NotImplementedError()

        if perm:
            message = ("%s revoked permission: %s from user: %s for group: %s"
                       % (req_user, perm, user, group))
            memberships = GroupMembership.objects.filter(user=user, group=group,
                                                         permission=perm)
        else:
            message = ("%s revoked all permissions from user: %s for group: %s"
                       % (req_user, user, group))
            memberships = GroupMembership.objects.filter(user=user, group=group)

        memberships.delete()
        log.info(message)
        api.log.create(message=message, user=req_user, group=group)
    
    def _grant(self, user, perms, group, project, req_user):
        if project:
            # TODO: Implement it!!
            raise NotImplementedError()
        perm_set = set([api.permissions.get(perm) for perm in perms])

        for perm in perm_set:
            GroupMembership.objects.get_or_create(user=user, group=group,
                                                  permission=perm)

            message = ("%s granted permission: %s to user: %s for group: %s"
                       % (req_user, perm.perm, user, group))
            log.info(message)
            api.log.create(message=message, user=req_user, group=group)

