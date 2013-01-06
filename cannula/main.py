from tastypie.resources import ModelResource
from tastypie.resources import ALL
from tastypie.resources import ALL_WITH_RELATIONS
from tastypie.authentication import SessionAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie import fields

from django.contrib.auth.models import User

from cannula.models import Key

class UserResource(ModelResource):
    
    class Meta:
        queryset = User.objects.all()
        authentication = SessionAuthentication()
        authorization = DjangoAuthorization()

    def gravatar(self, email):
        """Return a link to gravatar image."""
        url = 'http://www.gravatar.com/avatar/%s?s=48'
        from hashlib import md5
        email = email.strip().lower()
        hashed = md5(email).hexdigest()
        return url % hashed

    def dehydrate(self, bundle):
        email = bundle.data.pop('email')
        bundle.data['picture_url'] = self.gravatar(email)
        return bundle

class KeyResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user', full=True)
    
    class Meta:
        queryset = Key.objects.all()
        filtering = {
            'user': ALL_WITH_RELATIONS,
        }
        