import unittest
import logging
import sys
import shutil
import os
import tempfile
import ConfigParser
import subprocess

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

class CannulaTestCase(unittest.TestCase):
    
    def setUp(self):
        logging.info("Running Setup")
        self.base_dir = tempfile.mkdtemp(prefix="cannula_test_")
        self.dummy_project = os.path.join(self.base_dir, 'dummy')
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
                    
            from cannula.conf import api, CANNULA_BASE, supervisor, proxy
            self.assertEqual(CANNULA_BASE, self.base_dir)
            self.api = api
            self.proc = supervisor
            
            # create an admin user
            self.api.users.create('abby', password="lkjh", email='abby@cannula.com',
                first_name="Abby", last_name="Admin", is_admin=True)
            self.api.users.create('jim', password="lkjh", email='jim@cannula.com',
                first_name="Jim", last_name="User", is_admin=False)
            # Copy the test git project to base_dir
            shutil.copytree(os.path.join(DATA_DIR, 'dummy'), self.dummy_project)
            from cannula.utils import Git, shell
            shell(Git.init, cwd=self.dummy_project)
            shell(Git.add_all, cwd=self.dummy_project)
            shell(Git.commit % 'initial commit', cwd=self.dummy_project)
            
            # Write out base supervisor and proxy configs
            self.proc.write_main_conf(commit=True)
            proxy.write_main_conf(commit=True)
            self.proc.startup()
        except:
            logging.exception('Setup Failed')
            shutil.rmtree(self.base_dir)
            self.fail("Problem setting up testcase")
    
    def tearDown(self):
        shutil.rmtree(self.base_dir)
        self.proc.shutdown()