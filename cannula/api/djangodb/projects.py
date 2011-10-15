
from logging import getLogger

from django.db.models.loading import get_model

from cannula.api.base.projects import ProjectAPIBase

Project = get_model('cannula', 'project')


log = getLogger('api')

class ProjectAPI(ProjectAPIBase):

    
    def _get(self, group, projectname):
        if isinstance(projectname, Project):
            return projectname
        return Project.objects.get(group=group, abbr=projectname)
     
    
    def _list(self, user=None, group=None):
        # TODO: handle user arg?
        if group:
            return group.project_set.all()
        return Project.objects.all()
    
    
    def _create(self, group, abbr, name, desc, requirements, settings):
        "Subclasses must define this"
        project = Project.objects.create(group=group,
            name=name, abbr=abbr, desc=desc, requirements=requirements, settings=settings)
        return project