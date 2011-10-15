from django.contrib import admin
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from cannula.api.djangodb.models import *


class LogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'cluster', 'group', 'project', 'message']
    list_filter = ['cluster', 'group']
    search_fields = ['message', 'project__abbr', 'group__abbr']
admin.site.register(Log, LogAdmin)


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    exclude = ('date_joined',)

class GroupAdmin(admin.ModelAdmin):
    list_display = ['abbr', 'name', 'date_created']
    inlines = [GroupMembershipInline]
    search_fields = ['abbr', 'name']
admin.site.register(Group, GroupAdmin)


class DeployInline(admin.TabularInline):
    model = Deployment

class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    exclude = ('date_joined',)

class ProjectAdmin(admin.ModelAdmin):
    list_display = ['abbr', 'name', 'group', 'url', 'date_created']
    list_filter = ['date_created', 'group']
    search_fields = ['name', 'url', 'abbr']
    inlines = [DeployInline, ProjectMembershipInline]
    actions = ['destroy_projects']

    def destroy_projects(self, request, queryset):
        from cannula.conf import api
        for proj in queryset:
            try:
                api.projects.delete(proj.group, proj, request.user)
            except:
                pass
    destroy_projects.short_description = "Destroy Projects"

admin.site.register(Project, ProjectAdmin)


class PermissionAdmin(admin.ModelAdmin):
    list_display = ['perm', 'active', 'default']
    list_filter = ['active', 'default']
admin.site.register(Permission, PermissionAdmin)


class ServerAdmin(admin.ModelAdmin):
    list_display = ['name', 'ipaddr', 'port', 'platform_class']
    ordering = ['name']
admin.site.register(Server, ServerAdmin)


class ClusterServerInline(admin.TabularInline):
    model = Server

class ClusterAdmin(admin.ModelAdmin):
    list_display = ['name', 'servers_display']
    inlines = [ClusterServerInline]
    actions = ['restart']

    def restart(self, request, queryset):
        for cluster in queryset:
            for server in cluster.list_servers():
                with server.connect() as connection:
                    connection.bounceapache(cluster.name.lower())
    restart.short_description = "Restart Apache"
admin.site.register(Cluster, ClusterAdmin)


class PackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'tool_class', 'deploy_strategy', 'status']
admin.site.register(Package, PackageAdmin)


class RepositoryAdmin(admin.ModelAdmin):
    list_display = ['url', 'vcs_abbr']
admin.site.register(Repository, RepositoryAdmin)


class UnixAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'project', 'uid', 'gid']
    search_fields = ['project__abbr', 'project__name', 'uid', 'gid']
admin.site.register(UnixID, UnixAdmin)


class DeploymentAdmin(admin.ModelAdmin):
    list_display = ['project', 'cluster', 'package', 'active', 'date_stamp']
    list_filter = ['cluster', 'package', 'active']
    search_fields = ['project__abbr', 'project__name']
    actions = ['migrate_apps', 'destroy_apps']

    def destroy_apps(self, request, queryset):
        for app in queryset:
            app.delete_deployment()
            app.delete()
    destroy_apps.short_description = "Destroy Deployments"

    def migrate_apps(self, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        ids = ','.join(selected)
        return HttpResponseRedirect(reverse('migrate-apps', args=[ids]))
    migrate_apps.short_description = "Migrate Deployments"
admin.site.register(Deployment, DeploymentAdmin)
