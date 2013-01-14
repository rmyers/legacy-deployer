from django.conf.urls.defaults import url, patterns, include
from django.contrib import admin
from django.conf import settings

admin.autodiscover()

from tastypie.api import Api

from cannula import main

v1_api = Api(api_name='v1')
v1_api.register(main.KeyResource())
#v1_api.register(main.ProjectResource())
#v1_api.register(main.GroupResource())
v1_api.register(main.UserResource())

urlpatterns = patterns('',
    (r'^accounts/login/$', 'cannula.views.login'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout',
        {'template_name': 'cannula/logged_out.html'}),
     (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
)

    
urlpatterns += patterns('cannula.views',
    url(r'^$', 'index', name='cannula-index'),
    url(r'^api/', include(v1_api.urls)),
    url(r'^_api/groups/(?P<group>[^/]+)?', 'group_api', name='group-api'),
    url(r'^_api/keys/(?P<key>[^/]+)?', 'key_api', name='key-api'),
    url(r'^_api/projects/(?P<project>[^/]+)?', 'project_api', name='project-api'),
    url(r'^_settings/', 'manage_settings', name='manage-settings'),
    url(r'^accounts/profile/$', 'profile', name="account-profile"),                    
    url(r'^create/project/$', 'create_project', name='create-project'),
    url(r'^(?P<group>[^/]+)/$', 'group_details', name='group-details'),
    url(r'^(?P<group>[^/]+)/(?P<project>[^/]+)/$', 'project_details', name='project-details'),
)

