from django.contrib import admin

from cannula.models import *

admin.site.register(Profile)
admin.site.register(Key)
admin.site.register(Project)

class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    exclude = ('date_joined',)

class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'date_created']
    inlines = [GroupMembershipInline]
    search_fields = ['name']
admin.site.register(ProjectGroup, GroupAdmin)
