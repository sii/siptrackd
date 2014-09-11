import os

from utils import (BasicTestCase, StandardTestCase)
import siptrackdlib.errors

class TestObjectStore(StandardTestCase):
    def testGetMissingOID(self):
        self.assertRaises(siptrackdlib.errors.NonExistent,
                self.object_store.getOID, 'abc')

    def testGetExistingOID(self):
        obj = self.object_store.getOID('0')

    def testPersistentObjects(self):
        oid = self.object_store.view_tree.add('view').oid
        self.reloadObjectStore()
        obj = self.object_store.getOID(oid)
        self.assertEqual(oid, obj.oid)
