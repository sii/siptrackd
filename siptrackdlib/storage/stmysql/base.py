import os
import codecs
#import MySQLdb
import pymysql
import struct
import threading
import time
import sys

from twisted.enterprise import adbapi
from twisted.internet import defer
from twisted.internet import reactor

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
            class_id varchar(64)
        )
        """,
        """
        create table associations
        (
            self_oid varchar(16),
            other_oid varchar(16),
            primary key (self_oid, other_oid)
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
            data MEDIUMBLOB,
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
            data MEDIUMBLOB,
            timestamp integer,
            UNIQUE (oid, timestamp)
        )
        """,
        """create index device_config_data_oid_idx on device_config_data (oid)""",
]

class Storage(object):
    def __init__(self, config = None, readonly = False):
        """Load (or create if it doesn't exist) necessary infrastructure."""
        self.readonly = readonly
        self.db_config = config


    @defer.inlineCallbacks
    def initialize(self, version):
        self.db = adbapi.ConnectionPool(
            'pymysql',
            host=self.db_config.get('mysql', 'hostname'),
            user=self.db_config.get('mysql', 'username'),
            passwd=self.db_config.get('mysql', 'password'),
            db=self.db_config.get('mysql', 'dbname'),
            cp_reconnect=True,
        )
        db_initialized = yield self._checkDBInitialized()
        if not db_initialized:
            if self.readonly:
                raise errors.StorageError('storage in readonly mode')
            for table in sqltables:
                yield self.runOperation(table)
            yield self.setVersion(version)
#        self._keepalive()

    @defer.inlineCallbacks
    def _checkDBInitialized(self):
        q = """SELECT count(*)
        FROM information_schema.TABLES
        WHERE (TABLE_SCHEMA = %s) AND (TABLE_NAME = %s)"""
        res = yield self._fetchSingle(
            q,
            (self.db_config.get('mysql', 'dbname'), 'version')
        )
        if res == 0:
            defer.returnValue(False)
        defer.returnValue(True)

    @defer.inlineCallbacks
    def _fetchSingle(self, *args, **kwargs):
        res = yield self.runQuery(*args, **kwargs)
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
        yield self.runOperation(q)
        q = """insert into version (version) values (%s)"""
        yield self.runOperation(q, (version,))
        defer.returnValue(True)

    def addOID(self, parent_oid, oid, class_id, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        q = """insert into idmap (parent_oid, oid, class_id) values (%s, %s, %s)"""
        if txn:
            return self.txndbrun(txn, q, (parent_oid, oid, class_id))
        else:
            return self.runOperation(q, (parent_oid, oid, class_id))

    @defer.inlineCallbacks
    def removeOID(self, oid, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        if txn:
            ret = self._txnRemoveOID(txn, oid)
        else:
            ret = yield self._removeOID(oid)
        defer.returnValue(ret)

    def _txnRemoveOID(self, txn, oid):
        q = """delete from idmap where oid = %s"""
        self.txndbrun(txn, q, (oid,))
        q = """delete from nodedata where oid = %s"""
        self.txndbrun(txn, q, (oid,))
        q = """delete from associations where self_oid = %s"""
        self.txndbrun(txn, q, (oid,))
        return True

    @defer.inlineCallbacks
    def _removeOID(self, oid):
        q = """delete from idmap where oid = %s"""
        yield self.runOperation(q, (oid,))
        q = """delete from nodedata where oid = %s"""
        yield self.runOperation(q, (oid,))
        q = """delete from associations where self_oid = %s"""
        yield self.runOperation(q, (oid,))
        defer.returnValue(True)

    def associate(self, self_oid, other_oid, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        q = """insert into associations (self_oid, other_oid) values (%s, %s)"""
        if txn:
            return self.txndbrun(txn, q, (self_oid, other_oid))
        else:
            return self.runOperation(q, (self_oid, other_oid))

    def disassociate(self, self_oid, other_oid, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        q = """delete from associations where self_oid = %s and other_oid = %s"""
        if txn:
            return self.txndbrun(txn, q, (self_oid, other_oid))
        else:
            return self.runOperation(q, (self_oid, other_oid))

    def relocate(self, self_oid, new_parent_oid, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        q = """update idmap set parent_oid = %s where oid = %s"""
        if txn:
            return self.txndbrun(txn, q, (new_parent_oid, self_oid))
        else:
            return self.runOperation(q, (new_parent_oid, self_oid))

    def writeData(self, oid, name, data, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        dtype = 'pickle'
        data = pickle.dumps(data)
        qargs = (oid, name, dtype, data)
        q = """replace into nodedata (oid, name, datatype, data) values (%s, %s, %s, %s)"""
        if txn:
            return self.txndbrun(txn, q, qargs)
        else:
            return self.runOperation(q, qargs)

    def removeData(self, oid, name):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        q = """delete from nodedata where oid=%s and name=%s"""
        if txn:
            return self.txndbrun(txn, q, (oid, name), commit = True, write_lock = True)
        else:
            return self.runOperation(q, (oid, name), commit = True, write_lock = True)

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
        return self.runQuery(q)

    def listOIDClasses(self):
        q = """select oid, class_id from idmap"""
        return self.runQuery(q)

    def listAssociations(self):
        q = """select self_oid, other_oid from associations"""
        return self.runQuery(q)

    def dataExists(self, oid, name):
        q = """select oid from nodedata where oid=%s and name=%s limit 1"""
        res = yield self.runQuery(q, (oid, name))
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
        res = yield self.runQuery(q, (oid, name))
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
        ret = yield self.runInteraction(run)
        defer.returnValue(ret)

    def addDeviceConfigData(self, oid, data, timestamp):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        q = """insert into device_config_data (oid, data, timestamp) values (%s, %s, %s)"""
        return self.runOperation(q, (oid, data, timestamp))

    def getAllDeviceConfigData(self, oid, only_timestamps = False):
        if only_timestamps:
            q = """select timestamp from device_config_data where oid = %s order by timestamp"""
        else:
            q = """select data, timestamp from device_config_data where oid = %s order by timestamp"""
        return self.runQuery(q, (oid,))

    @defer.inlineCallbacks
    def getLatestDeviceConfigData(self, oid):
        q = """select data, timestamp from device_config_data where oid = %s order by timestamp desc limit 1"""
        res = yield self.runQuery(q, (oid,))
        if not res:
            defer.returnValue(None)
        data, timestamp = res[0]
        data = str(data)
        defer.returnValue((data, timestamp))

    @defer.inlineCallbacks
    def removeDeviceConfigData(self, oid, timestamp = None, txn = None):
        if self.readonly:
            raise errors.StorageError('storage in readonly mode')
        ret = None
        if txn:
            if timestamp is not None:
                q = """delete from device_config_data where oid = %s and timestamp = %s"""
                ret = self.txndbrun(txn, op, q, (oid, timestamp))
            else:
                q = """delete from device_config_data where oid = %s"""
                ret = self.txndbrun(txn, op, q, (oid,))
        else:
            op = self.db.runOperation
            if timestamp is not None:
                q = """delete from device_config_data where oid = %s and timestamp = %s"""
                ret = self.runOperation(q, (oid, timestamp))
            else:
                q = """delete from device_config_data where oid = %s"""
                ret = self.runOperation(q, (oid,))
        return ret

    @defer.inlineCallbacks
    def getTimestampDeviceConfigData(self, oid, timestamp):
        q = """select data from device_config_data where oid = %s and timestamp = %s limit 1"""
        res = yield self.runQuery(q, (oid, timestamp))
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
            yield self.runOperation(table)
        yield self.setVersion('2')

    @defer.inlineCallbacks
    def upgrade(self):
        self.db = adbapi.ConnectionPool(
            'pymysql',
            host=self.db_config.get('mysql', 'hostname'),
            user=self.db_config.get('mysql', 'username'),
            passwd=self.db_config.get('mysql', 'password'),
            db=self.db_config.get('mysql', 'dbname')
        )
        version = yield self.getVersion()
        version = str(version)
        if version == '1':
            yield self._upgrade1to2()
        elif version == '2':
            pass
        else:
            raise errors.StorageError('unknown storage version %s' % (version))
        defer.returnValue(True)

    @defer.inlineCallbacks
    def _keepalive(self):
        """Simple keepalive loop for the db."""
        print('Keepalive')
        reactor.callLater(30, self._keepalive)
        res = yield self.runQuery('''select 1''')

    def runQuery(self, *args, **kwargs):
        return self.dbrun(self.db.runQuery, *args, **kwargs)

    def runOperation(self, *args, **kwargs):
        return self.dbrun(self.db.runOperation, *args, **kwargs)

    def _dSleep(self, length, deferred=None):
        """A twisted deferred sleep.

        Can be called with a yield in a inlineCallbacks wrapped function.
        """
        if deferred:
            deferred.callback(True)
            ret = True
        else:
            ret = defer.Deferred()
            reactor.callLater(length, self._dSleep, length, ret)
        return ret

    @defer.inlineCallbacks
    def interact(self, function, *args, **kwargs):
        ret = None
        retries = 10
        while True:
            try:
                ret = yield self.db.runInteraction(function, *args, **kwargs)
            except (adbapi.ConnectionLost, pymysql.OperationalError) as e:
                print('Storage DB access failed, restarting transaction: %s' % e)
                if retries < 1:
                    print(e)
                    print('Storage actions are failing, shutting down')
                    reactor.stop()
                    sys.exit(1)
            except Exception as e:
                print(e)
                print('Storage actions are failing, shutting down')
                reactor.stop()
                sys.exit(1)
            else:
                break
            retries -= 1
            yield self._dSleep(1)
        defer.returnValue(ret)
    runInteraction = interact

    @defer.inlineCallbacks
    def dbrun(self, function, *args, **kwargs):
        ret = None
        retries = 10
        while True:
            try:
#                print('DBRUN', args, kwargs)
                ret = yield function(*args, **kwargs)
            except (adbapi.ConnectionLost, pymysql.OperationalError) as e:
                if retries < 1:
                    print(e)
                    print('Storage actions are failing, shutting down')
                    reactor.stop()
                    sys.exit(1)
            except Exception as e:
                print(e)
                print('Storage actions are failing, shutting down')
                reactor.stop()
                sys.exit(1)
            else:
                break
            retries -= 1
            yield self._dSleep(1)
        defer.returnValue(ret)

    def txndbrun(self, txn, *args, **kwargs):
        ret = None
        retries = 3
        while True:
            try:
#                print('TXNDBRUN', args, kwargs)
                ret = txn.execute(*args, **kwargs)
            except (adbapi.ConnectionLost, pymysql.OperationalError) as e:
                print('Storage DB access failed, retrying: %s' % e)
                if retries < 1:
                    print(e)
                    print('Storage actions are failing')
                    raise
            except Exception as e:
                print(e)
                print('Storage actions are failing, shutting down')
                reactor.stop()
                sys.exit(1)
            else:
                break
            retries -= 1
            time.sleep(0.1)
        return ret
