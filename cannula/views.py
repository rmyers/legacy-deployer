from logging import getLogger
import datetime
#from datetime.datetime import now

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, DetailView

from cannula.models import Profile, Project, Group, Key

log = getLogger('cannula.views')

class AuthMixin(object):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AuthMixin, self).dispatch(*args, **kwargs)
    
class Index(TemplateView):
    template_name = 'cannula/index.html'
    
    def get_context_data(self, **kwargs):
        user = self.request.user
        groups = user.groupmembership_set.all()
        return RequestContext(self.request, {
            'title': "My Groups and Projects",
            'groups': groups,
            'groups_create': user.groupmembership_set.filter(can_add=True), 
            'projects': user.project_set.all(),
            # Flag to disable breadcrumbs
            'home_page': True,
            'now': datetime.datetime.now(),
            'news': [],#TODO: make news
        })