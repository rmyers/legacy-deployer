from django.conf.urls.defaults import url, patterns
from django.contrib.auth.decorators import login_required
from django.conf import settings

from cannula.views import Index, CreateProject, GroupView, ProjectView, CreateGroup, CreateKey

urlpatterns = patterns('',
    url(r'^$', login_required(Index.as_view()), name='cannula-index'),
    (r'^accounts/login/$', 'django.contrib.auth.views.login', 
        {'template_name': 'cannula/form.html'}),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout',
        {'template_name': 'cannula/logged_out.html'}),
    (r'^accounts/profile/$', 'cannula.views.profile'),
    url(r'^create/group/$', login_required(CreateGroup.as_view()), 
        name='cannula-create-group'),
    url(r'^create/project/$', login_required(CreateProject.as_view()), 
        name='create-project'),
    url(r'^create/key/$', login_required(CreateKey.as_view()), 
        name='create-key'),
    url(r'^groups/$', CreateGroup.as_view(), name='cannula-groups'),
    #url(r'^groups/(?P<group>[^/]*)/$', api.groups.details_view, name='group-details'),
    #url(r'^groups/(?P<group>[^/]*)/__(?P<action>add|mod)/$', api.groups.mod_member_view, name='group-mod-member'),
    #url(r'^groups/(?P<group>[^/]*)/(?P<project>[^/]*)/deploy/$', api.projects.deploy_view, name='deploy-application'),
    #url(r'^groups/(?P<group>[^/]*)/(?P<project>[^/]*)/delete/$', api.projects.delete_view, name='delete-project'),
    #url(r'^groups/(?P<group>[^/]*)/(?P<project>[^/]*)/(?P<cluster>[^/]*)/$', api.deployments.modify_view, name='control-application'),
    #url(r'^groups/(?P<group>[^/]*)/(?P<project>[^/]*)/(?P<cluster>[^/]*)/delete/$', api.deployments.delete_view, name='delete-application'),
    #url(r'^groups/(?P<group>[^/]*)/(?P<project>[^/]*)/$', api.projects.details_view, name='project-details'),
    url(r'^projects/$', CreateProject.as_view(), name='cannula-projects'),
    url(r'^(?P<slug>[^/]+)/$', 
        login_required(GroupView.as_view()), 
        name='group-details'
    ),
    url(r'^(?P<group>[^/]+)/(?P<slug>[^/]+)/$', 
        login_required(ProjectView.as_view()), 
        name='project-details'
    ),
)

if settings.DEBUG:
    # strip off the leading '/' from the MEDIA_URL
    media_url = settings.MEDIA_URL[1:]
    urlpatterns += patterns('',
        (r'^' + media_url + '(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )
