from logging import getLogger
import datetime
#from datetime.datetime import now

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponseForbidden,\
    HttpResponseServerError, HttpResponse, HttpResponseNotAllowed
from django.views.generic.edit import CreateView
from cannula.apis.exceptions import DuplicateObject
from django.core.urlresolvers import reverse
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login

try:
    import json
except ImportError: # pragma: nocover
    from django.utils import simplejson as json

from cannula.models import Project, Key, ProjectGroup
from cannula.forms import ProjectForm, ProjectGroupForm, SSHKeyForm,\
    SettingsForm
from cannula.api import api
from cannula.conf import conf_dict, write_config


logger = getLogger('cannula.views')

def respond_json(obj, status=200):
    try:
        json_obj = json.dumps(obj)
    except:
        raise HttpResponseServerError("Could not decode object")
    
    return HttpResponse(json_obj, mimetype='application/json', status=status)

def ajax_errors(form):
    return ' '.join([str(e) for e in form.errors.values()])

@login_required
def profile(request):
    keys = api.keys.list(user=request.user)

    return render_to_response('cannula/profile.html',
        RequestContext(request, {
            'title': unicode(request.user),
            'keys': keys,
            'form': SSHKeyForm(),
        })
    )


@login_required
def index(request):
    user = request.user
    groups = api.groups.list(user=user)
    return render_to_response('cannula/index.html',
        RequestContext(request, {
            'title': "My Groups and Projects",
            'groups': groups,
            # Flag to disable breadcrumbs
            'home_page': True,
            'now': datetime.datetime.now(),
            'form': ProjectGroupForm(),
            'news': api.log.news(groups=groups),
        })
    )

@login_required
def create_project(request):
    group = api.groups.get(request.GET['group'])
    if not request.user.has_perm('add', obj=group):
        raise HttpResponseForbidden("You do not have permission to add projects.")
    
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            # Create the project
            try:
                project = api.projects.create(user=request.user, group=group, **form.cleaned_data)
                return HttpResponseRedirect(reverse('project-details', args=[group.name, project.name]))
            except DuplicateObject:
                form._errors["name"] = form.error_class(['Project by that name already exists'])
    else:
        form = ProjectForm()
    
    return render_to_response('cannula/form.html',
        RequestContext(request, {
            'title': "Create Project for %s" % group,
            'form': form,
        })
    )

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

@login_required
def group_api(request, group=None):
    """Handle listing groups and creating new ones"""
    
    if request.method == 'GET':
        groups = api.groups.list(user=request.user)
        d = {'objects': [group.to_dict() for group in groups]}
        return respond_json(d)
    
    elif request.method == "POST":
        form = ProjectGroupForm(request.POST)
        if form.is_valid():
            try:
                group = api.groups.create(user=request.user, **form.cleaned_data)
            except DuplicateObject:
                return respond_json({'errorMsg': "A group by that name exists already."})
            except:
                return respond_json({'errorMsg': "Unknown error"})
            
            return respond_json(group.to_dict())
        return respond_json({'errorMsg': ajax_errors(form)})
    
    elif request.method == 'DELETE':
        group = api.groups.get(group)
        if not request.user.has_perm('delete', obj=group):
            raise HttpResponseForbidden("You don't have permission to delete this group.")
        
        api.groups.delete(group)
        return respond_json({'message': "group deleted"})
    
    raise HttpResponseNotAllowed()

@login_required
def project_api(request, project=None):
    """Handle listing groups and creating new ones"""
    
    if request.method == "GET":
        group = request.GET.get('group')
        projects = api.projects.list(group=group)
        d = {'objects': [p.to_dict() for p in projects]}
        return respond_json(d)
    
    elif request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            try:
                project = api.projects.create(user=request.user, **form.cleaned_data)
            except:
                logger.exception("Error saving key")
                return respond_json({'errorMsg': "Unknown error"})
            
            return respond_json(project.to_dict())
        return respond_json({'errorMsg': ajax_errors(form)})
    
    elif request.method == 'DELETE':
        project = api.projects.get(project)
        project.delete()
        return respond_json({'message': "project deleted"})
    
    raise HttpResponseNotAllowed()

@login_required
def key_api(request, key=None):
    """Handle listing groups and creating new ones"""
    
    if request.method == "GET":
        keys = api.keys.list(user=request.user)
        d = {'objects': [k.to_dict() for k in keys]}
        return respond_json(d)
    
    elif request.method == "POST":
        form = SSHKeyForm(request.POST)
        if form.is_valid():
            try:
                key = api.keys.create_or_update(user=request.user, **form.cleaned_data)
            except:
                logger.exception("Error saving key")
                return respond_json({'errorMsg': "Unknown error"})
            
            return respond_json(key.to_dict())
        return respond_json({'errorMsg': ajax_errors(form)})
    
    elif request.method == 'DELETE':
        key = api.keys.get(request.user, key)
        key.delete()
        return respond_json({'message': "key deleted"})
    
    raise HttpResponseNotAllowed()

@login_required
def group_details(request, group):
    group = api.groups.get(group)
    if not request.user.has_perm('read', obj=group):
        raise HttpResponseForbidden("You do not have access to this page.")
    
    return render_to_response('cannula/projectgroup_detail.html', 
        RequestContext(request, {
            'title': unicode(group),
            'group': group,
            'form': ProjectForm(),
            'now': datetime.datetime.now(),
            'logs': api.log.list(group=group)
        })
    )

@login_required
def project_details(request, group, project):
    group = api.groups.get(group)
    project = api.projects.get(project)
    if not request.user.has_perm('read', obj=group):
        raise HttpResponseForbidden("You do not have access to this page.")
    
    return render_to_response('cannula/project_detail.html', 
        RequestContext(request, {
            'title': unicode(project),
            'project': project,
            'now': datetime.datetime.now(),
            'logs': api.log.list(project=project)
        })
    )

@login_required
def manage_settings(request):
    if not request.user.is_superuser:
        raise HttpResponseForbidden("You do not have access to this page.")
    
    if request.method == "POST":
        form = SettingsForm(request.POST)
        if form.is_valid():
            write_config(form.cleaned_data)
            return HttpResponseRedirect('/')
    else:
        form = SettingsForm(initial=conf_dict())
    
    return render_to_response('cannula/form.html',
        RequestContext(request, {
            'form': form,
            'title': "Edit Settings",
        })
    )

def login(request):
    """Ajax Login Form"""
    
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            return respond_json({'message': "Login Successsful!"})
        else:
            return respond_json({'message': "Login Failed"}, status=400)
    
    raise HttpResponseNotAllowed()