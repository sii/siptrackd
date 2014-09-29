import os
import os.path
try:
    from whoosh.index import create_in
    from whoosh import fields
    from whoosh.filedb.filestore import FileStorage
    from whoosh.filedb.filestore import RamStorage
    from whoosh.qparser import QueryParser, MultifieldParser
    from whoosh.qparser import plugins
    from whoosh import analysis
    from whoosh.compat import u
    import threading
    _have_whoosh = True
except:
    _have_whoosh = False

from siptrackdlib import errors
from siptrackdlib import log

class BaseSearch(object):
    def _buildIndex(self, object_store = None, force = False):
        pass

    def _getNodeOID(self, node):
        """Returns an oid from a node or oid string.

        Returns an oid string given either a node object
        or an oid string.
        """
        if type(node) in [str, unicode]:
            return node
        else:
            return node.oid

    def _getNonAttrNode(self, node):
        parent = node
        if node.class_name in ['attribute', 'versioned attribute']:
            parent = node.getParentNode()
        return parent

    def _stringifyValue(self, value, force_unicode=False):
        """Create a useful string out of a value.

        This will for example return the string '1' for the int 1 etc.
        """
        if type(value) in [str, unicode]:
            pass
        else:
            value = str(value)
        try:
            value = value.lower()
        except:
            pass
        if force_unicode and type(value) != unicode:
            try:
                value = decode('utf-8')
            except:
                value = u''
        return value

    def load(self, node, string_name, string_value):
        """String being added due to a node being loaded into the object tree.

        Called when a node has been loaded, this can probably be ignored
        for a searcher that stores its data persistently.
        """
        pass

    def set(self, node, string_name, string_value):
        """Set a brand new value for a string for a node."""
        pass

    def remove(self, node, string_name, oid, parent):
        """Remove a string for a node."""
        pass

    def search(self, text, fuzzy = True, default_fields = [], max_results = None):
        """Search for text.
        
        Returns a generator which yields each matching oid.
        """
        return iter([])

class MemorySearch(BaseSearch):
    def __init__(self):
        self.text_oid_map = {}

    def _addOID(self, oid):
        if oid not in self.text_oid_map:
            self.text_oid_map[oid] = {}

    def load(self, node, string_name, string_value):
        oid = self._getNodeOID(node)
        self._addOID(oid)
        string_value = self._stringifyValue(string_value)
        self.text_oid_map[oid][string_name] = string_value
    set = load

    def remove(self, node, string_name, oid, parent):
        oid = self._getNodeOID(node)
        if oid in self.text_oid_map:
            if string_name in self.text_oid_map[oid]:
                del self.text_oid_map[oid][string_name]

    def search(self, text, fuzzy = True, default_fields = [], max_results = None):
        count = 0
        for oid in self.text_oid_map:
            for string_name in self.text_oid_map[oid]:
                if text in self.text_oid_map[oid][string_name]:
                    yield oid
                    count += 1
                    break
            if max_results is not None and count > max_results:
                break

class WhooshSearch(BaseSearch):
    def __init__(self, storage_directory = None):
        self._using_existing_index = False
        self.schema, self.ix = self._setup(storage_directory)
        self._indexed = False
        self._write_lock = threading.Lock()

    def _setup(self, storage_directory):
        schema = fields.Schema(
            oid=fields.ID(stored=True, unique=True),
            name=fields.ID())
        schema.add('*', fields.TEXT, glob=True)
        if storage_directory:
            if  os.path.exists(storage_directory):
                self._using_existing_index = True
                storage = FileStorage(storage_directory)
                ix = storage.open_index()
            else:
                os.mkdir(storage_directory)
                storage = FileStorage(storage_directory)
                ix = storage.create_index(schema)
        else:
            storage = RamStorage()
            ix = storage.create_index(schema)
        return (schema, ix)

    def _buildIndex(self, object_store):
        if self._using_existing_index:
            return
        log.msg('WhooshSearch building index, hang on.')
        self._indexed = True
        attr_types = ['attribute', 'versioned attribute']
        writer = self.ix.writer()
        for node in object_store.view_tree.traverse(exclude = attr_types):
            self.set(node, '', '', writer)
        writer.commit()
        log.msg('WhooshSearch index building complete.')

    def load(self, *args, **kwargs):
        pass

    def set(self, node, string_name, string_value, writer = None):
        node = self._getNonAttrNode(node)
        values = node.buildSearchValues()
        values['oid'] = unicode(node.oid)
        self._write_lock.acquire()
        try:
            # Empty, remove.
            if len(values) == 1:
                if writer:
                    writer.delete_by_term('oid', unicode(node.oid))
                else:
                    writer = self.ix.writer()
                    writer.delete_by_term('oid', unicode(node.oid))
                    writer.commit()
            else:
                if writer:
                    writer.add_document(**values)
                else:
                    writer = self.ix.writer()
                    writer.add_document(**values)
                    writer.commit()
        finally:
            self._write_lock.release()

    def remove(self, node, string_name, oid, parent):
        self.set(parent, None, None)

    def search(self, queries, fuzzy = True, default_fields = [], max_results = None):
        if type(queries) != list:
            queries = [queries]
        if type(default_fields) != list:
            default_fields = [default_fields]
        if fuzzy and len(queries) == 1 and len(queries[0].split()) == 1 and ':' not in queries[0] and '*' not in queries[0]:
            queries = ['*%s*' % (queries[0])]
        for query in queries:
            if type(query) != unicode:
                query = query.decode('utf-8')
            log.msg('search query: %s' % (query))
            with self.ix.searcher() as searcher:
                parser = MultifieldParser(default_fields, self.ix.schema)
                parser.remove_plugin_class(plugins.WildcardPlugin)
                parser.add_plugin(WildcardPlugin)
                query = parser.parse(query)
                log.msg('search query parsed: %s' % (query))
                results = searcher.search(query, limit = None)
                count = 0
                for result in results:
                    yield result['oid']
                    count += 1
                    if max_results and count >= max_results:
                        break

    def searchHostnames(self, queries, max_results = None):
        if type(queries) != list:
            queries = [queries]
        parser = QueryParser('name', self.ix.schema)
        with self.ix.searcher() as searcher:
            for query in queries:
                if type(query) != unicode:
                    query = query.decode('utf-8')
                log.msg('search query: %s' % (query))
                query = parser.parse(query)
                log.msg('search query parsed: %s' % (query))
                count = 0
                for result in searcher.search(query, limit = None):
                    yield result['oid']
                    count += 1
                    if max_results and count >= max_results:
                        break

if _have_whoosh:
    # Make the default wildcard plugin stop splitting on . and -
    class WildcardPlugin(plugins.WildcardPlugin):
        # Any number of word chars, followed by at least one question mark or
        # star, followed by any number of word chars, question marks, or stars
        # \u055E = Armenian question mark
        # \u061F = Arabic question mark
        # \u1367 = Ethiopic question mark
        qms = u("\u055E\u061F\u1367")
        expr = u("(?P<text>[\\S]*[*?%s]([\\S]|[*?%s])*)") % (qms, qms)

def get_searcher(name = None, *args, **kwargs):
    if name == 'memory':
        searcher = MemorySearch(*args, **kwargs)
    elif name == 'whoosh':
        if not _have_whoosh:
            raise errors.SiptrackError('Sorry, whoosh search is unavailable.')
        searcher = WhooshSearch(*args, **kwargs)
    else:
        raise errors.SiptrackError('Unknown searcher "%s"' % (name))
    log.msg('Using %s searcher' % (name))
    return searcher
