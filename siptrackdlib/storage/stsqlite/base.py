import os
import codecs
from sqlite3 import dbapi2 as sqlite
import struct
import threading
import time

from twisted.enterprise import adbapi
from twisted.internet import defer

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
            class_id varchar(16),
            timestamp integer
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
        """,
        """create index nodedata_oid_idx on nodedata (oid)""",
        """create index associations_self_oid_idx on associations (self_oid)""",
        """create index idmap_oid_idx on idmap (oid)""",
        """create index idmap_parent_oid_idx on idmap (parent_oid)""",
        ]

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

    @defer.inlineCallbacks
    def initialize(self, version):
        needs_init = False
        if not os.path.exists(self.dbfile):
            needs_init = True
        self.db = adbapi.ConnectionPool('sqlite3', self.dbfile, check_same_thread = False)
        if needs_init:
            if self.readonly:
                raise errors.StorageError('storage in readonly mode')
            for table in sqltables:
                yield self.db.runOperation(table)
            yield self.setVersion(version)

    def interact(self, function, *args, **kwargs):
        return self.db.runInteraction(function, *args, **kwargs)

    @defer.inlineCallbacks
    def _fetchSingle(self, *args, **kwargs):
        res = yield self.db.runQuery(*args, **kwargs)
        ret = None
        if len(res) == 1:
            ret = res[0][0]
        defer.returnValue(ret)

    def getVersion(self):
        return self._fetchSingle("""select version from version""")

    def setVersion(self, version):
        q = """replace into version (version) values (?)"""
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        return self.db.runOperation(q, (version,))

    def addOID(self, parent_oid, oid, class_id, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        if txn:
            op = txn.execute
        else:
            op = self.db.runOperation
        q = """insert into idmap (parent_oid, oid, class_id, timestamp) values (?, ?, ?, ?)"""
        return op(q, (parent_oid, oid, class_id, time.time()))

    @defer.inlineCallbacks
    def removeOID(self, oid, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        if txn:
            op = txn.execute
        else:
            op = self.db.runOperation
        q = """delete from idmap where oid = ?"""
        yield op(q, (oid,))
        q = """delete from nodedata where oid = ?"""
        yield op(q, (oid,))
        q = """delete from associations where self_oid = ?"""
        yield op(q, (oid,))
        defer.returnValue(True)

    @defer.inlineCallbacks
    def removeChildOID(self, parent_oid, class_id, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        if txn:
            op = txn.execute
        else:
            op = self.db.runOperation
        q = """delete from nodedata where oid in (select oid from idmap where parent_oid = ? and class_id = ?)"""
        yield op(q, (parent_oid, class_id))
        q = """delete from associations where self_oid in (select oid from idmap where parent_oid = ? and class_id = ?)"""
        yield op(q, (parent_oid, class_id))
        q = """delete from idmap where parent_oid = ? and class_id = ?"""
        yield op(q, (parent_oid, class_id))
        defer.returnValue(True)

    def associate(self, self_oid, other_oid, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        if txn:
            op = txn.execute
        else:
            op = self.db.runOperation
        q = """insert into associations (self_oid, other_oid) values (?, ?)"""
        return op(q, (self_oid, other_oid))

    def disassociate(self, self_oid, other_oid, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        if txn:
            op = txn.execute
        else:
            op = self.db.runOperation
        q = """delete from associations where self_oid = ? and other_oid = ?"""
        return op(q, (self_oid, other_oid))

    def relocate(self, self_oid, new_parent_oid, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        if txn:
            op = txn.execute
        else:
            op = self.db.runOperation
        q = """update idmap set parent_oid = ? where oid = ?"""
        return op(q, (new_parent_oid, self_oid))

    def writeData(self, oid, name, data, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        if txn:
            op = txn.execute
        else:
            op = self.db.runOperation
        dtype = 'pickle'
        data = pickle.dumps(data)
        data = sqlite.Binary(data)
        qargs = (oid, name, dtype, data)
        q = """replace into nodedata (oid, name, datatype, data) values (?, ?, ?, ?)"""
        return op(q, qargs)

    def removeData(self, oid, name):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        if txn:
            op = txn.execute
        else:
            op = self.db.runOperation
        q = """delete from nodedata where oid=? and name=?"""
        return op(q, (oid, name), commit = True, write_lock = True)

    @defer.inlineCallbacks
    def OIDExists(self, oid):
        q = """select oid from idmap where oid = ? limit 1"""
        res = yield self._fetchSingle(q, (oid,))
        if res is None:
            defer.returnValue(False)
        defer.returnValue(True)

    def classIDFromOID(self, oid):
        q = """select class_id from idmap where oid = ? limit 1"""
        return self._fetchSingle(q, (oid,))

    def listOIDs(self):
        q = """select parent_oid, oid from idmap order by parent_oid"""
        return self.db.runQuery(q)

    def listOIDClasses(self):
        q = """select oid, class_id from idmap"""
        return self.db.runQuery(q)

    def listAssociations(self):
        q = """select self_oid, other_oid from associations"""
        return self.db.runQuery(q)

    def dataExists(self, oid, name):
        q = """select oid from nodedata where oid=? and name=? limit 1"""
        res = yield self.db.runQuery(q, (oid, name))
        if res:
            defer.returnValue(True)
        defer.returnValue(False)

    def _parseReadData(self, dtype, data):
        if dtype == 'pickle':
            data = pickle.loads(str(data))
        else:
            raise errors.StorageError('unknown data type "%s" while reading node data' % (dtype))
        return data

    @defer.inlineCallbacks
    def readData(self, oid, name):
        q = """select datatype, data from nodedata where oid = ? and name = ? limit 1"""
        res = yield self.db.runQuery(q, (oid, name))
        if not res:
            defer.returnValue(None)
        dtype, data = res[0]
        data = self._parseReadData(dtype, data)
        defer.returnValue(data)

    @defer.inlineCallbacks
    def makeOIDClassMapping(self, skip_class_ids):
        def run(txn):
            q = """select oid, class_id from idmap"""
            res = txn.execute(q)
            mapping = {}
            for oid, class_id in res:
                if class_id in skip_class_ids:
                    continue
                mapping[oid] = class_id
            return mapping
        ret = yield self.db.runInteraction(run)
        defer.returnValue(ret)

    @defer.inlineCallbacks
    def makeOIDData(self, skip_class_ids):
        def run(txn):
            data_mapping = {}
            q = """select nodedata.oid, nodedata.name, nodedata.datatype, nodedata.data, idmap.class_id from nodedata, idmap where nodedata.oid = idmap.oid"""
            res = txn.execute(q)
            for oid, name, dtype, data, class_id in res:
                if class_id in skip_class_ids:
                    continue
                data = self._parseReadData(dtype, data)
                if oid not in data_mapping:
                    data_mapping[oid] = {}
                data_mapping[oid][name] = data
            return data_mapping
        ret = yield self.db.runInteraction(run)
        defer.returnValue(ret)

