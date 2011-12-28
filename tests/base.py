import unittest
import logging
import sys
import shutil
import os
import tempfile
import ConfigParser

class CannulaTestCase(unittest.TestCase):
    
    def setUp(self):
        logging.info("Running Setup")
        self.base_dir = tempfile.mkdtemp(prefix="cannula_test_")
        self.ini = os.path.join(self.base_dir, 'cannula.ini')
        config = ConfigParser.ConfigParser()
        config.add_section('cannula')
        config.set('cannula', 'CANNULA_BASE', self.base_dir)
        config.set('cannula', 'CANNULA_CACHE', 'werkzeug.contrib.cache.NullCache')
        # TODO: Override any thing else?
        
        try:
            with open(self.ini, 'w') as conf_file:
                config.write(conf_file)
            
            # Use our temporary location and settings module
            os.environ['CANNULA_SETTINGS_MODULE'] = self.ini
            
            # Get rid of any existing imports
            for key in sys.modules.keys():
                if key.startswith('cannula'):
                    del sys.modules[key]
                    
            from cannula.conf import api, CANNULA_BASE
            self.assertEqual(CANNULA_BASE, self.base_dir)
            self.api = api
            
            # create an admin user
            self.api.users.create('abby', password="lkjh", email='abby@cannula.com',
                first_name="Abby", last_name="Admin", is_admin=True)
            self.api.users.create('jim', password="lkjh", email='jim@cannula.com',
                first_name="Jim", last_name="User", is_admin=False)
        except:
            shutil.rmtree(self.base_dir)
            self.fail("Problem setting up testcase")
    
    def tearDown(self):
        shutil.rmtree(self.base_dir)
        