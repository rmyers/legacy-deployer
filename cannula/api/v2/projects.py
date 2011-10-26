
from logging import getLogger

from django.db.models.loading import get_model

from cannula.api import DuplicateObject
from cannula.api import UnitDoesNotExist
from cannula.api import PermissionError
from cannula.api import BaseAPI
from cannula.conf import api

Project = get_model('cannula', 'project')


log = getLogger('api')

class ProjectAPI(BaseAPI):

    
    def _get(self, projectname):
        if isinstance(projectname, Project):
            return projectname
        return Project.objects.get(name=projectname)
     
    
    def _list(self, user=None, group=None):
        # TODO: handle user arg?
        if group:
            return group.project_set.all()
        return Project.objects.all()
    
    
    def _create(self, group, abbr, name, desc):
        project, created = Project.objects.get_or_create(group=group, name=name, 
            defaults={'desc':desc})
        if not created:
            raise DuplicateObject("Project already exists!")
        return project
    
    def create(self, user, group, name, desc=''):
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
        project = self._create(group=group,name=name,desc=desc)

        log.info("Project %s created in %s" % (project, group))
        return project