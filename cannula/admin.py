from django.contrib import admin

from cannula import models

# TODO: spice these up a bit
admin.site.register(models.Key)
admin.site.register(models.Project)
admin.site.register(models.Deployment)
admin.site.register(models.Log)

class GroupMembershipInline(admin.TabularInline):
    model = models.GroupMembership
    exclude = ('date_joined',)

class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'date_created']
    inlines = [GroupMembershipInline]
    search_fields = ['name']
admin.site.register(models.ProjectGroup, GroupAdmin)
