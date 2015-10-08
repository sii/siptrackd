import os
import codecs
import MySQLdb
import struct
import threading

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
            version varchar(100) primary key
        )
        """,
        """
        create table idmap
        (
            parent_oid varchar(16),
            oid varchar(16) primary key,
            class_id varchar(16)
        )
        """,
        """
        create table associations
        (
            self_oid varchar(16) primary key,
            other_oid varchar(16)
        )
        """,
        """
        create table nodedata
        (
            oid varchar(16),
            name varchar(64),
            datatype varchar(16),
            data blob,
            primary key (oid,name)
        )
        """,
        """
        create table device_config_data
        (
            oid varchar(16),
            data blob,
            timestamp integer,
            primary key (oid, timestamp)
        )
        """,
        """create index nodedata_oid_idx on nodedata (oid)""",
        """create index idmap_oid_idx on idmap (oid)""",
        """create index associations_self_oid_idx on associations (self_oid)""",
        """create index device_config_data_oid_idx on device_config_data (oid)""",
        ]

sqltables_1_to_2 = [
        """
        create table device_config_data
        (
            oid varchar(16),
            data blob,
            timestamp integer,
            UNIQUE (oid, timestamp)
        )
        """,
        """create index device_config_data_oid_idx on device_config_data (oid)""",
]

class Storage(object):
    def __init__(self, connection_string = None, readonly = False):
        """Load (or create if it doesn't exist) necessary infrastructure."""
        if not connection_string:
            raise errors.StorageError('stmysql storage requires a connection string option')
        self.db_data = self._parseConnectionString(connection_string)
        # The option might be straight from the command line.
        # Sort of ugly.
        if type(readonly) in [str, unicode]:
            if readonly in ['True', 'true']:
                readonly = True
            elif readonly in ['False', 'false']:
                readonly = False
            else:
                raise errors.StorageError('invalid value for "readonly" param: %s' % (readonly))
        self.readonly = readonly

    def _parseConnectionString(self, connection_string):
        ret = {}
        try:
            ret['host'], ret['user'], ret['password'], ret['db'] = connection_string.split(':')
        except:
            raise errors.StorageError('invalid connection string, format: host:user:password:db')
        return ret

    @defer.inlineCallbacks
    def initialize(self, version):
        self.db = adbapi.ConnectionPool('MySQLdb', host=self.db_data['host'],
                                       user=self.db_data['user'], passwd=self.db_data['password'],
                                       db=self.db_data['db'])
        db_initialized = yield self._checkDBInitialized()
        if not db_initialized:
            if self.readonly:
                raise errors.StorageError('storage in readonly mode')
            for table in sqltables:
                yield self.db.runOperation(table)
            yield self.setVersion(version)

    @defer.inlineCallbacks
    def _checkDBInitialized(self):
        q = """SELECT count(*)
        FROM information_schema.TABLES
        WHERE (TABLE_SCHEMA = %s) AND (TABLE_NAME = %s)"""
        res = yield self._fetchSingle(q, (self.db_data['db'], 'version'))
        print 'QQQQ', res
        if res == 0:
            defer.returnValue(False)
        defer.returnValue(True)

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

    @defer.inlineCallbacks
    def setVersion(self, version):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        q = """delete from version"""
        yield self.db.runOperation(q)
        q = """insert into version (version) values (%s)"""
        yield self.db.runOperation(q, (version,))
        defer.returnValue(True)

    def addOID(self, parent_oid, oid, class_id, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        if txn:
            op = txn.execute
        else:
            op = self.db.runOperation
        q = """insert into idmap (parent_oid, oid, class_id) values (%s, %s, %s)"""
        print 'QQQQQQQQ', q, (parent_oid, oid, class_id)
        return op(q, (parent_oid, oid, class_id))

    @defer.inlineCallbacks
    def removeOID(self, oid, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        if txn:
            op = txn.execute
        else:
            op = self.db.runOperation
        q = """delete from idmap where oid = %s"""
        yield op(q, (oid,))
        q = """delete from nodedata where oid = %s"""
        yield op(q, (oid,))
        q = """delete from associations where self_oid = %s"""
        yield op(q, (oid,))
        defer.returnValue(True)

    def associate(self, self_oid, other_oid, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        if txn:
            op = txn.execute
        else:
            op = self.db.runOperation
        q = """insert into associations (self_oid, other_oid) values (%s, %s)"""
        return op(q, (self_oid, other_oid))

    def disassociate(self, self_oid, other_oid, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        if txn:
            op = txn.execute
        else:
            op = self.db.runOperation
        q = """delete from associations where self_oid = %s and other_oid = %s"""
        return op(q, (self_oid, other_oid))

    def relocate(self, self_oid, new_parent_oid, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        if txn:
            op = txn.execute
        else:
            op = self.db.runOperation
        q = """update idmap set parent_oid = %s where oid = %s"""
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
#        data = sqlite.Binary(data)
        qargs = (oid, name, dtype, data)
        q = """replace into nodedata (oid, name, datatype, data) values (%s, %s, %s, %s)"""
        return op(q, qargs)

    def removeData(self, oid, name):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        if txn:
            op = txn.execute
        else:
            op = self.db.runOperation
        q = """delete from nodedata where oid=%s and name=%s"""
        return op(q, (oid, name), commit = True, write_lock = True)

    @defer.inlineCallbacks
    def OIDExists(self, oid):
        q = """select oid from idmap where oid = %s limit 1"""
        res = yield self._fetchSingle(q, (oid,))
        if res is None:
            defer.returnValue(False)
        defer.returnValue(True)

    def classIDFromOID(self, oid):
        q = """select class_id from idmap where oid = %s limit 1"""
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
        q = """select oid from nodedata where oid=%s and name=%s limit 1"""
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
        q = """select datatype, data from nodedata where oid = %s and name = %s limit 1"""
        res = yield self.db.runQuery(q, (oid, name))
        if not res:
            defer.returnValue(None)
        dtype, data = res[0]
        data = self._parseReadData(dtype, data)
        defer.returnValue(data)

    @defer.inlineCallbacks
    def makeOIDData(self):
        def run(txn):
            data_mapping = {}
            q = """select oid, name, datatype, data from nodedata"""
            txn.execute(q)
            for oid, name, dtype, data in txn:
                data = self._parseReadData(dtype, data)
                if oid not in data_mapping:
                    data_mapping[oid] = {}
                data_mapping[oid][name] = data
            return data_mapping
        ret = yield self.db.runInteraction(run)
        defer.returnValue(ret)

    def addDeviceConfigData(self, oid, data, timestamp):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        q = """insert into device_config_data (oid, data, timestamp) values (%s, %s, %s)"""
        op = self.db.runOperation
        data = sqlite.Binary(data)
        return op(q, (oid, data, timestamp))

    def getAllDeviceConfigData(self, oid, only_timestamps = False):
        if only_timestamps:
            q = """select timestamp from device_config_data where oid = %s order by timestamp"""
        else:
            q = """select data, timestamp from device_config_data where oid = %s order by timestamp"""
        return self.db.runQuery(q, (oid,))

    @defer.inlineCallbacks
    def getLatestDeviceConfigData(self, oid):
        q = """select data, timestamp from device_config_data where oid = %s order by timestamp desc limit 1"""
        res = yield self.db.runQuery(q, (oid,))
        if not res:
            defer.returnValue(None)
        data, timestamp = res[0]
        data = str(data)
        defer.returnValue((data, timestamp))

    @defer.inlineCallbacks
    def removeDeviceConfigData(self, oid, timestamp = None, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        if txn:
            op = txn.execute
        else:
            op = self.db.runOperation
        if timestamp is not None:
            q = """delete from device_config_data where oid = %s and timestamp = %s"""
            yield op(q, (oid, timestamp))
        else:
            q = """delete from device_config_data where oid = %s"""
            yield op(q, (oid,))
        defer.returnValue(True)

    @defer.inlineCallbacks
    def getTimestampDeviceConfigData(self, oid, timestamp):
        q = """select data from device_config_data where oid = %s and timestamp = %s limit 1"""
        res = yield self.db.runQuery(q, (oid, timestamp))
        if not res:
            defer.returnValue(None)
        data = str(res[0][0])
        defer.returnValue(data)

    def countDeviceConfigData(self, oid):
        q = """select count(*) from device_config_data where oid = %s"""
        return self._fetchSingle(q, (oid,))

    @defer.inlineCallbacks
    def _upgrade1to2(self):
        print 'DB upgrade version 1 -> 2'
        for table in sqltables_1_to_2:
            yield self.db.runOperation(table)
        yield self.setVersion('2')

    @defer.inlineCallbacks
    def upgrade(self):
        self.db = adbapi.ConnectionPool('MySQLdb', host=self.db_data['host'],
                                       user=self.db_data['user'], passwd=self.db_data['password'],
                                       db=self.db_data['db'])
        version = yield self.getVersion()
        version = str(version)
        if version == '1':
            yield self._upgrade1to2()
        elif version == '2':
            pass
        else:
            raise errors.StorageError('unknown storage version %s' % (version))
        defer.returnValue(True)
