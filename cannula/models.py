from django.db import models
from django.contrib.auth.models import User, Group

class ProjectGroup(models.Model):
    
    owner = models.ForeignKey(User)
    group = models.ForeignKey(Group)
    
    def __unicode__(self):
        return self.group.name


class Project(models.Model):
    
    name = models.CharField(max_length=255, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User,
        help_text="User who created the project.")
    group = models.ForeignKey(ProjectGroup, null=True, blank=True,
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
    twitter = models.CharField(max_length=255, blank=True)
    facebook = models.CharField(max_length=255, blank=True)
    ssh_keys = models.ManyToManyField(Key)
    
    def __unicode__(self):
        return self.user