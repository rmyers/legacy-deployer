from django.db import models
from django.contrib.auth.models import User, Group

class ProjectGroup(models.Model):
    
    owner = models.ForeignKey(User)
    group = models.ForeignKey(Group)
    
    def __unicode__(self):
        return self.group


class Project(models.Model):
    
    name = models.CharField(max_length=255, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User,
        help_text="User who created the project.")
    group = models.ForeignKey(ProjectGroup, required=False,
        help_text="(Optional) group that has access.")

    def __unicode__(self):
        return self.name

class Key(models.Model):
    
    name = models.CharField(max_length=255)
    ssh_key = models.TextField()
    
    def __unicode__(self):
        return self.name

class Profile(models.Model):
    
    user = models.ForeignKey(User)
    twitter = models.CharField(max_length=255, required=False)
    facebook = models.CharField(max_length=255, required=False)
    ssh_keys = models.ManyToManyField(Keys)
    
    def __unicode__(self):
        return self.user