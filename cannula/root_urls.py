from django.conf.urls.defaults import url, patterns, include
from django.conf import settings

urlpatterns = patterns('',
    (r'^%s' % settings.MAIN_URL, include('cannula.urls')),
)
