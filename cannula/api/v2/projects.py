import os

from logging import getLogger

from django.db.models.loading import get_model

from cannula.api import DuplicateObject
from cannula.api import UnitDoesNotExist
from cannula.api import PermissionError
from cannula.api import BaseAPI
from cannula.conf import api, CANNULA_GIT_CMD
from cannula.utils import write_file

Project = get_model('cannula', 'project')

log = getLogger('api')

class ProjectAPI(BaseAPI):
    # TODO: wire up using different users
    useradd_cmd = '/usr/sbin/useradd %(options)s %(name)s'
    userdel_cmd = '/usr/sbin/userdel -r %(name)s'
    userget_cmd = '/bin/grep ^%(name)s: /etc/passwd'
    git_init_cmd = '%(git_cmd)s init --bare %(repo)s'

    
    def _get(self, projectname):
        if isinstance(projectname, Project):
            return projectname
        try:
            return Project.objects.get(name=projectname)
        except Project.DoesNotExist:
            raise UnitDoesNotExist("Project does not exist") 
    
    def get(self, projectname):
        return self._get(projectname)
    
    def _list(self, user=None, group=None):
        # TODO: handle user arg?
        if group:
            return group.project_set.all()
        return Project.objects.all()
    
    
    def _create(self, group, name, description):
        project, created = Project.objects.get_or_create(group=group, name=name, 
            defaults={'description':description})
        if not created:
            raise DuplicateObject("Project already exists!")
        return project
    
    def create(self, user, group, name, description=''):
        """
        Create a project and return its project object.

        This requires permission to create project in the group and  a unique
        string identifier for the project.  If the project is not unique, a
        DuplicateObject Exception is raised.

        Required Arguments:

         * user: (String) User attempting the create function.
         * group: (String) Name of project group to put project under.
         * name: (String) Name of project to create.

        Optional Arguments:

         * desc: Text description of the project.

        Returns:

         On successful create:
           The newly created project object

         On failure:
           Exception
        """
        user = api.users.get(user)
        group = api.groups.get(group)
        
        if not user.has_perm('add', group):
            raise PermissionError("You can not create projects in this group")

        # Create the Project object.
        project = self._create(group=group,name=name,description=description)
        log.info("Project %s created in %s" % (project, group))
        api.log.create("Project %s created" % project, user=user, group=group)
        self.initialize(project, user)
        return project
    
    
    def initialize(self, name, user):
        """
        Utility to create a project on the filesystem.
        
        #. Create a unix user for the project.
        #. Create home directory for code.
        #. Create a bare git repository for code.
        
        """
        from cannula.utils import shell
        project = self.get(name)
        user = api.users.get(user)
        
        if not user.has_perm('add', project.group):
            raise PermissionError("You can not create projects in this group")
        
        # TODO: Create unix user for project
        
        log.info("Creating project directories for: %s", project)
        if not os.path.isdir(project.repo_dir):
            os.makedirs(project.repo_dir)
        
        if not os.path.isdir(project.project_dir):
            os.makedirs(project.project_dir)
        
        # Create the git repo
        args = {
            'git_cmd': CANNULA_GIT_CMD,
            'repo': project.repo_dir
        }
        shell(self.git_init_cmd % args)
        
        ctx = {'project': project}
        # Update git config in new repo
        write_file(project.git_config, 'git/git-config.txt', ctx)
        # Write out post-recieve hook
        write_file(project.post_receive, 'git/post-receive.sh', ctx)
        # Write out a description file
        write_file(project.git_description, 'git/description.txt', ctx)
        
        log.info("Project %s initialized", project)
        api.log.create("Project %s initialized" % project, user=user, group=project.group)