import os
from logging import getLogger
from shutil import copy2

from django.db.models.loading import get_model

from cannula.apis import BaseAPI
from cannula.conf import CANNULA_CMD
from cannula.api import api
from django.template.loader import render_to_string

log = getLogger('api.keys')

class KeyAPI(BaseAPI):
    
    model = get_model('cannula', 'key')
    
    def create_or_update(self, user, name, ssh_key):
        key, created = self.model.objects.get_or_create(user=user,
            name=name, defaults={'ssh_key':ssh_key})
        if not created:
            log.info("Updating key: %s for user: %s", name, user)
            key.ssh_key = ssh_key
        else:
            log.info("Created key: %s for user: %s", name, user)
        return key
    
    
    def _list(self, user=None):
        if user:
            user = api.users.get(user)
            keys = self.model.objects.filter(user=user)
        else:
            keys = self.model.objects.all()
        return keys.order_by('name').distinct()
    
    def create(self, user, name, ssh_key):
        user = api.users.get(user)
        # create group
        return self.create_or_update(user, name, ssh_key)
    
    def list(self, user=None):
        """
        Return a list of all keys.

        If user is given, then filter the list of keys to only those that
        the user owns.
        """
        return self._list(user=user)
    
    def authorized_keys(self):
        """Returns a formated authorized_key file for all keys."""
        ctx = {
            'keys': self.list(),
            'cannula_cmd': CANNULA_CMD,
        }
        return render_to_string('cannula/authorized_keys.txt', ctx)
        
    def write_keys(self):
        """Write the key file to the current users .ssh/authorized_keys file."""
        key_file = self.authorized_keys()
        ssh_path = os.path.expanduser('~/.ssh')
        authorized_keys = os.path.join(ssh_path, 'authorized_keys')
        if not os.path.isdir(ssh_path):
            os.makedirs(ssh_path, mode=0700)
        
        if os.path.isfile(authorized_keys):
            # save the old version just incase
            copy2(authorized_keys, '%s.bak' % authorized_keys)
        
        # Write the authorized keys file
        with open(authorized_keys, 'w') as f:
            f.write(key_file)