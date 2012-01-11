import os
from logging import getLogger
from shutil import copy2

from cannula.api import BaseYamlAPI, messages
from cannula.conf import api, CANNULA_CMD
from cannula.api.exceptions import ApiError
from cannula.utils import render_to_string

logger = getLogger('api.keys')

class KeyAPI(BaseYamlAPI):
    
    model = messages.Key
    base_dir = 'keys'
    
    def obj_name(self, user, keyname):
        user = api.users.get(user)
        keyname = keyname.replace(' ', '_')
        return '%s:%s' % (user.name, keyname)
    
    def create(self, user, keyname, ssh_key):
        name = self.obj_name(user, keyname)
        return super(KeyAPI, self).create(name, ssh_key=ssh_key)
    
    def mine(self, user):
        user = api.users.get(user)
        keys = [self.get(n) for n in self.list_all() if n.startswith('%s:' % user.name)]
        return [self.get(k) for k in keys]
    
    def authorized_keys(self):
        """Returns a formated authorized_key file for all keys."""
        ctx = {
            'keys': self.list_all(fetch=True),
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