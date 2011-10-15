import sys
import os
import unittest

from django.core.management import setup_environ

from base import FileSystem
from nodes import File, Directory

# Setup a fake django settings file for templates.
sys.path.append(os.path.join(os.pardir, os.pardir))
from cannula import test_settings
setup_environ(test_settings)

def call_test():
    return "dynamic"

class FSTest(FileSystem):
    template_dir = 'test/fstest'
    
    root = Directory(parent='tmp')
    apache_root = Directory(parent='$root', name='apache')
    apache_conf_dir = Directory(parent='$apache_root', name='conf')
    apache_conf = File(parent='$apache_conf_dir', name='httpd.conf')
    variable = File(parent='$root', name=call_test)
    fake_root = Directory(parent='', name='')
    fake_file = File(parent='$fake_root', name='blah.py')

class TestFileSystem(unittest.TestCase):
    
    def setUp(self):
        self.fs = FSTest()
    
    def test_paths(self):
        self.assertEqual(self.fs.root.path, 'tmp/root')
        self.assertEqual(self.fs.apache_root.path, 'tmp/root/apache')
        self.assertEqual(self.fs.apache_conf_dir.path, 'tmp/root/apache/conf')
        self.assertEqual(self.fs.apache_conf.path, 'tmp/root/apache/conf/httpd.conf')
        self.assertEqual(self.fs.variable.path, 'tmp/root/dynamic')
        self.assertEqual(self.fs.fake_root.path, '')
        self.assertEqual(self.fs.fake_file.path, 'blah.py')
    
    def test_templates(self):
        self.assertEqual(self.fs.apache_conf.template, 'test/fstest/httpd.conf')
        self.assertEqual(self.fs.variable.template, 'test/fstest/dynamic')
        self.assertEqual(self.fs._template_dir, 'test/fstest')
        ctx = {'title': 'apache_conf', 'server': 'localhost', 'port': 80}
        content = self.fs.apache_conf.content(ctx)
        self.assertEqual(content, u'# filesystem test\n#\n# apache_conf\n\nServerName localhost\nListen 80\n\n# end ')
    
    def test_create(self):
        with self.fs as filez:
            ctx = {'title': 'apache_conf', 'server': 'localhost', 'port': 80}
            filez.sync(ctx)
            self.assertTrue(os.path.isdir(filez.root.local_path))
            self.assertTrue(os.path.isdir(filez.apache_root.local_path))
            self.assertTrue(os.path.isdir(filez.apache_conf_dir.local_path))
            self.assertTrue(os.path.isfile(filez.apache_conf.local_path))
            self.assertTrue(os.path.isfile(filez.variable.local_path))
            self.assertTrue(os.path.isdir(filez.fake_root.local_path))
            self.assertTrue(os.path.isfile(filez.fake_file.local_path))
    
if __name__ == '__main__':
    unittest.main()