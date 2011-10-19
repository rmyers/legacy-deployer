from datetime import datetime

from django.db import models
from django.contrib.auth.models import User, Group

class ProjectGroup(models.Model):
    """
    Project Group

    Collection of projects that users have access to. 
    Users can belong to multiple groups. But usually there is one 
    group per department.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    members = models.ManyToManyField(User, through="GroupMembership")
    date_created = models.DateField(default=datetime.now)
    
    def __unicode__(self):
        return self.name
    
class GroupMembership(models.Model):
    """
    Many to Many relationship for the Project Group membership. This holds a
    little information about the user, such as the date added and the
    permission level they have.
    """
    user = models.ForeignKey(User)
    group = models.ForeignKey(ProjectGroup)
    can_add = models.BooleanField(default=False, blank=True)
    can_delete = models.BooleanField(default=False, blank=True)
    can_modify = models.BooleanField(default=False, blank=True)
    date_joined = models.DateField(default=datetime.now)
    
    def __unicode__(self):
        return self.group.name
    
class Project(models.Model):
    
    name = models.CharField(max_length=255, unique=True, db_index=True)
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