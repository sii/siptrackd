from siptrackdlib.storage import stsqlite
from siptrackdlib.storage import stmysql
from siptrackdlib import errors

def load(storage_type, *args, **kwargs):
    if storage_type == 'stsqlite':
        return stsqlite.Storage(*args, **kwargs)
    elif storage_type == 'stmysql':
        return stmysql.Storage(*args, **kwargs)
    else:
        raise errors.StorageError('invalid storage backend')

def list_backends():
    return ['stsqlite', 'stmysql']
