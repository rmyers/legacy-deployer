
from protorpc import messages

class User(messages.Message):
    
    username = messages.StringField(1, required=True)
    email = messages.StringField(2)
    first_name = messages.StringField(3)
    last_name = messages.StringField(4)
    password = messages.StringField(5)
    is_admin = messages.BooleanField(default=False)

   

class Project(messages.Message):
    
    name = messages.StringField(1, required=True)
    group = messages.StringField(2, requied=True)
    description = messages.StringField(3)
    created = messages.IntegerField(4)

class Group(messages.Message):
    
    name = messages.StringField(1, required=True)
    projects = messages.MessageField(Project, 2, repeated=True)
    description = messages.StringField(3)
    created = messages.IntegerField(4)
    members = messages.MessageField(User, 5, repeated=True)

class GroupMembership(messages.Message):
    
    group_name = messages.StringField(1, required=True)
    username = messages.StringField(2, required=True)
    add = messages.BooleanField(3, default=False)
    modify = messages.BooleanField(4, default=False)
    delete = messages.BooleanField(5, default=False)


    