
from logging import getLogger

from django import http
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils.decorators import method_decorator
from django import forms

from cannula.api import DuplicateObject
from cannula.api import UnitDoesNotExist
from cannula.api import PermissionError
from cannula.api import ApiError
from cannula.api import BaseAPI
from cannula.conf import api, WORKER_CHOICES, VCS_CHOICES
from cannula import tasks
from cannula.utils import format_exception, validate_python_package_name, add_blank_choice

log = getLogger('api')

class CreateProject(forms.Form):
    group = forms.ChoiceField()
    name = forms.CharField(max_length=100,
        help_text="A free-form name for your project, e.g. 'Staff Time Sheets'.")
    abbr = forms.CharField(max_length=50,
        help_text="Python package name for your project, e.g. 'timesheets'.")
    repository = forms.CharField(max_length=512,
        help_text="URL of the repository for this project. This is the URL"
        " that you would 'clone' or 'checkout'")
    vcs = forms.ChoiceField(choices=VCS_CHOICES,
        help_text="Repository type.")
    requirements = forms.CharField(widget=forms.Textarea, required=False,
        help_text="Requirements for this project, overrides project or repository defaults")
    settings = forms.CharField(widget=forms.Textarea, required=False,
        help_text="Settings for this project, overrides project or repository defaults. "
        "Depending on the project type this will be written out differently.")
    desc = forms.CharField(max_length=1024, required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text="(Optional) Description of this project.")


    def __init__(self, *args, **kwargs):
        """
        Dynamically populate the env and stage choices.
        """
        self.username = kwargs.pop('username')
        super(CreateProject, self).__init__(*args, **kwargs)

        groups = api.groups.list(self.username)
        group_choices = [(g.abbr, '%s (%s)' % (g.name, g.abbr)) for g in groups]
        group_choices = add_blank_choice(group_choices)
        self.fields['group'].choices = group_choices

    def clean_name(self):
        name = self.cleaned_data['name']
        if name:
            name = name.strip()
        return name

    def clean_abbr(self):
        abbr = self.cleaned_data['abbr']
        validate_python_package_name(abbr)
        try:
            api.projects.get(self.cleaned_data['group'], abbr)
            raise forms.ValidationError(u'A project with this name already exists in this group.')
        except UnitDoesNotExist:
            pass
        return abbr

class DeleteProject(forms.Form):
    """
    Form displayed when deleting project to make sure the user confirms project
    deletion.  This form will delete actually delete the project when is_valid
    is called if all the fields are error-free.
    """
    required_text = ("You must confirm this statement in order to delete this"
                     " project.")

    confirm_delete = forms.BooleanField(label='Delete this project',
        help_text="By clicking this box, you confirm that this project will be"
                  " deleted from the interface and that this project's"
                  " associated repository will also be deleted.",
        error_messages={'required': required_text})
    confirm = forms.BooleanField(label='Delete data',
        help_text="By clicking this box you confirm that this deletion is an"
                  " irreversible action, and that your code and data will be"
                  " permanently deleted.  You confirm that you have made any"
                  " necessary backups of your data from the project's"
                  " repository.",
        error_messages={'required': required_text})


class DeployProject(forms.Form):
    cluster = forms.ChoiceField(widget=forms.RadioSelect,
        help_text="Select a stage to deploy this application to.")
    repo_path = forms.CharField(label="Repo Path", initial='',
        help_text="Enter the path within your repository you would like to"
                  " deploy (including your project directory)."
                  " SVN Examples: /trunk/myproj, /tags/1.0/myproj,"
                  " GIT/HG Examples: master, mybranch, tip, default")
    revision = forms.CharField(max_length=25, required=False,
        help_text="Enter the revision number to deploy, or leave blank to"
                  " deploy the latest revision.")
    requirements = forms.CharField(widget=forms.Textarea, required=False,
        help_text="Requirements for this project, overrides project or repository defaults")
    settings = forms.CharField(widget=forms.Textarea, required=False,
        help_text="Settings for this project, overrides project or repository defaults. "
        "Depending on the project type this will be written out differently.")

    
    def __init__(self, *args, **kwargs):
        """
        Dynamically populate the env and stage choices.
        """
        self.username = kwargs.pop('username')
        super(DeployProject, self).__init__(*args, **kwargs)

        clusters = api.clusters.list(self.username)
        choices = [(stage.abbr, stage) for stage in clusters]
        self.fields['cluster'].choices = choices
        

class ProjectAPIBase(BaseAPI):
    
    details_template = ['cannula/project_details.html']
    deploy_template = ['cannula/form.html']
    delete_template = ['cannula/form.html']
    create_template = ['cannula/form.html']
    list_template = ['cannula/project.html']
    
    create_form = CreateProject
    delete_form = DeleteProject
    deploy_form = DeployProject
    
    def _get(self, group, projectname):
        "Subclasses must define this"
        raise NotImplementedError()
    
    
    def get(self, groupname, projectname):
        group = api.groups.get(groupname)
        try:
            return self._get(group, projectname)
        except:
            raise UnitDoesNotExist("Project does not exist")
    
    
    def _list(self, user=None, group=None):
        "Subclasses must define this"
        raise NotImplementedError()
    
    
    def list(self, user=None, group=None):
        """
        Return a list of Project units for the ProjectGroup with the given
        groupname.

        Required Arguments:

         * user: (String) EID of the the user doing the query.
         * group: (String) Name of project group.
        """
        if user:
            user = api.users.get(user)
            # TODO: return list of projects user has access to?
        if group:
            group = api.groups.get(group)
            
        return self._list(user, group)
    
    
    def _create(self, group, abbr, name, requirements, settings):
        "Subclasses must define this"
        raise NotImplementedError()
    
    
    def create(self, user, group, abbr, requirements='', settings='',
               name=None, desc='', perm='create', **kwargs):
        """
        Create a project and return its project object.

        This requires permission to create project in the group and  a unique
        string identifier for the project.  If the project is not unique, a
        DuplicateObject Exception is raised.

        Required Arguments:

         * user: (String) User attempting the create function.
         * group: (String) Name of project group to put project under.
         * abbr: (String) Name of project to create.

        Optional Arguments:

         * name: A long name for the project.
         * desc: Text description of the project.

        Returns:

         On successful create:
           The newly created project object

         On failure:
           Exception
        """
        user = api.users.get(user)
        group = api.groups.get(group)
        if not api.permissions.has_perm(user, perm, group=group):
            raise PermissionError("User: %s does not have perm: %s" % (user, perm))

        # Check group members and remove inactive ones so we don't get errors
        # from UTForge when granting members permission after the project gets
        # created.
        api.groups.check_members(group, user)

        # Ensure the Python package name (abbr) doesn't already exist.
        try:
            self.get(group, abbr)
            raise DuplicateObject("This project already exists in this group.")
        except UnitDoesNotExist:
            pass

        if name is None:
            name = abbr

        # Create the Project object.
        project = self._create(group=group,
            name=name,
            abbr=abbr,
            desc=desc,
            settings=settings,
            requirements=requirements,
        )

        log.info("Project %s created in %s" % (project, group))
        return project
    
    
    def deploy(self, req_user, group, project, cluster=None, url='/',
               requirements='', settings='', repo_path=''):
        """
        Deploy this project to a given cluster using the deployment method
        chosen. If this is the first deployment of this project first sync the
        cluster.
        """
        req_user = api.users.get(req_user)
        group = api.groups.get(group)
        project = self.get(group, project)
        cluster = api.clusters.get(cluster)

        try:
            # check if we are already deployed.
            current = api.deployments.get(group, project, cluster)
            message = "Updated deployment: %s @ %s to %s @ %s" % (
                    current.repo_path, current.revision,
                    repo_path, revision)
            # mark it as in-active so we don't get errors
            current.active = False
            current.save()
        except UnitDoesNotExist:
            # First deployment of this project on this cluster.
            current = None
            message = "Initial deployment: %s" % repo_path

        deployment = api.deployments.create(group, project, cluster, url,
                        package, repo_path, revision, current)

        # Deploy the project
        try:
            tasks.deploy_project.delay(group.abbr, project.abbr, cluster.name)
        except:
            message = "Failed to deploy project, " \
                      "group: %s, project: %s" % (group, project)
            log.error(message)
            log.error(format_exception())
            tasks.delete_deployment(deployment.id)
            deployment.delete()
            raise

        log.info("%s by %s" % (message, req_user))
        api.log.create(message=message, user=req_user, group=group, 
                       project=project, cluster=cluster)
        return deployment
    
    
    def delete(self, group, project, user):
        group = api.groups.get(group)
        project = api.projects.get(group, project)
        user = api.users.get(user)

        deployments = api.deployments.list(group, project)
        for deploy in deployments:
            deploy.delete_deployment()
            deploy.delete()

        try:
            connection = project.repo.server.connect()
            with connection:
                connection.delete_project(project.repo.url, user.username)
        except:
            log.error("Problem deleting project: %s" % project)
            raise

        unix_ids = api.unix_ids.list(group, project)
        for uid in unix_ids:
            log.info("Unsyncing Unix ID: %s" % uid)
            uid.unsync()

        project.delete()
        message = "%s deleted project %s from group %s" % (user, project, group)
        log.info(message)
        api.log.create(message, user=user, group=group)

    
    @method_decorator(login_required)
    def details_view(self, request, group, project):
        """
        List the deployments and their statuses for a single project.
        """
        group = api.groups.get_or_404(group)
        project = self.get_or_404(group, project)
        if not request.user.has_perm('read', group):
            return http.HttpResponseForbidden("<h1>Forbidden</h1>")
    
        page = request.GET.get('page', '1')
        apps = api.deployments.list(group, project, active_only=True)
        is_admin = request.user.is_superuser
        context = {
            'title': "%s Deployments" % project,
            'applications': apps,
            'project': project,
            'group': group,
            'has_deploy_permission': True,
            'is_admin': is_admin,
            'logs': api.log.list(group, project, page=page),
        }
        return self.respond(request, self.details_template, context)
    
    @method_decorator(login_required)
    @transaction.commit_on_success
    def deploy_view(self, request, group, project):
        """
        Display/process form for deploying a project to a cluster.
        """
        group = api.groups.get_or_404(group)
        project = self.get_or_404(group, project)
        if not request.user.has_perm('deploy', project):
            log.debug('403: %s attempted to deploy %s.%s' % (request.user, group.abbr, project.abbr))
            return http.HttpResponseForbidden('<h1>Forbidden</h1>')
    
        errors = False
        add = True
        app_info = {}
        title = "Add Deployment"
    
        if request.method == "POST":
            form = self.deploy_form(request.POST, username=request.user.username)
            if form.is_valid():
                #TODO: hook url up!
                self.deploy(request.user, group, project, url=None,
                            **form.cleaned_data)
                message = "%s successfully deployed." % project
                log.debug(message)
                request.session['message'] = message
                return http.HttpResponseRedirect('../')
            errors = True
        else:
            cluster = request.GET.get('cluster')
            # If a cluster was specified, then we are updating an existing
            # deployment and want to pre-fill the form with the existing data.
            if cluster:
                # Check that a valid cluster was specified.
                try:
                    cluster = api.clusters.get(cluster)
                except UnitDoesNotExist:
                    return http.HttpResponseBadRequest('Invalid cluster name.')
                if cluster not in api.clusters.list(request.user):
                    return http.HttpResponseBadRequest('Invalid cluster name.')
                add = False
                deployment = api.deployments.get(group, project, cluster)
                app_info = {
                    'cluster_name': cluster.abbr,
                    'repo_path': deployment.repo_path,
                    'revision': deployment.revision,
                    'env': deployment.package.pk,
                    'processes': deployment.num_processes,
                }
                title = "Update %s Deployment" % cluster
            form = self.deploy_form(initial=app_info, username=request.user.username)

        context = {
            'form': form,
            'title': title,
            'errors': errors,
            'project': project,
            'group': group,
            'add': add,
        }
        return self.respond(request, self.deploy_template, context)
    
    @method_decorator(login_required)
    @transaction.commit_on_success
    def delete_view(self, request, group, project):
        """
        Display/process delete confirmation form.
        """
        group = api.groups.get_or_404(group)
        project = api.projects.get_or_404(group, project)
        if not request.user.has_perm('admin', project):
            log.debug('403: %s attempted to delete %s.%s' % (
                request.user, group.abbr, project.abbr)
            )
            return http.HttpResponseForbidden('<h1>Forbidden</h1>')
    
        errors = False
        if request.method == 'POST':
            form = self.delete_form(data=request.POST)
            if form.is_valid():
                # Delete the project
                self.delete(group, project, request.user)
                request.session['message'] = "Project %s deleted." % project
                return http.HttpResponseRedirect(reverse('cannula-index'))
            errors = True
        else:
            form = self.delete_form()
        context = {
            'title': "Delete Project %s" % project,
            'form': form,
            'add': False,
            'errors': errors,
            }
        return self.respond(request, self.delete_template, context)

    @method_decorator(login_required)
    @transaction.commit_manually
    def create_view(self, request):
        errors = False
        if request.method == "POST":
            form = self.create_form(data=request.POST, username=request.user)
            if form.is_valid():
                try:
                    self.create(request.user, **form.cleaned_data)
                    request.session['message'] = "Project successfully created."
                    transaction.commit()
                    return http.HttpResponseRedirect(reverse('cannula-index'))
                except Exception as create_exception:
                    log.error("Error creating project, group: %s project: %s"
                              % (group, abbr))
                    log.error(format_exception())
                    transaction.rollback()
                    # Explicitly specify the original exception instance here in
                    # case the repo deletion also raises an exception.
                    raise create_exception
            errors = True
        else:
            # Allow group to be passed as GET parameter, used for groups creating
            # their first project from the home page.
            initial = {'group': request.GET.get('group', '')}
            form = self.create_form(initial=initial, username=request.user)
        context = {
            'title': "Add Project",
            'form': form,
            'cancel_url': reverse('cannula-index'),
            'errors': errors,
            'add': True,
        }
        return self.respond(request, self.create_template, context)

    @method_decorator(login_required)
    def list_view(self, request):
        """
        Display a list of projects.
        """
        projects = self.list()
        context = {
            'title': "Projects",
            'projects': projects,
            'count': len(projects),
        }
        return self.respond(request, self.list_template, context)