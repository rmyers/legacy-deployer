from django.conf.urls.defaults import url, patterns, include
from django.contrib import admin
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',
    (r'^accounts/login/$', 'django.contrib.auth.views.login', 
        {'template_name': 'cannula/form.html'}),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout',
        {'template_name': 'cannula/logged_out.html'}),
     (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    # strip off the leading '/' from the MEDIA_URL
    media_url = settings.MEDIA_URL[1:]
    urlpatterns += patterns('',
        (r'^' + media_url + '(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
        # Stop favicon 500 errors when developing
        (r'^(?P<path>favicon\.ico)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': False})
    )
    
urlpatterns += patterns('cannula.views',
    url(r'^$', 'index', name='cannula-index'),
    url(r'^_api/groups/(?P<group>[^/]+)?', 'group_api', name='group-api'),
    url(r'^_api/keys/(?P<key>[^/]+)?', 'key_api', name='key-api'),
    url(r'^_api/projects/(?P<project>[^/]+)?', 'project_api', name='project-api'),
    url(r'^_settings/', 'manage_settings', name='manage-settings'),
    url(r'^accounts/profile/$', 'profile', name="account-profile"),                    
    url(r'^create/project/$', 'create_project', name='create-project'),
    url(r'^(?P<group>[^/]+)/$', 'group_details', name='group-details'),
    url(r'^(?P<group>[^/]+)/(?P<project>[^/]+)/$', 'project_details', name='project-details'),
)

