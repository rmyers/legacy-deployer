from django.conf.urls.defaults import url, patterns
from django.contrib.auth.decorators import login_required
from django.conf import settings

from cannula.conf import api
from cannula.views import Index, CreateProject

urlpatterns = patterns('',
    url(r'^$', login_required(Index.as_view()), name='cannula-index'),
    url(r'^create/group/$', api.groups.create_view, name='cannula-create-group'),
    url(r'^create/project/$', login_required(CreateProject.as_view()), 
        name='create-project'),
    url(r'^groups/$', api.groups.list_view, name='cannula-groups'),
    url(r'^groups/(?P<group>[^/]*)/$', api.groups.details_view, name='group-details'),
    url(r'^groups/(?P<group>[^/]*)/__(?P<action>add|mod)/$', api.groups.mod_member_view, name='group-mod-member'),
    url(r'^groups/(?P<group>[^/]*)/(?P<project>[^/]*)/deploy/$', api.projects.deploy_view, name='deploy-application'),
    url(r'^groups/(?P<group>[^/]*)/(?P<project>[^/]*)/delete/$', api.projects.delete_view, name='delete-project'),
    url(r'^groups/(?P<group>[^/]*)/(?P<project>[^/]*)/(?P<cluster>[^/]*)/$', api.deployments.modify_view, name='control-application'),
    url(r'^groups/(?P<group>[^/]*)/(?P<project>[^/]*)/(?P<cluster>[^/]*)/delete/$', api.deployments.delete_view, name='delete-application'),
    url(r'^groups/(?P<group>[^/]*)/(?P<project>[^/]*)/$', api.projects.details_view, name='project-details'),
    url(r'^projects/$', api.projects.list_view, name='cannula-projects'),
)

if settings.DEBUG:
    # strip off the leading '/' from the MEDIA_URL
    media_url = settings.MEDIA_URL[1:]
    urlpatterns += patterns('',
        (r'^' + media_url + '(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )
