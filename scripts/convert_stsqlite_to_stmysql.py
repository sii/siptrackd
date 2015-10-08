#!/usr/bin/env python

"""Convert a stsqlite database to a stmysql database.

Works with siptrack version 2 storage.
"""

import sys
import MySQLdb as mysql
from sqlite3 import dbapi2 as sqlite
import siptrackdlib.storage.stmysql.base

TABLE_SPEC = {
    'version': ['version'],
    'idmap': ['parent_oid', 'oid', 'class_id'],
    'associations': ['self_oid', 'other_oid'],
    'nodedata': ['oid', 'name', 'datatype', 'data'],
    'device_config_data': ['oid', 'data', 'timestamp'],
}

def create_mysql_tables(db):
    print 'Creating mysql tables'
    cur = db.cursor()
    for table in siptrackdlib.storage.stmysql.base.sqltables:
        cur.execute(table)
    cur.close()
    db.commit()

def copy_tables(db_sqlite, db_mysql):
    sqlite_cur = db_sqlite.cursor()
    for table_name, columns in TABLE_SPEC.iteritems():
        print 'Copying table %s' % table_name
        rows = 0
        mysql_cur = db_mysql.cursor()
        read_q = """select %s from %s""" % (','.join(columns), table_name)
        write_q = """insert into %s (%s) values (%s)""" % (table_name, ','.join(columns), ','.join(['%s' for n in columns]))
        sqlite_cur.execute(read_q)
        count = 0
        for row in sqlite_cur:
            rows += 1
            if table_name == 'device_config_data':
                oid, data, timestamp = row
                row = (oid, data, timestamp)
                if len(data) > 3*1024*1024:
                    print 'Skipping', oid, len(data)
                    continue
            try:
                mysql_cur.execute(write_q, row)
            except:
                print 'Table insert failed:', write_q, row
                raise
            count += 1
            if count > 1000:
                db_mysql.commit()
                count = 0
        print 'Copied %d rows' % rows
        db_mysql.commit()
        mysql_cur.close()


def main():
    if len(sys.argv) != 3:
        print 'Usage: %s sqlite-file mysql-connection-string' % sys.argv[0]
        print '  mysql-connection-string: host:user:password:db'
        print '  The mysql database must be created but empty of tables'
        sys.exit(1)

    db_sqlite = sqlite.connect(sys.argv[1])
    my_host, my_user, my_password, my_db = sys.argv[2].split(':')
    db_mysql = mysql.connect(host=my_host, user=my_user, passwd=my_password, db=my_db)
    db_mysql.autocommit(0)
    create_mysql_tables(db_mysql)
    copy_tables(db_sqlite, db_mysql)


if __name__ == '__main__':
    main()
