import unittest
import tempfile
import shutil
import os

class BasicTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = self._makeTempDir()

    def tearDown(self):
        self._cleanTempDir(self.tempdir)

    def _makeTempDir(self):
        return tempfile.mkdtemp()

    def _cleanTempDir(self, dir):
        if not os.path.isdir(dir):
            return
        norm_path = os.path.abspath(os.path.normpath(dir))
        if os.path.normpath == '/':
            return
        shutil.rmtree(dir)

    def _makeObjectStore(self):
        import siptrackdlib
        from siptrackdlib.storage import stsqlite
        storage_file = os.path.join(self.tempdir, 'stsqlite.db')
        storage = stsqlite.Storage(storage_file)
        object_store = siptrackdlib.ObjectStore(storage)
        return object_store

class StandardTestCase(BasicTestCase):
    def setUp(self):
        super(StandardTestCase, self).setUp()
        self.object_store = self._makeObjectStore()

    def tearDown(self):
        super(StandardTestCase, self).tearDown()

    def reloadObjectStore(self):
        del self.object_store
        self.object_store = self._makeObjectStore()

def run_tests(test_modules):
    alltest = unittest.TestSuite()
    for module in test_modules:
        module = __import__(module)
        alltest.addTest(unittest.findTestCases(module))
    unittest.TextTestRunner(verbosity=2).run(alltest)

