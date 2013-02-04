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
    def auth(self):
        """Check the authorization header for a username to lookup"""
        headers = self.request.headers
        auth = headers.get('Authorization', None)
        if auth:
            return verify_digest(auth)
        return None
    
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
        
    @webapp2.cached_property
    def user(self):
        """Check the authorization header for a username to lookup"""
        if self.auth:
            return User.get_by_auth_id(self.auth)
        return None
    
    def base_url(self):
        return self.request.host_url + '/api/v1'
    
    def uri(self):
        if self.endpoint:
            return self.base_url() + self.endpoint
        return self.base_url()
    
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


class StoreHandler(API):
    
    def post(self):
        obj = json.loads(base64.b64decode(self.request.body).decode('zlib'))
        logging.error(obj)


class IndexHandler(API):
    
    def get(self):
        self.render('cannula/index.html', {'welcome': 'Home dude!'})

###
### Setup the routes for the API
###
routes = [
    webapp2.Route('/', IndexHandler),
    webapp2.Route('/api/store/', StoreHandler),
] 

# The Main Application
app = webapp2.WSGIApplication(routes)
