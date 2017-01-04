import re

from twisted.web import xmlrpc

from siptrackd_twisted import helpers
from siptrackd_twisted import gatherer
from siptrackd_twisted import baserpc
from siptrackdlib import treenodes
from siptrackdlib import errors

class SimpleRPC(baserpc.BaseRPC):
    def search_match(self, node, re_ptrs):
        match = True
        for name, re_value in re_ptrs:
            if not node.regmatch(re_value, name):
                match = False
        return match

    @helpers.ValidateSession()
    def xmlrpc_search(self, session, oid, search_patterns, ret_attr, include = [],
            exclude = []):
        re_ptrs = []
        for name, value in search_patterns:
            re_ptrs.append((name, re.compile(value, re.IGNORECASE)))
        if oid in ['', 'ROOT']:
            oid = self.object_store.view_tree.oid
        root = self.object_store.getOID(oid, user = session.user)
        node_filter = treenodes.NodeFilter(include, exclude,
                no_match_break = False)
        local_include = [
            'attribute',
            'versioned attribute',
            'encrypted attribute'
        ]
        result = []
        for node in root.traverse(include = local_include, exclude = exclude,
                no_match_break = False):
            parent = node.getParentNode()
            if node_filter.filter(parent.branch) != node_filter.result_match:
                continue
            if self.search_match(node, re_ptrs):
                ret_value = parent.getAttributeValue(ret_attr, '')
                result.append((ret_value, parent.oid))
        return result

    @helpers.ValidateSession()
    def xmlrpc_get_device_names_for_ip(self, session, ip_address, network_trees = None):
        if not network_trees:
            network_trees = []
            vt = self.object_store.view_tree
            for view in vt.listChildren(include=['view']):
                for nt in view.listChildren(include=['network tree']):
                    network_trees.append(nt)
        else:
            if type(network_trees) in [str, unicode]:
                network_trees = [network_trees]
            _network_trees = []
            for nt_oid in network_trees:
                nt = self.object_store.getOID(nt_oid, user=session.user)
                if nt.class_name == 'network tree':
                    _network_trees.append(nt)
            network_trees = _network_trees
        ret = []
        for nt in network_trees:
            try:
                network = nt.getNetwork(ip_address)
            except errors.SiptrackError:
                network = None
            if network:
                for device in network.listAssocRef(include=['device']):
                    if not device.hasReadPermission(session.user):
                        continue
                    name = device.getAttribute('name')
                    if name:
                        ret.append(name.value)
        return ret

    @helpers.ValidateSession()
    def xmlrpc_get_device_data(self, session, device_name):
        searcher = self.object_store.view_tree.search('^%s$' % (device_name), attr_limit=['name'], include=['device'], user=session.user)
        match = False
        for device in searcher:
            if device.getAttributeValue('name') == device_name:
                match = True
                break
        if not match:
            return False
        data = self._getDevice(session.user, device)
        return data

    def _getDeviceRoot(self, device):
        while device.parent and device.parent.class_name == 'device':
            device = device.parent
        return device

    def _getDevice(self, user, device):
        data = {'match': device.oid, 'node_data': {}}
        nodes = [device]
        nodes += device.listAssocRef(include=['device'])
        data['node_data'][device.oid] = self._getDeviceData(user, device)
        for node in nodes:
            for cur in self._iterDeviceParents(node):
                data['node_data'][cur.oid] = self._getDeviceData(user, cur)
        return data

    def _iterDeviceParents(self, device):
        yield device
        while device.parent and device.parent.class_name == 'device':
            device = device.parent
            yield device

    def _getDeviceData(self, user, device):
        data = {'oid': device.oid, 'parent': device.parent.oid, 'attributes': {}, 'passwords': [], 'links': [], 'children': [], 'networks': []}

        local_include = [
            'attribute',
            'versioned attribute',
            'encrypted attribute'
        ]

        for attribute in device.listChildren(include=local_include):
            data['attributes'][attribute.name] = attribute.value
        for password in device.listChildren(include=['password']):
            password_dict = {'password': password.getPassword(None, user), 'username': password.getAttributeValue('username', ''), 'description': password.getAttributeValue('description', '')}
            data['passwords'].append(password_dict)
        for node in device.listAssocRef(include=['device']):
            data['links'].append(node.oid)
        for node in device.listChildren(include=['device']):
            data['children'].append(node.oid)
        for network in device.listAssocRef(include=['ipv4 network', 'ipv6 network']):
            data['networks'].append(str(network.address))
        return data
