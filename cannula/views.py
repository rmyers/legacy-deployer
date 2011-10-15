from logging import getLogger
import datetime
#from datetime.datetime import now

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required

from cannula.conf import api 


log = getLogger('cannula.views')

@login_required
def index(request):
    """
    List all the groups and projects a user belongs to.
    """
    user = api.users.get(request.user.username)
    groups = api.groups.list(user)
    context = RequestContext(request, {
        'title': "My Groups and Projects",
        'groups': groups,
        'groups_create': api.groups.list(user=user, perm='create'),
        'groups_admin': api.groups.list(user=user, perm='admin'),
        # Flag to disable breadcrumbs.
        'home_page': True,
        'now': datetime.datetime.now(),
        'news': api.log.news(groups)
    })
    template = 'cannula/index.html'
    return render_to_response(template, context_instance=context)