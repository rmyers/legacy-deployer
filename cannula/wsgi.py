import webapp2
import logging
import json
import base64
import datetime
import time
import hmac
import hashlib
import urlparse
import re
from functools import wraps
from collections import defaultdict

from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor
from webapp2 import abort
from webapp2_extras import jinja2
from webapp2_extras import auth
from webapp2_extras import sessions
from webapp2_extras.security import generate_random_string

from cannula.gae.models import User

SIMPLE_TYPES = (int, long, float, bool, dict, basestring, list)

try:
    from secrets import *
except ImportError:
    SECRET_KEY = "foobar"


def to_dict(model, exclude=[]):
    """
    Stolen from stackoverflow: 
    http://stackoverflow.com/questions/1531501/json-serialization-of-google-app-engine-models
    """
    output = {}
    
    def encode(output, key, model):
        value = getattr(model, key)

        if value is None or isinstance(value, SIMPLE_TYPES):
            output[key] = value
        elif isinstance(value, datetime.date):
            # Convert date/datetime to ms-since-epoch ("new Date()").
            ms = time.mktime(value.utctimetuple())
            ms += getattr(value, 'microseconds', 0) / 1000
            output[key] = int(ms)
        elif isinstance(value, ndb.GeoPt):
            output[key] = {'lat': value.lat, 'lon': value.lon}
        elif isinstance(value, ndb.Model):
            output[key] = to_dict(value)
        else:
            raise ValueError('cannot encode property: %s', key)
        return output
    
    for key in model.to_dict().iterkeys():
        output = encode(output, key, model)
    
    if isinstance(model, ndb.Expando):
        for key in model._properties.iterkeys():
            output = encode(output, key, model)
    
    # remove any fields we don't want to display
    for f in exclude:
        if f in output:
            del output[f]

    return output




def auth_required(func):

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            if not self.auth.get_user_by_session():
                self.abort(401)
        except:
            self.auth.unset_session()
            self.abort(401)

        return func(self, *args, **kwargs)
    return wrapper


class API(webapp2.RequestHandler):
    
    endpoint = None
    model = None
    form = None
    exclude = []


    def options(self):
        """Be a good netizen citizen and return HTTP verbs allowed."""
        valid = ', '.join(webapp2._get_handler_methods(self))
        self.response.set_status(200)
        self.response.headers['Allow'] = valid
        return self.response.out

    @webapp2.cached_property
    def session_store(self):
        return sessions.get_store(request=self.request)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()
    
    @webapp2.cached_property
    def auth(self):
        return auth.get_auth()

    @webapp2.cached_property
    def user(self):
        return self.auth.get_user_by_session()

    @webapp2.cached_property
    def user_id(self):
        return str(self.user['user_id']) if self.user else None

    @webapp2.cached_property
    def jinja2(self):
        return jinja2.get_jinja2(app=self.app)
    
    def render(self, filename, context=None, **kwargs):
        if context is None:
            context = {}
        context.update(kwargs)
        self.response.write(self.jinja2.render_template(filename, **context))
    
    def parse_form(self, form=None):
        """Hook to run the validation on a form"""
        form = form or self.form
        if not form:
            raise AttributeError("Form object missing")
        
        # see how we were posted
        try:
            data = json.loads(self.request.body)
        except:
            # fall back to POST and GET args
            data = self.request.params

        return form(data)
    
    def base_url(self):
        return self.request.host_url + '/api/v1'
    
    def uri(self):
        return self.uri_for(self)
        if self.endpoint:
            return self.base_url() + self.endpoint
        #return self.base_url()
    
    def resource_uri(self, model):
        return '%s/%s' % (self.uri(), model.key.id())
    
    def serialize(self, model, exclude=[]):
        # Allow models to override the default to_dict
        if hasattr(self.model, 'serialize'):
            resp = self.model.serialize(model, exclude)
        else:
            resp = to_dict(model, exclude)
        resp['uri'] = self.resource_uri(model)
        resp['key'] = model.key.urlsafe()
        resp['id'] = model.key.id()
        return resp

    def fetch_model(self, key):
        # Test if the string is an actual datastore key first
        try:
            key = ndb.Key(urlsafe=key)
        except:
            abort(404)
            
        obj = key.get()
        if obj is None:
            abort(404)
        return self.respond_json(self.serialize(obj, self.exclude))

    def fetch_models(self):
        limit = int(self.request.get('limit', 100))
        cursor = self.request.get('cursor', None)
        order = self.request.get('order')
        filter_string = self.request.get('filter')
        
        query = self.model.query()
        
        if cursor:
            cursor = Cursor(urlsafe=cursor)
        
        # filter is ignored for apis that don't define 'handle_filter'
        if filter_string and hasattr(self, 'handle_filter'):
            query = self.handle_filter(query, filter_string)

        if order and hasattr(self, 'handle_order'):
            query = self.handle_order(query, order)
        
        models, next_cursor, more = query.fetch_page(limit, start_cursor=cursor)
        
        resp = {
            'limit': limit,
            'filter': filter_string,
            'cursor': next_cursor.urlsafe() if next_cursor else '',
            'uri': self.uri(),
            'models': [self.serialize(m, self.exclude) for m in models],
        }
        if more:
            resp['next'] = self.uri() + '?limit=%s&cursor=%s&filter=%s' % (limit, next_cursor.urlsafe(), filter_string)
        return self.respond_json(resp)
    
    def respond_json(self, message, status_code=200):
        self.response.set_status(status_code)
        self.response.headers['Content-type'] = 'application/json'
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        
        try:
            resp = json.dumps(message)
        except:
            self.response.set_status(500)
            resp = json.dumps({u'message': u'message not serializable'})
        
        return self.response.out.write(resp)


class APIRoutes(object):
    
    def __init__(self, prefix="/api/"):
        self.prefix = prefix
        self.routes = []
    
    def register(self, handler):
        if not hasattr(handler, 'model') or handler.model is None:
            logging.error("Unable to register %s", handler)
        
            


class StoreHandler(API):
    """Sentry EntryPoint Handler.
    
    This handles processing events sent by sentry compatable tools.
    """
    
    def post(self):
        obj = json.loads(base64.b64decode(self.request.body).decode('zlib'))
        logging.error(obj)


class IndexHandler(API):
    
    def get(self, *args, **kwargs):
        self.render('cannula/index.html', {'welcome': 'Home dude!'})

class UserHandler(API):
    
    model = User
    endpoint = 'user'
    excludes = ['password', 'auth_ids']
    
    def get(self, key=None):
        if key:
            return self.fetch_model(key)
        return self.fetch_models()

###
### Setup the routes for the API
###
routes = [
    webapp2.Route('/api/v1/user', UserHandler),
    webapp2.Route('/api/v1/user/<key:[\w=-]+>', UserHandler),
    webapp2.Route('/api/store/', StoreHandler),
    webapp2.Route('/<:.*>', IndexHandler),
] 

### 
### Application configuration
###
config = {
    'webapp2_extras.auth': {
        'user_model': 'cannula.gae.models.User',
        'cookie_name': 'cannula_session',
    },
    'webapp2_extras.sessions': {'secret_key': SECRET_KEY},
    'webapp2_extras.jinja2' : {
        'template_path': [
            'templates',
            'cannula/templates',
        ],
    }
}

# The Main Application
app = webapp2.WSGIApplication(routes)
