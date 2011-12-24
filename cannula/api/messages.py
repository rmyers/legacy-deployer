
import os

class User(object):
    
    def __init__(self, name, email=None, first_name=None,
        last_name=None, password=None, is_admin=False):
        self.name = name
        self.email = email or '%s@localhost.com' % name
        self.first_name = first_name
        self.last_name = last_name
    
    @property
    def location(self):
        return os.path.join('/balh', self.name)
    
#class Project(messages.Message):
#    
#    name = messages.StringField(1, required=True)
#    group = messages.StringField(2, requied=True)
#    description = messages.StringField(3)
#    created = messages.IntegerField(4)
#
#class Group(messages.Message):
#    
#    name = messages.StringField(1, required=True)
#    projects = messages.MessageField(Project, 2, repeated=True)
#    description = messages.StringField(3)
#    created = messages.IntegerField(4)
#    members = messages.MessageField(User, 5, repeated=True)
#
#class GroupMembership(messages.Message):
#    
#    # group:username
#    name = messages.StringField(1, required=True)
#    group_name = messages.StringField(2, required=True)
#    username = messages.StringField(3, required=True)
#    add = messages.BooleanField(4, default=False)
#    modify = messages.BooleanField(5, default=False)
#    delete = messages.BooleanField(6, default=False)
#
#class Deployment(messages.Message):
#    
#    project = messages.StringField(1, required=True)
#    username = messages.StringField(2, required=True)
#    old_deploy_rev = messages.StringField(3)
#    new_deploy_rev = messages.StringField(4)
#    old_conf_rev = messages.StringField(5)
#    timestamp = messages.IntegerField(6)
    