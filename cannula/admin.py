from django.contrib import admin
from django.contrib.auth.models import Permission

from cannula.models import *

admin.site.register(Key)
admin.site.register(Project)
admin.site.register(Permission)

class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    exclude = ('date_joined',)

class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'date_created']
    inlines = [GroupMembershipInline]
    search_fields = ['name']
admin.site.register(ProjectGroup, GroupAdmin)
