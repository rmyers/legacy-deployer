from django.conf.urls.defaults import patterns, include
from django.conf import settings

# Prefix the whole application under settings.MAIN_URL
#
# This allows us to run the site on the same domain and not
# stomp on the applications urls.
urlpatterns = patterns('',
    (r'^%s' % settings.MAIN_URL, include('cannula.urls')),
)
