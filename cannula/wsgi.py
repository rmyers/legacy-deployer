import base64
import datetime
from functools import wraps
import json
import logging
import re
import time
from urlparse import urljoin

from google.appengine.api.datastore_errors import Error, BadValueError
from google.appengine.api import namespace_manager
from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext import ndb
import webapp2
from webapp2_extras import jinja2
from webapp2_extras import auth
from webapp2_extras import sessions
from webapp2_extras.security import generate_random_string

from cannula.gae.models import User, Project, SSHKey, Group, Account

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


def generate_csrf():
    csrf = generate_random_string(length=32)
    return base64.b64encode(csrf)


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


def parameter(name, _type, required=True, default=None):
    """Decorator to handle POST/GET parsing into kwargs."""
    
    def inner(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            value = self.request.get(name, default)
            if not value and required:
                msg = {
                    'message': u'Missing required argument: %s' % name
                }
                return self.respond_json(msg, 400)
            try:
                value = _type(value)
            except Exception, e:
                return self.respond_json({'message': unicode(e.message)}, 400)
            kwargs[name] = value
            return func(self, *args, **kwargs)
        return wrapper
    return inner
                

def cast_int(items):
    """Turn the list of items into integers if possible.
    
    >>> t = cast_int(['1', '2', 'abc'])
    >>> print t
    [1, 2, 'abc']
    """
    def cast(arg):
        try:
            return int(arg)
        except ValueError:
            return arg
    
    return map(cast, items)
        


class BaseHandler(webapp2.RequestHandler):
    
    csrf_exempt = False
    
    def __init__(self, request, response):
        response.set_cookie('XSRF-TOKEN', generate_random_string(length=32))
        self.initialize(request, response)

    def dispatch(self):
        """Custom dispatch to handle CSRF protection."""
        is_post = self.request.method in ['POST', 'PUT', 'DELETE']
        # Allow handlers to exempt themselves
        if not self.csrf_exempt and is_post:
            token = self.request.cookies.get('XSRF-TOKEN', None)
            req_token = self.request.headers.get('X-XSRF-TOKEN', None)
            logging.info("xsrf check: %s = %s", token, req_token)
            if not all([token, req_token, token == req_token]):
                logging.error("xsrf failure: %s != %s", token, req_token)
                self.abort(403)

        try:
            # Dispatch the request.
            namespace = self.session.get('namespace', '')
            namespace_manager.set_namespace(namespace)
            logging.info('Using namespace: %s', namespace or 'global')
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)
    
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
        
    def render(self, filename, context=None, **kwargs):
        if context is None:
            context = {}
        context.update(kwargs)
        self.response.write(self.jinja2.render_template(filename, **context))


class APIMeta(type):
    """API Metaclass, used to handle url registration."""
    
    def __new__(cls, name, bases, dct):
        parent = dct.get('parent')
        # Our Children
        dct['_children'] = []
        # The depth this api is at.
        dct['_depth'] = 0
        this = super(APIMeta, cls).__new__(cls, name, bases, dct)
        if parent is not None:
            parent._children.append(this)
            this._depth = parent._depth + 1
        return this
    

class API(BaseHandler):
    """API Handler"""
    
    __metaclass__ = APIMeta
    
    # Override the default endpoint of self.model._get_kind()
    endpoint = None
    # The main model of this API
    model = None
    # Parent handler, used in ancestor query and urls
    parent = None
    # exclude fields from serialize method
    exclude = []
    # get regex for getting a single resource
    get_var = '<:[\w:=-]+>'

    def options(self):
        """Be a good netizen and return HTTP verbs allowed."""
        valid = ', '.join(webapp2._get_handler_methods(self))
        self.response.set_status(200)
        self.response.headers['Allow'] = valid
        return self.response.out
    
    @classmethod
    def kind(cls):
        if cls.endpoint:
            return cls.endpoint
        if cls.model is None:
            raise AttributeError("Either 'endpoint' or 'model' must be set.")
        # Get the kind from the model
        return cls.model._get_kind()
    
    @classmethod
    def url_pattern(cls, for_prefix=False):
        """Return the url for the route builder.
        
        Example::
        
            >>> SubHandler.url_pattern()
            '/api/v1/model/<regex>/submodel'
            >>> SubHandler.url_pattern(for_prefix=True)
            '/api/v1/model/<regex>/submodel/<regex>'
        """
        kind = cls.kind().lower()
        if cls.parent:
            prefix = cls.parent.url_pattern(for_prefix=True)
        else:
            try:
                request = webapp2.get_request()
                prefix = urljoin('http://%s' % request.host, cls.prefix)
            except:
                prefix = cls.prefix
            
        if for_prefix and cls.get_var:
            return '%s/%s/%s' % (prefix, kind, cls.get_var)
        return '%s/%s' % (prefix, kind)

    @classmethod
    def resource_uri(cls, model):
        """Return the resource pattern or the model."""
        if cls.parent:
            if cls.parent.model:
                prefix = cls.parent.resource_uri(model.key.parent())
            else:
                prefix = cls.parent.url_pattern(for_prefix=True)
        if not isinstance(model, ndb.Key):
            model = model.key
        return '%s/%s/%s' % (prefix, cls.kind().lower(), model.id())
    
    def serialize(self, model):
        # Allow models to override the default to_dict
        if hasattr(self.model, 'serialize'):
            resp = self.model.serialize(model)
        else:
            resp = to_dict(model, self.exclude)
        resp['uri'] = self.resource_uri(model)
        resp['key'] = model.key.urlsafe()
        resp['id'] = model.key.id()
        return resp

    @classmethod
    def get_pairs(cls, *ids):
        """Get a list of (kind, id) pairs for this resource."""
        ids = cast_int(ids)
        pairs = []
        my_id = None
        if len(ids) == cls._depth:
            my_id = ids.pop(-1)
        if cls.parent and cls.parent.model:
            pairs = cls.parent.get_pairs(*ids)
        if my_id:
            pairs.append((cls.model._get_kind(), my_id))
        return pairs

    def fetch(self, pairs):
        """Fetch and serialize the resource from a list of (kind, id) pairs."""
        key = ndb.Key(pairs=pairs)
        obj = key.get()
        if obj is None:
            self.abort(404)
        return self.serialize(obj)

    def fetch_models(self, *ids, **kwargs):
        
        limit = int(self.request.get('limit', 100))
        cursor = self.request.get('cursor', None)
        parent_key = kwargs.get('parent_key')

        if parent_key:
            logging.info('running ancestor query for: %s', parent_key)
            query = self.model.query(ancestor=parent_key)
        else:
            query = self.model.query()

        if cursor:
            cursor = Cursor(urlsafe=cursor)
        
        # allow subclasses to modify the query through GET args
        if hasattr(self, 'handle_args'):
            query = self.handle_args(query, **self.request.GET)

        models, next_cursor, more = query.fetch_page(limit, start_cursor=cursor)

        uri = self.url_for(self.kind().lower(), *ids)
        resp = {
            'limit': limit,
            'cursor': next_cursor.urlsafe() if next_cursor else '',
            'uri': uri,
            'models': [self.serialize(m) for m in models],
        }
        if more:
            q = self.request.GET.copy()
            q['cursor'] = next_cursor.urlsafe()
            query_str = '&'.join(['%s=%s' % (k,v) for k, v in q.iteritems()])
            resp['next'] = '%s?%s' % (uri, query_str)
        return resp
    
    @auth_required
    def get(self, *ids):
        """Standard GET"""
        if len(ids) == self._depth:
            # fetch the model itself
            pairs = self.get_pairs(*ids)
            return self.respond_json(self.fetch(pairs))
        elif len(ids):
            # fetch parent to do ancestor query
            pairs = self.parent.get_pairs(*ids)
            pkey = ndb.Key(pairs=pairs)
            return self.respond_json(self.fetch_models(*ids, parent_key=pkey))
        
        return self.respond_json(self.fetch_models())

    @auth_required
    def post(self, *ids):
        if not self.model:
            self.abort(405)
        payload = json.loads(self.request.body)
        if len(ids) == self._depth:
            return self.put(*ids)
        elif len(ids):
            pairs = self.get_pairs(*ids)
            parent_key = ndb.Key(pairs=pairs)
            payload['parent'] = parent_key
        try:
            model = self.model(**payload)
            model.put()
        except AttributeError as ae:
            return self.respond_json({'message': unicode(ae.message)}, 400)
        except Error as e:
            logging.exception("Datastore Error")
            return self.respond_json({'message': unicode(e.message)}, 400)
        self.respond_json(self.serialize(model), status_code=201)

    @auth_required
    def put(self, *ids):
        if not self.model:
            self.abort(405)
        if len(ids) != self._depth:
            self.abort(405)
        payload = json.loads(self.request.body)
        pairs = self.get_pairs(*ids)
        key = ndb.Key(pairs=pairs)
        model = key.get()
        if model is None:
            self.abort(404)
        try:
            for k, v in payload.iteritems():
                setattr(model, k, v)
            model.put()
        except AttributeError as ae:
            return self.respond_json({'message': unicode(ae.message)}, 400)
        except Error as e:
            logging.exception("Datastore Error")
            return self.respond_json({'message': unicode(e.message)}, 400)
        self.respond_json(self.serialize(model))
    
    @classmethod
    def _endpoints(cls):
        """Return a dict of comment and url for this route."""
        docstring = cls.__doc__ or cls.kind().title()
        
        yield {
            'comment': docstring,
            'uri': cls.url_pattern()
        }
        
        if cls.get_var:
            yield {
                'comment': docstring + ' Resource',
                'uri': cls.url_pattern(for_prefix=True)
            }

        for child in cls._children:
            logging.error(child)
            yield child._endpoints()


class RootHandler(API):
    """Cannula API"""

    endpoint = 'v1'
    get_var = None
    version = 'api_v1'
    prefix = '/api'
    
    def get(self):
        """Just dish out some helpful uri info."""
        def unwrap(routes, endpoints):
            # recursively return all routes from the generators
            for r in endpoints:
                if isinstance(r, dict):
                    routes.append(r)
                else:
                    unwrap(routes, r)
            return routes
            
        resp = {
            'comment': self.__doc__,
            'version': self.version,
            'uri': self.url_pattern(),
            'endpoints': unwrap([], self._endpoints())
        }
        return self.respond_json(resp)


class APIRoutes(object):
    
    def __init__(self, prefix="/api/", root=None):
        self.prefix = prefix
        self.routes = []
        self.register(self.prefix, root)
        
    
    def register(self, prefix, handler):
        prefix = prefix if prefix.endswith('/') else prefix + '/'
        kind = handler.kind().lower()
        prefix = urljoin(prefix, kind)
        self.routes.append(webapp2.Route(prefix, handler, name=kind))
        if handler.get_var is not None:
            prefix = '%s/%s' % (prefix, handler.get_var)
            name = 'get_%s' % kind
            self.routes.append(webapp2.Route(prefix, handler, name=name))
        
        # Add all the child routes
        for child in handler._children:
            self.register(prefix, child)



class StoreHandler(BaseHandler):
    """Sentry EntryPoint Handler.
    
    This handles processing events sent by sentry compatable tools.
    """
    
    def post(self):
        obj = json.loads(base64.b64decode(self.request.body).decode('zlib'))
        logging.error(obj)


class IndexHandler(BaseHandler):
    
    def __init__(self, *args, **kwargs):
        super(IndexHandler, self).__init__(*args, **kwargs)
        self.response.set_cookie('foo', 'blahs')
        
    def get(self, *args, **kwargs):
        self.render('cannula/index.html', {'welcome': 'Home dude!'})

class SigninHandler(BaseHandler):
    
    @parameter('email', unicode)
    @parameter('password', unicode)
    def post(self, email, password):
        # Users and Accounts are in the global namespace.
        namespace_manager.set_namespace('')
        auth_id = 'email:%s' % email
        try:
            self.auth.get_user_by_password(auth_id, password)
        except:
            resp = {'message': "Email or Password Incorrect!"}
            return self.respond_json(resp, 400)

        return self.respond_json(self.user)

class SignupHandler(BaseHandler):
    
    @ndb.transactional
    def _create_account(self, name, level=1):
        acc_key = ndb.Key('Account', name)
        if acc_key.get():
            return None
        account = Account(key=acc_key, namespace=name, level=int(level))
        return account.put()
        
    
    @parameter('name', unicode)
    @parameter('email', unicode)
    @parameter('password', unicode)
    @parameter('confirm_password', unicode)
    @parameter('username', unicode)
    @parameter('level', int, default=1)
    def post(self, name, email, password, confirm_password, username, level):
        # Users and Accounts are in the global namespace.
        namespace_manager.set_namespace('')

        account = self._create_account(username, level)
        if account is None:
            resp = {
                'message': u'An account with that username exists!',
                'field': u'account_name',
            }
            return self.respond_json(resp, 400)
        
        # Attempt to create the User
        attrs = {
            'auth_id': 'email:%s' % email,
            'name': name,
            'password_raw': password,
        }
        created, user = User.create_user(**attrs)
        
        if not created:
            # Transaction rollback!
            account.delete()
            resp = {
                'message': u'An account with that email exists!',
                'field': u'email',
            }
            return self.respond_json(resp, 400)
        
        self.respond_json(to_dict(user), 201)
        

class ProfileHandler(BaseHandler):
    
    def post(self, *args, **kwargs):
        logging.error(self.request.params)


class NamespaceHandler(BaseHandler):
    
    def get(self, *args, **kwargs):
        namespace = self.request.get('namespace')
        namespace_manager.set_namespace(namespace)
        self.session['namespace'] = namespace
        logging.error(self.session.items())
        self.redirect('/')

    def post(self, *args, **kwargs):
        logging.error(self.request.params)
        namespace = self.request.get('namespace')
        if not self.user.is_admin or namespace not in self.user.namespaces:
            self.abort(403)
        namespace_manager.set_namespace(namespace)
        self.redirect('/')

class UserHandler(API):
    """User Handler"""

    model = User
    parent = RootHandler
    excludes = ['password', 'auth_ids']
    csrf_exempt = True

class ProjectHandler(API):
    """Project Handler"""

    model = Project
    parent = UserHandler
    csrf_exempt = True

class KeyHandler(API):
    
    model = SSHKey
    parent = UserHandler
    csrf_exempt = True    

class GroupHandler(API):
    
    model = Group
    parent = RootHandler
    csrf_exempt = True
    methods = ['GET', 'PUT', 'OPTIONS', 'HEAD']
    
    def handle_args(self, query, project=None, **kwargs):
        if project is not None:
            try:
                project = int(project)
                return query.filter('project', project)
            except:
                pass
        return query
        
        

###
### Main routes for api
### 
api_routes = APIRoutes(prefix='/api/', root=RootHandler)

###
### Setup extra routes
###
routes = list(api_routes.routes)
routes += [
    webapp2.Route('/api/store/', StoreHandler),
    webapp2.Route('/accounts/signin/', SigninHandler),
    webapp2.Route('/accounts/signup/', SignupHandler),
    webapp2.Route('/accounts/profile/', ProfileHandler),
    webapp2.Route('/accounts/namespace/', NamespaceHandler),
    webapp2.Route('/<:.*>', IndexHandler),
] 

### 
### Application configuration
###
config = {
    'webapp2_extras.auth': {
        'user_model': 'cannula.gae.models.User',
        'cookie_name': 'cannula_auth',
        'user_attributes': ['name']
    },
    'webapp2_extras.sessions': {
        'secret_key': SECRET_KEY,
        'backend': 'securecookie',
        'cookie_name': 'cannula_session'
    },
    'webapp2_extras.jinja2' : {
        'template_path': [
            'templates',
            'cannula/templates',
        ],
    }
}

# The Main Application
app = webapp2.WSGIApplication(routes, config=config)
