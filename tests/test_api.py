from base import CannulaTestCase
import os

class TestAPI(CannulaTestCase):
    
    
    def test_projects(self):
        from cannula.api import PermissionError
        g1 = self.api.groups.create('testy', 'abby')
        p1 = self.api.projects.create('test', user='abby', group=g1)
        self.assertRaises(PermissionError, self.api.projects.create, 'test2', user='jim', group='testy')
        
        self.assertEqual(p1.get_absolute_url(), '/testy/test/')
        self.api.projects.initialize('test', user='abby')
        self.assertTrue(os.path.isdir(p1.repo_dir))
        self.assertTrue(os.path.isdir(p1.project_dir))
        
    def test_groups(self):
        from cannula.api import PermissionError
        g1 = self.api.groups.create('test', 'abby')
        self.assertRaises(PermissionError, self.api.groups.create, 'test', 'jim')
    
    def test_users(self):
        from cannula.api import DuplicateObject
        self.assertRaises(DuplicateObject, self.api.users.create, 'jim')
        ted = self.api.users.create('ted', password='lkjh')
        
        self.assertTrue(ted.check_password('lkjh'))
        self.assertFalse(ted.check_password('lskjlskj'))
        
        self.assertEqual(unicode(ted), 'ted')
        
        jim = self.api.users.get('jim')
        self.assertEqual(unicode(jim), 'Jim User')

if __name__ == '__main__':
    import unittest
    unittest.main()