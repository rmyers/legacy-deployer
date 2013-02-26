"""
GAE Models for Cannula

@author: rmyers
"""

from base64 import b64decode
import logging

from google.appengine.ext import ndb
from google.appengine.api.datastore_errors import BadValueError
from google.appengine.api import namespace_manager
from webapp2_extras.appengine.auth.models import User as BaseUser
from webapp2_extras import security
from webapp2_extras import auth


class SSHKeyProperty(ndb.BlobProperty):
    """Special Property to handle ssh keys."""
    
    def _validate(self, value):
        parts = value.split()
        if not parts[0] in ['ssh-rsa', 'ssh-dsa']:
            raise BadValueError("Keys must be in ssh-rsa or ssh-dsa format")
        try:
            decoded = b64decode(parts[1])
        except:
            # keys are base64 encoded
            raise BadValueError("Invalid key encoding!")
        # check the encoded string header matches
        # length of header string in key stored in 4 byte
        try:
            length = ord(decoded[3])
            # string starts at the 5th byte to length
            key_type = decoded[4:length+4]
            if key_type != parts[0]:
                raise BadValueError("Key type and header do not match!")
        except IndexError:
            raise BadValueError("Key string too short!")


class User(BaseUser):

    first_name = ndb.StringProperty()
    last_name = ndb.StringProperty()
    accounts = ndb.StringProperty(repeated=True)
    
    @property
    def email(self):
        return self._grab_auth_id('email')
        
    def _grab_auth_id(self, kind):
        """helper method to return the first auth_id of a certain kind"""
        uid = None
        for auth in self.auth_ids:
            if auth.startswith('%s:' % kind):
                _, uid = auth.split(':')
                break
        return uid
    
    def update_password(self, password, new_password):
        """Update the password for the user if the existing password matches."""
        if not security.check_password_hash(password, self.password):
            raise auth.InvalidPasswordError()
        
        self.password = security.generate_password_hash(new_password, length=12)
        self.put()


# Account Levels, the number also equals the retention length in days.
TRIAL = 1
DEVELOPER = 7
MEDIUM = 30
ENTERPRISE = 90

ACCOUNT_LEVELS = {
    TRIAL: 'Trial',
    DEVELOPER: 'Developer',
    MEDIUM: 'Medium',
    ENTERPRISE: 'Enterprise',
}

class Account(ndb.Model):
    """Stores payment and namespace info, handles rate limits."""
    
    namespace = ndb.StringProperty(required=True)
    stripe_info = ndb.TextProperty()
    level = ndb.IntegerProperty(choices=ACCOUNT_LEVELS.keys())
    
    def __unicode__(self):
        return self.namespace


class SSHKey(ndb.Model):
    name = ndb.StringProperty(indexed=False)
    ssh_key = SSHKeyProperty(indexed=False)
    
    def __unicode__(self):
        return self.name


class Project(ndb.Model):
    
    name = ndb.StringProperty()
    

    def __unicode__(self):
        return self.name


levels = [
    logging.CRITICAL,
    logging.ERROR,
    logging.DEBUG,
    logging.FATAL,
    logging.INFO,
    logging.WARN, 
]


class EventBase(ndb.Model):
    """
    Abstract base class for both Event and Group.
    """
    logger = ndb.StringProperty(default='root', indexed=True)
    level = ndb.IntegerProperty(choices=levels, 
        default=logging.ERROR, indexed=True)
    message = ndb.TextProperty(indexed=False)
    culprit = ndb.StringProperty(indexed=False)
    num_comments = ndb.IntegerProperty(default=0, indexed=False)
    platform = ndb.StringProperty(indexed=False)
    project = ndb.IntegerProperty(indexed=True)


class Group(EventBase):
    """
    Aggregated message which summarizes a set of Events.
    """
    times_seen = ndb.IntegerProperty(default=1, indexed=False)
    users_seen = ndb.IntegerProperty(default=0, indexed=False)
    last_seen = ndb.DateTimeProperty(auto_now=True, indexed=True)
    first_seen = ndb.DateTimeProperty(auto_now_add=True, indexed=True)
    resolved_at = ndb.DateTimeProperty(indexed=False)
    time_spent_total = ndb.FloatProperty(default=0)
    time_spent_count = ndb.IntegerProperty(default=0)

    def __unicode__(self):
        return "(%s) %s" % (self.times_seen, self.error())

    @property
    def avg_time_spent(self):
        if not self.time_spent_count:
            return
        return float(self.time_spent_total) / self.time_spent_count

    def get_version(self):
        if not self.data:
            return
        if 'version' not in self.data:
            return
        module = self.data.get('module', 'ver')
        return module, self.data['version']


class Event(EventBase):
    """
    An individual event.
    """
    event_id = ndb.StringProperty(indexed=False)
    datetime = ndb.DateTimeProperty(auto_now=True, indexed=True)
    time_spent = ndb.FloatProperty(indexed=False)
    data = ndb.JsonProperty()
    server_name = ndb.StringProperty()
    site = ndb.StringProperty()

    def serialize(self):
        data = {}
        data['id'] = self.event_id
        data['checksum'] = self.checksum
        data['project'] = self.project
        data['logger'] = self.logger
        data['level'] = self.get_level_display()
        data['culprit'] = self.culprit
        for k, v in sorted(self.data.iteritems()):
            data[k] = v
        return data

