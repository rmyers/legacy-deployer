from logging import getLogger
import datetime
#from datetime.datetime import now

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateResponseMixin, View, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import ModelFormMixin, CreateView

from cannula.models import Project, Key, ProjectGroup
from cannula.forms import ProjectForm, ProjectGroupForm, SSHKeyForm
from cannula.conf import api


log = getLogger('cannula.views')

@login_required
def profile(request):
    keys = api.keys.list(user=request.user)
    groups = api.groups.list(user=request.user)
    return render_to_response('cannula/profile.html',
        RequestContext(request, {
            'keys': keys,
            'groups': groups,
        })
    )

class AuthMixin(object):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(AuthMixin, self).dispatch(*args, **kwargs)
    
class Index(TemplateView):
    template_name = 'cannula/index.html'
    
    def get_context_data(self, **kwargs):
        user = self.request.user
        groups = api.groups.list(user=user)
        groups_create = api.groups.list(user=user, perm='add')
        return RequestContext(self.request, {
            'title': "My Groups and Projects",
            'groups': groups,
            'groups_create': groups_create, 
            # Flag to disable breadcrumbs
            'home_page': True,
            'now': datetime.datetime.now(),
            'news': api.log.news(groups=groups),
        })

class CreateProject(CreateView):
    
    model = Project
    form_class = ProjectForm
    template_name = 'cannula/form.html'
    
    def get_context_data(self, **kwargs):
        kwargs.update({'title': 'Create Project'})
        return kwargs
    
    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instanciating the form.
        """
        kwargs = super(CreateProject, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs
    
    def form_valid(self, form):
        data = form.cleaned_data
        data['user'] = form.user
        self.object = api.projects.create(**data)
        return HttpResponseRedirect(self.get_success_url())

class CreateGroup(CreateView):
    
    model = ProjectGroup
    form_class = ProjectGroupForm
    template_name = 'cannula/form.html'
    
    def get_context_data(self, **kwargs):
        kwargs.update({'title': 'Create Project Group'})
        return kwargs
    
    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instanciating the form.
        """
        kwargs = super(CreateGroup, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs
    
    def form_valid(self, form):
        data = form.cleaned_data
        data['user'] = form.user
        self.object = api.groups.create(**data)
        return HttpResponseRedirect(self.get_success_url())

class CreateKey(CreateView):
    
    model = Key
    form_class = SSHKeyForm
    template_name = 'cannula/form.html'
    
    def get_context_data(self, **kwargs):
        kwargs.update({'title': 'Create Key'})
        return kwargs
    
    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instanciating the form.
        """
        kwargs = super(CreateKey, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs
    
    def form_valid(self, form):
        data = form.cleaned_data
        data['user'] = form.user
        self.object = api.keys.create(**data)
        return HttpResponseRedirect('/accounts/profile/')

class GroupView(DetailView):
    
    model = ProjectGroup
    slug_field = 'name'

class ProjectView(DetailView):
    
    model = Project
    slug_field = 'name'
    
    def get_context_data(self, object, **kwargs):
        kwargs.update({
            'title': unicode(object),
            'project': object,
            'now': datetime.datetime.now(),
            'logs': api.log.list(project=object)})
        return kwargs