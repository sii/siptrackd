import os
import codecs
from sqlite3 import dbapi2 as sqlite
import struct
import threading

try:
    import cPickle as pickle
except ImportError:
    import pickle

from siptrackdlib import errors

sqltables = [
        """
        create table version
        (
            version varchar(100)
        )
        """,
        """
        create table idmap
        (
            parent_oid varchar(16),
            oid varchar(16),
            class_id varchar(16)
        )
        """,
        """
        create table associations
        (
            self_oid varchar(16),
            other_oid varchar(16)
        )
        """,
        """
        create table nodedata
        (
            oid varchar(16),
            name varchar,
            datatype varchar(16),
            data blob,
            UNIQUE (oid, name)
        )
        """
        ]

class SQLHandler(object):
    def __init__(self, dbcon):
        self.dbcon = dbcon
        self._transaction = False
        self._write_lock = threading.Lock()

    def doQuery(self, query, qargs = (), commit = False, keep_cursor = False, write_lock = False):
        cur = self.dbcon.cursor()
        if write_lock:
            self._write_lock.acquire()
        try:
#            print 'q="%s", qargs="%s"' % (query, qargs)
            cur.execute(query, qargs)
            if commit and not self._transaction:
                self.dbcon.commit()
        except sqlite.DatabaseError:
            cur.close()
            raise
        finally:
            if write_lock:
                self._write_lock.release()
        if not keep_cursor:
            cur.close()
            cur = None
        return cur

    def fetchSingle(self, query, qargs = ()):
        cur = self.doQuery(query, qargs, keep_cursor = True)
        res = cur.fetchone()
        cur.close()
        if res != None and len(res) > 0:
            return res[0]
        return None

    def fetchRow(self, query, qargs = ()):
        cur = self.doQuery(query, qargs, keep_cursor = True)
        res = cur.fetchone()
        cur.close()
        return res

    def returnsRow(self, query, qargs = ()):
        cur = self.doQuery(query, qargs, keep_cursor = True)
        ret = False
        if cur.fetchone():
            ret = True
        cur.close()
        return ret

    def iterRows(self, query, qargs = ()):
        cur = self.doQuery(query, qargs, keep_cursor = True)
        for row in cur:
            yield row
        cur.close()

    def startTransaction(self):
        self._transaction = True

    def endTransaction(self):
        if self._transaction:
            self._transaction = False
            self.dbcon.commit()

    def rollbackTransaction(self):
        if self._transaction:
            self._transaction = False
            self.dbcon.rollback()

class Storage(object):
    def __init__(self, dbfile = None, readonly = False):
        """Load (or create if it doesn't exist) necessary infrastructure."""
        if not dbfile:
            raise errors.StorageError('stsqlite storage requires a dbfile option')
        self.dbfile = dbfile
        # The option might be straight from commandline.
        # Sort of ugly.
        if type(readonly) in [str, unicode]:
            if readonly in ['True', 'true']:
                readonly = True
            elif readonly in ['False', 'false']:
                readonly = False
            else:
                raise errors.StorageError('invalid value for "readonly" param: %s' % (readonly))
        self.readonly = readonly

    def reload(self):
        sqlite_db = sqlite.connect(self.dbfile, check_same_thread = False)
        self.sqlhandler = SQLHandler(sqlite_db)

    def getVersion(self):
        version = self.sqlhandler.fetchSingle("""select version from version""")
        return version

    def setVersion(self, version):
        q = """replace into version (version) values (?)"""
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        cur = self.sqlhandler.dbcon.cursor()
        cur.execute(q, (version,))
        cur.close()

    def initialize(self, version):
        needs_init = False
        if not os.path.exists(self.dbfile):
            needs_init = True
        sqlite_db = sqlite.connect(self.dbfile, check_same_thread = False)
        self.sqlhandler = SQLHandler(sqlite_db)
        if needs_init:
            if self.readonly:
                raise errors.StorageError('storage in readonly mode')
            cur = self.sqlhandler.dbcon.cursor()
            for table in sqltables:
                cur.execute(table)
            cur.close()
            self.setVersion(version)
            self.sqlhandler.dbcon.commit()

    def startTransaction(self):
        self.sqlhandler.startTransaction()

    def endTransaction(self):
        self.sqlhandler.endTransaction()

    def rollbackTransaction(self):
        self.sqlhandler.rollbackTransaction()

    def addOID(self, parent_oid, oid, class_id):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        q = """insert into idmap (parent_oid, oid, class_id) values (?, ?, ?)"""
        args = (parent_oid, oid, class_id)
        self.sqlhandler.doQuery(q, args, commit = True, write_lock = True)

    def OIDExists(self, oid):
        q = """select oid from idmap where oid = ? limit 1"""
        return self.sqlhandler.returnsRow(q, (oid,))

    def classIDFromOID(self, oid):
        q = """select class_id from idmap where oid = ? limit 1"""
        return self.sqlhandler.fetchSingle(q, (oid,))

    def removeOID(self, oid):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        q = """delete from idmap where oid = ?"""
        self.sqlhandler.doQuery(q, (oid,), commit = True, write_lock = True)
        q = """delete from nodedata where oid = ?"""
        self.sqlhandler.doQuery(q, (oid,), commit = True, write_lock = True)
        q = """delete from associations where self_oid = ?"""
        self.sqlhandler.doQuery(q, (oid,), commit = True, write_lock = True)

    def listOIDs(self):
        q = """select * from idmap order by parent_oid"""
        return [(row[0], row[1]) for row in self.sqlhandler.iterRows(q)]

    def listOIDClasses(self):
        q = """select oid, class_id from idmap"""
        return [(row[0], row[1]) for row in self.sqlhandler.iterRows(q)]

    def listAssociations(self):
        q = """select * from associations"""
        return [(row[0], row[1]) for row in self.sqlhandler.iterRows(q)]

    def associate(self, self_oid, other_oid):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        q = """insert into associations (self_oid, other_oid) values (?, ?)"""
        self.sqlhandler.doQuery(q, (self_oid, other_oid), commit = True, write_lock = True)

    def disassociate(self, self_oid, other_oid):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        q = """delete from associations where self_oid = ? and other_oid = ?"""
        self.sqlhandler.doQuery(q, (self_oid, other_oid), commit = True, write_lock = True)

    def relocate(self, self_oid, new_parent_oid):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        q = """update idmap set parent_oid = ? where oid = ?"""
        self.sqlhandler.doQuery(q, (new_parent_oid, self_oid), commit = True, write_lock = True)

    def writeData(self, oid, name, data):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        dtype = 'pickle'
        data = pickle.dumps(data)
        data = sqlite.Binary(data)
        qargs = (oid, name, dtype, data)
        q = """replace into nodedata (oid, name, datatype, data) values (?, ?, ?, ?)"""
        self.sqlhandler.doQuery(q, qargs, commit = True, write_lock = True)

    def dataExists(self, oid, name):
        q = """select oid from nodedata where oid=? and name=?"""
        return self.sqlhandler.returnsRow(q, (oid, name))

    def _parseReadData(self, dtype, data):
        if dtype == 'pickle':
            data = pickle.loads(str(data))
        else:
            raise errors.StorageError('unknown data type "%s" while reading node data' % (dtype))
        return data

    def readData(self, oid, name):
        q = """select datatype, data from nodedata where oid = ? and name = ?"""
        res = self.sqlhandler.fetchRow(q, (oid, name))
        if not res:
            return None
        dtype, data = res
        data = self._parseReadData(dtype, data)
        return data

    def removeData(self, oid, name):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        q = """delete from nodedata where oid=? and name=?"""
        return self.sqlhandler.doQuery(q, (oid, name), commit = True, write_lock = True)

    def iterOIDData(self):
        q = """select oid, name, datatype, data from nodedata"""
        for oid, name, dtype, data in self.sqlhandler.iterRows(q):
            data = self._parseReadData(dtype, data)
            yield (oid, name, data)

