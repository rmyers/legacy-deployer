from base import CannulaTestCase
import os

class TestAPI(CannulaTestCase):
    
    
    def test_projects(self):
        from cannula.apis import PermissionError
        g1 = self.api.groups.create('testy', 'abby')
        p1 = self.api.projects.create('test', user='abby', group=g1)
        self.assertRaises(PermissionError, self.api.projects.create, 'test2', user='jim', group='testy')
        
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
        self.assertRaises(DuplicateObject, self.api.users.create, 'jim')
        ted = self.api.users.create('ted', password='lkjh')
        
        self.assertTrue(ted.check_password('lkjh'))
        self.assertFalse(ted.check_password('lskjlskj'))
        
        self.assertEqual(unicode(ted), 'ted')
        
        jim = self.api.users.get('jim')
        self.assertEqual(unicode(jim), 'Jim User')
    
    def test_permissions(self):
        from cannula.apis import PermissionError
        g1 = self.api.groups.create('test', 'abby')
        self.assertRaises(PermissionError, self.api.groups.delete, g1, 'jim')
    
    def test_keys(self):
        self.assertRaises(ValueError, self.api.keys.create, 'jim', 'beans', 'bad_key')
        self.assertRaises(ValueError, self.api.keys.create, 'jim', 'beans', 'ssh-rsa')
        ssh_key = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQD7bwOVC/d8JI4VS4OD/eJbKIUMJSKamCTz0jSe1dV4FHBioT7+r8HyZwgSKO/iCsc9jnjD5dlMAVhMqWxPeuxgfpd6IT7b8x9XMLKhV8/RORrRsqaT7yVCDgL8tfU0rpNmVUrGJVvRJtqijCNVMmGsVwekZBby3qBP+JIlbCBR2OgJRxhAfySuBqeaZpH2Aefzo9YoXW86LV07LRX0qkf0kCpOc+IR/7hYvgVeNBBKJghc/1B5RPRhts26mKesiPm1l+iwbpoqLV5QMGWadM6Iee4jgYgRA7nOPKHqRbwRrvaEJM/Wh2O9oLflCNa0j9n7D/YtehUYJZ3RjL7lBXcb jim@localhost'
        key = self.api.keys.create('jim', 'beans', ssh_key)
        self.assertEqual(key.ssh_key, ssh_key)
    
    def test_deploy(self):
        from cannula.utils import Git, shell
        g1 = self.api.groups.create('testy', 'abby')
        p1 = self.api.projects.create('test', user='abby', group=g1)
        # 
        self.api.projects.initialize(p1, user='abby')
        push = '%s master' % p1.repo_dir
        out, _ = shell(Git.push % push, cwd=self.dummy_project)
        print out
        yaml_file = os.path.join(p1.project_dir, 'app.yaml')
        self.assertTrue(os.path.isfile(yaml_file))
        self.api.deploy.deploy(p1, 'abby')

if __name__ == '__main__':
    import unittest
    unittest.main()