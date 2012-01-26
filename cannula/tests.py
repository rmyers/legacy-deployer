from django.test import TestCase
import logging
import sys
import shutil
import os
import tempfile
import ConfigParser
import subprocess
from django.core.exceptions import ValidationError

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../tests/', 'data')

from cannula import conf

base_dir = tempfile.mkdtemp(prefix="cannula_test_")
conf.CANNULA_BASE = base_dir

class CannulaTestCase(TestCase):
    
    def setUp(self):
        super(CannulaTestCase, self).setUp()
        self.base_dir = conf.CANNULA_BASE
        if not os.path.isdir(self.base_dir):
            os.makedirs(self.base_dir)
        logging.info("Running Setup")
        self.dummy_project = os.path.join(self.base_dir, 'dummy')
        
        # TODO: Override any thing else?
        
        try:
                    
            from cannula.api import api
            self.api = api
            
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
            self.api.proc.write_main_conf(commit=True)
            self.api.proxy.write_main_conf(commit=True)
            self.api.proc.startup()
        except:
            logging.exception('Setup Failed')
            shutil.rmtree(self.base_dir)
            self.fail("Problem setting up testcase")
    
    def test_projects(self):
        from cannula.apis import PermissionError
        g1 = self.api.groups.create('testy', 'abby')
        p1 = self.api.projects.create(name='test', user='abby', group=g1)
        self.assertRaises(PermissionError, self.api.projects.create, name='test2', user='jim', group='testy')
        
        self.assertEqual(p1.get_absolute_url(), '/testy/test/')
        self.api.projects.initialize('test', user='abby')
        self.assertTrue(os.path.isdir(p1.repo_dir))
        self.assertTrue(os.path.isdir(p1.project_dir))
        
        # Delete
        self.assertRaises(PermissionError, self.api.projects.delete, p1, 'jim')
        self.api.projects.delete(p1, 'abby')
        
    def test_groups(self):
        from cannula.apis import PermissionError, DuplicateObject
        g1 = self.api.groups.create('test', 'abby')
        self.assertRaises(PermissionError, self.api.groups.create, 'test', 'jim')
        self.assertEqual(g1.get_absolute_url(), '/test/')
        self.assertRaises(DuplicateObject, self.api.groups.create, 'test', 'abby')
        
    
    def test_users(self):
        from cannula.apis import DuplicateObject
        from django.contrib.auth.models import User
        self.assertRaises(DuplicateObject, self.api.users.create, 'jim')
        ted = self.api.users.create('ted', password='lkjh')
        
        self.assertTrue(ted.check_password('lkjh'))
        self.assertFalse(ted.check_password('lskjlskj'))
        
        self.assertEqual(unicode(ted), 'ted')
        
        jim = self.api.users.get('jim')
        self.assertEqual(unicode(jim), 'jim')
        self.assertEqual(jim.get_full_name(), 'Jim User')
    
    def test_permissions(self):
        from cannula.apis import PermissionError
        g1 = self.api.groups.create('test', 'abby')
        self.assertRaises(PermissionError, self.api.groups.delete, g1, 'jim')
    
    def test_keys(self):
        #self.assertRaises(ValidationError, self.api.keys.create, 'jim', 'beans', 'bad_key')
        #self.assertRaises(ValidationError, self.api.keys.create, 'jim', 'beans', 'ssh-rsa')
        self.api.keys.create('jim', 'beans', 'bad_key')
        ssh_key = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQD7bwOVC/d8JI4VS4OD/eJbKIUMJSKamCTz0jSe1dV4FHBioT7+r8HyZwgSKO/iCsc9jnjD5dlMAVhMqWxPeuxgfpd6IT7b8x9XMLKhV8/RORrRsqaT7yVCDgL8tfU0rpNmVUrGJVvRJtqijCNVMmGsVwekZBby3qBP+JIlbCBR2OgJRxhAfySuBqeaZpH2Aefzo9YoXW86LV07LRX0qkf0kCpOc+IR/7hYvgVeNBBKJghc/1B5RPRhts26mKesiPm1l+iwbpoqLV5QMGWadM6Iee4jgYgRA7nOPKHqRbwRrvaEJM/Wh2O9oLflCNa0j9n7D/YtehUYJZ3RjL7lBXcb jim@localhost'
        key = self.api.keys.create('jim', 'beans', ssh_key)
        self.assertEqual(key.ssh_key, ssh_key)
    
    def test_deploy(self):
        from cannula.utils import Git, shell
        g1 = self.api.groups.create('testy', 'abby')
        p1 = self.api.projects.create(name='test', user='abby', group=g1)
        # 
        self.api.projects.initialize(p1, user='abby')
        push = '%s master' % p1.repo_dir
        out, _ = shell(Git.push % push, cwd=self.dummy_project)
        print out
        yaml_file = os.path.join(p1.project_dir, 'app.yaml')
        self.assertTrue(os.path.isfile(yaml_file))
        self.api.deploy.deploy(p1, 'abby')
    
    def tearDown(self):
        super(CannulaTestCase, self).tearDown()
        self.api.proc.shutdown()
        shutil.rmtree(self.base_dir)