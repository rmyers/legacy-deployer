import posixpath
import logging

from django import http
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django import forms
from django.views.decorators.http import require_POST
from django.utils import simplejson
from django.utils.decorators import method_decorator

from cannula.api import DuplicateObject
from cannula.api import UnitDoesNotExist
from cannula.api import PermissionError
from cannula.api import ApiError
from cannula.api import BaseAPI
from cannula.conf import api

log = logging.getLogger('api')

class DeleteDeployment(forms.Form):
    """
    Form displayed when deleting a deployed project (application) from a stage.
    User must confirm deletion.  This form will actually delete the application
    when is_valid is called if all the fields are error-free.
    """
    required_text = ("You must confirm this statement in order to delete this"
                     " deployment.")

    confirm_delete = forms.BooleanField(label='Delete this deployment',
        help_text="By clicking this box, you confirm that this deployment will"
                  " be deleted from the interface and that the server"
                  " process serving the project will be stopped.",
        error_messages={'required': required_text})

class DeploymentAPIBase(BaseAPI):
    
    change_template = 'cannula/form.html'
    delete_template = 'cannula/form.html'
    modify_permission = 'deploy'
    
    delete_form = DeleteDeployment
    
    def _get(self, group, project, cluster):
        """Subclasses must define this."""
        raise NotImplementedError()
    
    
    def get(self, group, project, cluster):
        group = api.groups.get(group)
        project = api.projects.get(group, project)
        cluster = api.clusters.get(cluster)
        try:
            return self._get(group, project, cluster)
        except:
            raise UnitDoesNotExist("Deployment not found")
    
    
    def _list(self, group, project, cluster, active_only, inactive_only):
        """Subclasses must define this."""
        raise NotImplementedError()
    
    
    def list(self, group, project, cluster=None, active_only=False, inactive_only=False):
        if active_only and inactive_only:
            raise ApiError("Can not list active_only and inactive_only together")
        group = api.groups.get(group)
        project = api.projects.get(group, project)
        if cluster:
            cluster = api.clusters.get(cluster)
        
        return self._list(group, project, cluster, active_only, inactive_only)
    
    
    def _get_num_processes(self, cluster, strategy, deployment=None,
                           override=None):
        """
        Return the number of processes that should be used for a deployment.

        If given, override will be used.  If a deployment is passed, then
        return the number of processes that deployment was using.  Otherwise,
        let the deployment strategy determine the number of processes that
        should be used based on the cluster.
        """
        if override is not None:
            return override
        if deployment:
            return deployment.num_processes
        else:
            return strategy.num_processes(cluster)
        
    
    def _create(self, group, project, cluster, url, package,
               repo_path, revision=None, current=None):
        """Subclasses must define this."""
        raise NotImplementedError()
    
    
    def create(self, group, project, cluster, url, package,
               repo_path, revision=None, current=None):
        """
        Return a new Deployment object based on the given parameters.
        
        * repo_path: SVN path or Git branch, etc.
        * revision: Repo revision
        * processes: Number of processes to start.
        * current: The current deployment if any.
        """
        group = api.groups.get(group)
        project = api.projects.get(group, project)
        cluster = api.clusters.get(cluster)
        package = api.packages.get(package)
        # We need the project directory on the repo_path in order to
        # check it out properly.
        if project.abbr not in repo_path:
            repo_path = posixpath.join(repo_path, project.abbr)
        if not revision:
            # get the latest revision.
            revision = project.repo.head()
        
        return self._create(group, project, cluster, url, package, 
                           repo_path, revision, current)
    
    
    def delete(self, user, group, project, cluster):
        """
        Delete the deployment of this application and cleanup
        the files settings of the deployment method.

        If this is the last deployment of this project and group
        do some more clean up on the deploy host.
        """
        user = api.users.get(user)
        group = api.groups.get(group)
        project = api.projects.get(group, project)
        cluster = api.clusters.get(cluster)

        deployment = self.get(group, project, cluster)
        try:
            deployment.delete_deployment()
            deployment.delete()
        except Exception, e:
            log.error("Deployment deletion failed: %s" % e)
            raise
        message = "%s Deleted deployment for %s on %s" % (user, project, cluster)
        log.info(message)
        self.log(message="Deleted deployment",
                user=user, group=group, project=project, cluster=cluster)

    
    def modify(self, user, group, project, cluster, action, **kwargs):
        """
        Modify existing deployment current actions include:

        * 'start': Starts a stopped deployment.
        * 'stop': Rewrites WSGI file for deployment to a maintenance message.
        * 'restart': Restarts the deployment processes.
        * 'migrate': Migrate the deployment to another tools version.
        """
        user = api.users.get(user)
        group = api.groups.get(group)
        project = api.projects.get(group, project)
        cluster = api.clusters.get(cluster)
        if not user.has_perm(self.modify_permission, project):
            raise PermissionError

        deployment = self.get(group, project, cluster)
        try:
            deployment.modify_deployment(action, user, **kwargs)
        except InvalidAction:
            raise
        except Exception, e:
            log.error("Deployment modification failed: %s" % e)
            raise
        message = ("%s executed '%s' action on %s.%s in %s"
                   % (user, action, group.abbr, project.abbr, cluster))
        log.info(message)
        # The individual actions write the logs to the DB.
        return deployment

    @method_decorator(require_POST)
    @method_decorator(login_required)
    @transaction.commit_on_success
    def modify_view(self, request, group, project, cluster):
        """
        Control an application's state (start, stop, restart).
        """
        action = request.POST.get('action')
        data = {'action': action}        
        try:
            deployment = self.modify(request.user, group, project, cluster, action)
        except UnitDoesNotExist:
            raise http.Http404
        except PermissionError:
            log.debug('403: %s attempted to control %s.%s' % (request.user, group.abbr, project.abbr))
            return http.HttpResponseForbidden('<h1>Forbidden</h1>')
        except InvalidAction:
            if request.is_ajax():
                data.update({'message': "Invalid action"})
                return http.HttpResponse(simplejson.dumps(data), status=200)
            return http.HttpResponseBadRequest('Invalid action.')
        except InvalidStatus:
            if request.is_ajax():
                data.update({'message': "Invalid status for this action"})
                return http.HttpResponse(simplejson.dumps(data), status=200)
            return http.HttpResponseBadRequest('Invalid status for this action.')
        except:
            if request.is_ajax():
                data.update({'message': "There was a problem running this action."})
                return http.HttpResponse(simplejson.dumps(data), status=200)
            raise

        project_log = api.log.get(group, project, cluster)
        msg = "%s for %s on cluster %s" % (project_log.message, project, cluster)
        if request.is_ajax():
            data = {'message': msg,
                    'status': deployment.status,
                    'action': action,
                    'last_update': unicode(project_log)}
            try:
                resp = simplejson.dumps(data)
                status = 200
            except:
                resp = simplejson.dumps({'message': "There was a problem running this action."})
                status = 500
            return http.HttpResponse(resp, status=status)
        request.session['message'] = msg
        return http.HttpResponseRedirect('../')
  
    @method_decorator(login_required)
    @transaction.commit_on_success
    def delete_view(self, request, group, project, cluster):
        """
        Display/process confirmation form for deleting a deployed project
        (application) from a cluster, which will result in deleting the application's
        units and files from the server.
        """
        group = api.groups.get_or_404(group)
        project = api.projects.get_or_404(group, project)
        cluster = api.clusters.get_or_404(cluster)
        if not request.user.has_perm('deploy', project):
            log.debug('403: %s attempted to delete deployment %s.%s' % (
                request.user, group.abbr, project.abbr)
            )
            return http.HttpResponseForbidden('<h1>Forbidden</h1>')
    
        errors = False
        if request.method == 'POST':
            form = self.delete_form(data=request.POST)
            if form.is_valid():
                self.delete(request.user, group, project, cluster)
                request.session['message'] = "%s deployment deleted." % cluster.name
                return http.HttpResponseRedirect(
                    reverse('project-details', args=[group.abbr, project.abbr]))
            errors = True
        else:
            form = self.delete_form()
        context = {
            'title': "Delete %s deployment of project %s" % (cluster, project),
            'form': form,
            'add': False,
            'project': project,
            'group': group,
            'errors': errors,
            }
        return self.respond(request, self.delete_template, context)
