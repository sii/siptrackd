from siptrackdlib.storage import stsqlite
from siptrackdlib import errors

def load(storage_type, *args, **kwargs):
    if storage_type == 'stsqlite':
        return stsqlite.Storage(*args, **kwargs)
    else:
        raise errors.StorageError('invalid storage backend')

def list_backends():
    return ['stsqlite']
