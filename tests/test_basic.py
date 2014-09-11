import os

from utils import BasicTestCase

class TestBasic(BasicTestCase):
    def testMakeObjectStore(self):
        object_store = self._makeObjectStore()

    def testGetOID0(self):
        object_store = self._makeObjectStore()
        oid_0 = object_store.getOID('0')
        self.assertEqual(oid_0, object_store.view_tree)

