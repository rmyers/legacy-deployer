from django.conf.urls.defaults import url, patterns
from django.contrib.auth.decorators import login_required
from django.conf import settings

from cannula.views import CreateProject, CreateGroup, CreateKey

urlpatterns = patterns('',
    url(r'^$', 'cannula.views.index', name='cannula-index'),
    (r'^accounts/login/$', 'django.contrib.auth.views.login', 
        {'template_name': 'cannula/form.html'}),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout',
        {'template_name': 'cannula/logged_out.html'}),
    (r'^accounts/profile/$', 'cannula.views.profile'),
    url(r'^create/group/$', login_required(CreateGroup.as_view()), 
        name='cannula-create-group'),
    url(r'^create/key/$', login_required(CreateKey.as_view()), 
        name='create-key'),
    
)

urlpatterns += patterns('cannula.views',
    url(r'^_api/groups/(?P<group>[^/]+)?', 'group_api', name='group-api'),
    url(r'^_api/keys/(?P<key>[^/]+)?', 'key_api', name='key-api'),
    url(r'^accounts/profile/$', 'profile', name="account-profile"),                    
    url(r'^create/project/$', 'create_project', name='create-project'),
    url(r'^(?P<group>[^/]+)/$', 'group_details', name='group-details'),
    url(r'^(?P<group>[^/]+)/(?P<project>[^/]+)/$', 'project_details', name='project-details'),
)

if settings.DEBUG:
    # strip off the leading '/' from the MEDIA_URL
    media_url = settings.MEDIA_URL[1:]
    urlpatterns += patterns('',
        (r'^' + media_url + '(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )
