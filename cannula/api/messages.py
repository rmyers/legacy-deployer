
from protorpc import messages

class User(messages.Message):
    
    name = messages.StringField(1, required=True)
    email = messages.StringField(2)
    

class Project(messages.Message):
    
    name = messages.StringField(1, required=True)

    