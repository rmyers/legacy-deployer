from base import CannulaTestCase


class TestAPI(CannulaTestCase):
    
    
    def test_projects(self):
        from cannula.api import PermissionError
        g1 = self.api.groups.create('testy', 'abby')
        p1 = self.api.projects.create('test', user='abby', group='testy')
        self.assertRaises(PermissionError, self.api.projects.create, 'test2', user='jim', group='testy')
        
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