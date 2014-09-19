import re

from siptrackdlib.objectregistry import object_registry
from siptrackdlib import treenodes
from siptrackdlib import errors
from siptrackdlib import attribute
from siptrackdlib import storagevalue

class NotEnoughDataError(errors.SiptrackError):
    """Not enough data available _yet_ to complete a variable expansion.
    
    Used by fixed rules during variable expansion to indicate that there is
    currently not enough data available to complete the expansion.
    """
    pass

def split_string(input):
    """Split a string into arguments.
    
    Works sort of like str.split(), except that string quoting and escaping
    is permitted. "" quotes and \ escapes.
    Returns a list of the split string.
    """

    args = []
    state = 'new'
    quoted = False
    escaped = False
    for char in input:
        if state == 'new':
            if char == ' ':
                continue
            state = 'running'
            cur_arg = ''
            if char == '"':
                quoted = True
                continue
        if state == 'running':
            if escaped:
                escaped = False
                cur_arg += char
                continue
            elif char == '\\':
                escaped = True
                continue
            if (quoted and char == '"') or (not quoted and char == ' '):
                state = 'new'
                quoted = False
                args.append(cur_arg)
                continue
            cur_arg += char
    if quoted:
        raise errors.SiptrackError('mismatched quotes')
    if state == 'running':
        args.append(cur_arg)
    return args

def suggest_templates(base_node, template_class):
    cur = base_node
    while cur != None:
        for template in cur.listChildren(include = [template_class]):
            if template == base_node:
                continue
            yield template
        cur = cur.parent

class BaseTemplate(treenodes.BaseNode):
    class_id = 'TMPL'
    class_name = 'template'
    valid_rule_types = ['TMPLRULETEXT', 'TMPLRULEFIXED', 'TMPLRULEREGMATCH',
            'TMPLRULEBOOL', 'TMPLRULEPASSWORD', 'TMPLRULEASSIGNNET',
            'TMPLRULESUBDEV', 'TMPLRULEINT', 'TMPLRULEDELATTR',
            'TMPLRULEFLUSHNODES', 'TMPLRULEFLUSHASSOC']

    def __init__(self, oid, branch, inheritance_only = None,
            inherited_templates = None):
        super(BaseTemplate, self).__init__(oid, branch)
        self.inheritance_only = storagevalue.StorageBool(self,
                'inheritance_only', inheritance_only)
        self.inherited_templates = storagevalue.StorageNodeList(self,
                'inherited', inherited_templates, self._validateInherited)
        self.sequences = {}

    def startSequence(self, name, start_value = 0):
        if name not in self.sequences:
            self.sequences[name] = []
        self.sequences[name].append(start_value)

    def stopSequence(self, name):
        self.sequences[name].pop()

    def getSequence(self, name):
        if name in self.sequences:
            if len(self.sequences[name]) > 0:
                return self.sequences[name][-1]
        return 0

    def setSequence(self, name, value):
        self.sequences[name].pop()
        self.sequences[name].append(value)

    def _created(self, user):
        super(BaseTemplate, self)._created(user)
        self.inheritance_only.commit()
        self.inherited_templates.commit()

    def _loaded(self, data = None):
        super(BaseTemplate, self)._loaded(data)
        self.inheritance_only.preload(data)
        self.inherited_templates.preload(data)

    def apply(self, node, arguments = {}, overwrite = False, skip_rules = [],
            user = None):
        # First make as certain as possible that everything checks out
        # before we start applying the rules.
        for rule in self.listCombinedRules():
            if rule in skip_rules:
                continue
            try:
                rule.validate(node, user, *arguments.get(rule.oid, []))
            except TypeError: # Wrong number of arguments passed
                raise errors.SiptrackError('invalid argument count to apply template rule (oid: %s)' % (rule.oid))
        # And next, apply the rules.
        rules = []
        for rule in list(self.listCombinedRules()):
            if rule.run_first:
                rules.insert(0, rule)
            else:
                rules.append(rule)
        retry_rules = []
        prev_retry_count = 0
        updated = []
        while len(rules) > 0 or len(retry_rules) > 0:
            # If we've run out of rules, try again with the ones that
            # returned NotEnoughDataError.
            if len(rules) == 0:
                # If we're retrying with failed rules, make sure that
                # the number of failed rules has decreased, otherwise
                # we're just looping and will never finish.
                if prev_retry_count == len(retry_rules):
                    raise errors.SiptrackError('rule application is looping, there are unresolvable fixed rule expansion variables')
                prev_retry_count = len(retry_rules)
                rules = retry_rules
                retry_rules = []
            rule = rules.pop(0)
            if rule in skip_rules:
                continue
            try:
                updated += rule.apply(node, overwrite, user, *arguments.get(rule.oid, []))
            except NotEnoughDataError:
                # A fixed rule expansion didn't have enough data to continue.
                # Retry it later.
                retry_rules.append(rule)
        return updated

    def listRules(self):
        for rule in self.listChildren():
            if rule.class_id in self.valid_rule_types:
                yield rule

    def listCombinedRules(self):
        for rule in self.listRules():
            yield rule
        for node in self.inherited_templates.get():
            for rule in node.listCombinedRules():
                yield rule

    def _validateInherited(self, value):
        raise NotImplementedError('_validateInherited must be defined in subclass')

    def _hasInheritanceLoop(self, inherited):
        matched = {self: None}
        remaining = list(inherited)
        while remaining:
            node = remaining.pop(0)
            if node in matched:
                return True
            matched[node] = None
            remaining += list(node.inherited_templates.get())
        return False

class DeviceTemplate(BaseTemplate):
    class_id = 'DTMPL'
    class_name = 'device template'

    def _validateInherited(self, value):
        if type(value) != list:
            raise errors.SiptrackError('invalid value for argument inherited templates')
        for node in value:
            if type(node) is not DeviceTemplate:
                raise errors.SiptrackError('invalid value for argument inherited templates')
        if self._hasInheritanceLoop(value):
            raise errors.SiptrackError('inheritance loop detected')

class NetworkTemplate(BaseTemplate):
    class_id = 'NTMPL'
    class_name = 'network template'

    def _validateInherited(self, value):
        if type(value) != list:
            raise errors.SiptrackError('invalid value for argument inherited templates')
        for node in value:
            if type(node) is not NetworkTemplate:
                raise errors.SiptrackError('invalid value for argument inherited templates')
        if self._hasInheritanceLoop(value):
            raise errors.SiptrackError('inheritance loop detected')

class BaseTemplateRule(treenodes.BaseNode):
    """Base class for template rules.

    This class should be subclassed by all template rules.
    """
    run_first = False

    def validate(self, node, user):
        """Validate the rule.

        Checks that the rule is able to be applied to the node.
        """
        return True

    def _applyAttributes(self, apply_node):
        """Copies a rules own attributes to the given node.

        This method copies all attributes a rule has to the given node.
        Attributes that have an 'exclude' attribute are skipped.
        """
        updated = []
        for attr in self.listChildren(include = ['attribute']):
            exclude = attr.getAttribute('exclude')
            # Skip attributes that have an 'exclude' attribute set to True
            if exclude is not None and exclude.value is True:
                continue
            node = apply_node.add(None, 'attribute', attr.name, attr.atype, attr.value)
            updated.append(node)
        return updated

    def removeAttributes(self, node, name):
        """Removes any attributes with name 'name' in the given node."""
        attrs = []
        include = ['attribute', 'versioned attribute']
        for attr in node.listChildren(include = include):
            if attr.name == name:
                attrs.append(attr)
        updated = []
        for attr in attrs:
            updated += attr.remove(recursive = True)
        return updated

class TemplateRulePassword(BaseTemplateRule):
    class_id = 'TMPLRULEPASSWORD'
    class_name = 'template rule password'

    def __init__(self, oid, branch, username = None, description = None,
            key = None):
        super(TemplateRulePassword, self).__init__(oid, branch)
        self.username = storagevalue.StorageValue(self, 'username', username)
        self.description = storagevalue.StorageValue(self, 'description', description)
        self.key = storagevalue.StorageNode(self, 'key', key)

    def _created(self, user):
        super(TemplateRulePassword, self)._created(user)
        self.username.commit()
        self.description.commit()
        self.key.commit()

    def _loaded(self, data = None):
        super(TemplateRulePassword, self)._loaded(data)
        self.username.preload(data)
        self.description.preload(data)
        self.key.preload(data)

    def validate(self, node, user, pwd = ''):
        if type(pwd) not in [str, unicode]:
            raise errors.SiptrackError('invalid password')
        if self.key.get():
            if not self.key.get().canEncryptDecrypt(user = user):
                raise errors.SiptrackError('unable to use password key when trying to add password')

    def apply(self, node, overwrite, user, pwd = ''):
        updated = [node.add(user, 'password', pwd, self.key.get())]
        if self.username.get() is not None:
            updated += password.add(user, 'attribute', 'username', 'text', self.username.get())
        if self.description.get() is not None:
            updated += password.add(user, 'attribute', 'description', 'text',
                    self.description.get())
        return updated

class TemplateRuleAssignNetwork(BaseTemplateRule):
    class_id = 'TMPLRULEASSIGNNET'
    class_name = 'template rule assign network'

    def __init__(self, oid, branch):
        super(TemplateRuleAssignNetwork, self).__init__(oid, branch)

    def validate(self, node, user):
        if not node.class_name == 'device':
            raise errors.SiptrackError('assign network only valid for devices')

    def apply(self, node, overwrite, user):
        # Don't fail the whole template if we can't auto-assign a network.
        try:
            n, updated = node.autoAssignNetwork(user)
        except errors.SiptrackError:
            updated = []
        return updated
        

class TemplateRuleSubdevice(BaseTemplateRule):
    class_id = 'TMPLRULESUBDEV'
    class_name = 'template rule subdevice'

    def __init__(self, oid, branch, num_devices = None,
            device_template = None, sequence_offset = None):
        super(TemplateRuleSubdevice, self).__init__(oid, branch)
        self.num_devices = storagevalue.StorageNum(self, 'num_devices',
                num_devices)
        self.device_template = storagevalue.StorageNode(self, 'device_tmpl',
                device_template)
        self.sequence_offset = storagevalue.StorageNum(self, 'sequence_offset',
                sequence_offset)

    def _created(self, user):
        super(TemplateRuleSubdevice, self)._created(user)
        self.num_devices.commit()
        self.device_template.commit()
        self.sequence_offset.commit()

    def _loaded(self, data = None):
        super(TemplateRuleSubdevice, self)._loaded(data)
        self.num_devices.preload(data)
        self.device_template.preload(data)
        self.sequence_offset.preload(data)

    def validate(self, node, user, template_args = {}, num_devices = None):
        if type(template_args) != dict:
            raise errors.SiptrackError('argument to TemplateRuleSubdevice must be a dict')

    def apply(self, node, overwrite, user, template_args = {}, num_devices = None):
        if num_devices is None:
            num_devices = self.num_devices.get()
        tmpl = self.device_template.get()
        updated = []
        if tmpl:
            tmpl.startSequence('subdevice')
            try:
                for n in range(num_devices):
                    tmpl.setSequence('subdevice', self.sequence_offset.get() + n)
                    child = node.add(None, 'device')
                    updated.append(child)
                    updated += tmpl.apply(child, template_args, user = user)
            finally:
                tmpl.stopSequence('subdevice')
        else:
            for n in range(num_devices):
                child = node.add(None, 'device')
                updated.append(child)
        return updated

class TemplateRuleText(BaseTemplateRule):
    """Plain text based on user input template rule."""
    class_id = 'TMPLRULETEXT'
    class_name = 'template rule text'

    def __init__(self, oid, branch, attr_name = None, versions = None):
        super(TemplateRuleText, self).__init__(oid, branch)
        self.attr_name = storagevalue.StorageValue(self, 'attr name',
                attr_name)
        self.versions = storagevalue.StorageNumPositive(self, 'versions',
                versions)

    def _created(self, user):
        super(TemplateRuleText, self)._created(user)
        if type(self.attr_name.get()) not in [str, unicode]:
            raise errors.SiptrackError('invalid value for attr_name')
        self.attr_name.commit()
        self.versions.commit()

    def _loaded(self, data = None):
        super(TemplateRuleText, self)._loaded(data)
        self.attr_name.preload(data)
        self.versions.preload(data)

    def validate(self, node, user, value = ''):
        if type(value) not in [str, unicode]:
            raise errors.SiptrackError('invalid argument type for rule %s' % (self.class_name))

    def apply(self, node, overwrite, user, value = ''):
        if overwrite:
            self.removeAttributes(node, self.attr_name.get())
        attr = node.add(None, 'versioned attribute', self.attr_name.get(),
                'text', value, self.versions.get())
        return [attr] + self._applyAttributes(attr)

class TemplateRuleFixed(BaseTemplateRule):
    """Template rule to add a fixed string, with or without variable expansion.

    Takes no user input.
    """
    class_id = 'TMPLRULEFIXED'
    class_name = 'template rule fixed'

    def __init__(self, oid, branch, attr_name = None, value = None,
            variable_expansion = None, versions = None):
        super(TemplateRuleFixed, self).__init__(oid, branch)
        self.attr_name = storagevalue.StorageValue(self, 'attr name',
                attr_name)
        self.value = storagevalue.StorageValue(self, 'value', value)
        self.variable_expansion = storagevalue.StorageValue(self, 'variable expansion',
                variable_expansion)
        self.versions = storagevalue.StorageNumPositive(self, 'versions',
                versions)

    def _created(self, user):
        super(TemplateRuleFixed, self)._created(user)
        if type(self.attr_name.get()) not in [str, unicode]:
            raise errors.SiptrackError('invalid value for attr_name')
        if type(self.value.get()) not in [str, unicode]:
            raise errors.SiptrackError('invalid value for value')
        if self.variable_expansion.get() is None:
            self.variable_expansion.set(False)
        if self.variable_expansion.get() not in [True, False]:
            raise errors.SiptrackError('invalid value for variable_expansion')

        # Make sure expansion etc. works before we allow the rule to be
        # created. Sets node to self just to have something to pass in,
        # it won't be modified.
        self.validate(node = self, user = user)

        self.attr_name.commit()
        self.value.commit()
        self.variable_expansion.commit()
        self.versions.commit()

    def _loaded(self, data = None):
        super(TemplateRuleFixed, self)._loaded(data)
        self.attr_name.preload(data)
        self.value.preload(data)
        self.variable_expansion.preload(data)
        self.versions.preload(data)

    def _getCounter(self, counter_type, name):
        """Return a counter of the given type and name in this rules view."""
        view = self.getParent('view')
        match = None
        if counter_type == 'counterloop':
            counter_type = 'counter loop'
        for cnt in view.listChildren(include = [counter_type]):
            for attr in cnt.listChildren(include = ['attribute']):
                if attr.name == 'name' and attr.value == name:
                    return cnt
        return None

    def _resolveArgs(self, node, args):
        ret = []
        for arg in args:
            try:
                arg_type, arg_name = arg.split(':', 1)
            except ValueError:
                raise errors.SiptrackError('invalid fixed rule argument \'%s\'' % (arg))
            if arg_type in ['counter', 'counterloop']:
                counter = self._getCounter(arg_type, arg_name)
                if not counter:
                    raise errors.SiptrackError('unknown counter while expanding fixed rule')
                ret.append(counter.get())
            if arg_type in ['sequence']:
                value = self.parent.getSequence(arg_name)
                ret.append(value)
            elif arg_type in ['attribute', 'attr']:
                attr = node.getAttribute(arg_name)
                if attr is None:
                    raise NotEnoughDataError()
                ret.append(attr.value)
        return ret

    def _incCounters(self, args):
        """Increment the counters that are used during the variable expansion.

        This is done seperately to make sure that only some counters are
        incremented if something fails along the way during the expansion.
        No error checking should be need since everything has already been
        checked in _resolveArgs and friends.
        """
        counters = []
        for arg in args:
            arg_type, arg_name = arg.split(':', 1)
            if arg_type in ['counter', 'counterloop']:
                counter = self._getCounter(arg_type, arg_name)
                counter.inc()

    def _expandValue(self, node, value, inc_counters = True):
        """Perform variable expansion on a fixed rule string."""
        split = split_string(value)
        if len(split) == 0:
            return ''
        formatstring = split[0]
        args = self._resolveArgs(node, split[1:])
        try:
            value = formatstring % tuple(args)
        except TypeError:
            raise errors.SiptrackError('invalid format string while expanding fixed rule')
        # Increment the counters _last_ when we've seen that everything
        # has worked out.
        if inc_counters:
            self._incCounters(split[1:])
        return value

    def validate(self, node, user):
        value = self.value.get()
        if self.variable_expansion.get() is True:
            try:
                value = self._expandValue(node, value, inc_counters = False)
            except NotEnoughDataError:
                pass

    def apply(self, node, overwrite, user):
        value = self.value.get()
        if self.variable_expansion.get() is True:
            value = self._expandValue(node, value)
        updated = []
        if overwrite:
            updated += self.removeAttributes(node, self.attr_name.get())
        attr = node.add(None, 'versioned attribute', self.attr_name.get(),
                'text', value, self.versions.get())
        updated.append(attr)
        updated += self._applyAttributes(attr)
        return updated

class TemplateRuleRegmatch(BaseTemplateRule):
    class_id = 'TMPLRULEREGMATCH'
    class_name = 'template rule regmatch'

    def __init__(self, oid, branch, attr_name = None, regexp = None,
        versions = None):
        super(TemplateRuleRegmatch, self).__init__(oid, branch)
        self.attr_name = storagevalue.StorageValue(self, 'attr name',
                attr_name)
        self.regexp = storagevalue.StorageValue(self, 'regexp', regexp)
        self.versions = storagevalue.StorageNumPositive(self, 'versions',
                versions)

    def _created(self, user):
        super(TemplateRuleRegmatch, self)._created(user)
        if type(self.attr_name.get()) not in [str, unicode]:
            raise errors.SiptrackError('invalid value for attr_name')
        if type(self.regexp.get()) not in [str, unicode]:
            raise errors.SiptrackError('invalid value for regexp')
        self.attr_name.commit()
        self.regexp.commit()
        self.versions.commit()

    def _loaded(self, data = None):
        super(TemplateRuleRegmatch, self)._loaded(data)
        self.attr_name.preload(data)
        self.regexp.preload(data)
        self.versions.preload(data)

    def validate(self, node, user, value = ''):
        if type(value) not in [str, unicode]:
            raise errors.SiptrackError('invalid argument type for rule %s' % (self.class_name))
        if not re.search(self.regexp.get(), value):
            raise errors.SiptrackError('argument doesn\'t match rule regexp')

    def apply(self, node, overwrite, user, value = ''):
        updated = []
        if overwrite:
            updated += self.removeAttributes(node, self.attr_name.get())
        attr = node.add(None, 'versioned attribute', self.attr_name.get(),
            'text', value, self.versions.get())
        updated.append(attr)
        updated += self._applyAttributes(attr)
        return updated

class TemplateRuleBool(BaseTemplateRule):
    class_id = 'TMPLRULEBOOL'
    class_name = 'template rule bool'

    def __init__(self, oid, branch, attr_name = None, default_value = None,
            versions = None):
        super(TemplateRuleBool, self).__init__(oid, branch)
        self.attr_name = storagevalue.StorageValue(self, 'attr name',
                attr_name)
        self.default_value = storagevalue.StorageValue(self, 'default value',
                default_value)
        self.versions = storagevalue.StorageNumPositive(self, 'versions',
                versions)

    def _created(self, user):
        super(TemplateRuleBool, self)._created(user)
        if type(self.attr_name.get()) not in [str, unicode]:
            raise errors.SiptrackError('invalid value for attr_name')
        if self.default_value.get() not in [True, False]:
            raise errors.SiptrackError('invalid value for default_value')
        self.attr_name.commit()
        self.default_value.commit()
        self.versions.commit()

    def _loaded(self, data = None):
        super(TemplateRuleBool, self)._loaded(data)
        self.attr_name.preload(data)
        self.default_value.preload(data)
        self.versions.preload(data)

    def validate(self, node, user, value = None):
        if value is None:
            value = self.default_value.get()
        if type(value) not in [bool]:
            raise errors.SiptrackError('invalid argument type for rule %s' % (self.class_name))

    def apply(self, node, overwrite, user, value = None):
        if value is None:
            value = self.default_value.get()
        updated = []
        if overwrite:
            updated += self.removeAttributes(node, self.attr_name.get())
        attr = node.add(None, 'versioned attribute', self.attr_name.get(), 'bool',
                value, self.versions.get())
        updated.append(attr)
        updated += self._applyAttributes(attr)
        return updated

class TemplateRuleInt(BaseTemplateRule):
    class_id = 'TMPLRULEINT'
    class_name = 'template rule int'

    def __init__(self, oid, branch, attr_name = None, default_value = None,
            versions = None):
        super(TemplateRuleInt, self).__init__(oid, branch)
        self.attr_name = storagevalue.StorageValue(self, 'attr name',
                attr_name)
        self.default_value = storagevalue.StorageValue(self, 'default value',
                default_value)
        self.versions = storagevalue.StorageNumPositive(self, 'versions',
                versions)

    def _created(self, user):
        super(TemplateRuleInt, self)._created(user)
        if type(self.attr_name.get()) not in [str, unicode]:
            raise errors.SiptrackError('invalid value for attr_name')
        if type(self.default_value.get()) != int:
            raise errors.SiptrackError('invalid value for default_value')
        self.attr_name.commit()
        self.default_value.commit()
        self.versions.commit()

    def _loaded(self, data = None):
        super(TemplateRuleInt, self)._loaded(data)
        self.attr_name.preload(data)
        self.default_value.preload(data)
        self.versions.preload(data)

    def validate(self, node, user, value = None):
        if value is None:
            value = self.default_value.get()
        if type(value) != int:
            raise errors.SiptrackError('invalid argument type for rule %s' % (self.class_name))

    def apply(self, node, overwrite, user, value = None):
        if value is None:
            value = self.default_value.get()
        updated = []
        if overwrite:
            updated += self.removeAttributes(node, self.attr_name.get())
        attr = node.add(None, 'versioned attribute', self.attr_name.get(), 'int',
                value, self.versions.get())
        updated.append(attr)
        updated += self._applyAttributes(attr)

class TemplateRuleDeleteAttribute(BaseTemplateRule):
    class_id = 'TMPLRULEDELATTR'
    class_name = 'template rule delete attribute'
    run_first = True

    def __init__(self, oid, branch, attr_name = None):
        super(TemplateRuleDeleteAttribute, self).__init__(oid, branch)
        self.attr_name = storagevalue.StorageValue(self, 'attr name',
                attr_name)

    def _created(self, user):
        super(TemplateRuleDeleteAttribute, self)._created(user)
        if type(self.attr_name.get()) not in [str, unicode]:
            raise errors.SiptrackError('invalid value for attr_name')
        self.attr_name.commit()

    def _loaded(self, data = None):
        super(TemplateRuleDeleteAttribute, self)._loaded(data)
        self.attr_name.preload(data)

    def validate(self, node, user):
        pass

    def apply(self, node, overwrite, user):
        return self.removeAttributes(node, self.attr_name.get())

class TemplateRuleFlushNodes(BaseTemplateRule):
    class_id = 'TMPLRULEFLUSHNODES'
    class_name = 'template rule flush nodes'
    run_first = True

    def __init__(self, oid, branch, include = None, exclude = None):
        super(TemplateRuleFlushNodes, self).__init__(oid, branch)
        self.include = storagevalue.StorageValue(self, 'include',
                include, self._inclExclValidator)
        self.exclude = storagevalue.StorageValue(self, 'exclude',
                exclude, self._inclExclValidator)

    def _created(self, user):
        super(TemplateRuleFlushNodes, self)._created(user)
        self.include.commit()
        self.exclude.commit()

    def _loaded(self, data = None):
        super(TemplateRuleFlushNodes, self)._loaded(data)
        self.include.preload(data)
        self.exclude.preload(data)

    def _inclExclValidator(self, value):
        if type(value) is not list:
            raise errors.SiptrackError('invalid include/exclude value')
        for ntype in value:
            if type(ntype) not in [str, unicode]:
                raise errors.SiptrackError('invalid include/exclude value')

    def validate(self, node, user):
        pass

    def apply(self, node, overwrite, user):
        updated = []
        for node in list(node.listChildren(include = self.include.get(),
            exclude = self.exclude.get())):
            updated += node.remove(recursive = True)
        return updated

class TemplateRuleFlushAssociations(BaseTemplateRule):
    class_id = 'TMPLRULEFLUSHASSOC'
    class_name = 'template rule flush associations'
    run_first = True

    def __init__(self, oid, branch, include = None, exclude = None):
        super(TemplateRuleFlushAssociations, self).__init__(oid, branch)
        self.include = storagevalue.StorageValue(self, 'include',
                include, self._inclExclValidator)
        self.exclude = storagevalue.StorageValue(self, 'exclude',
                exclude, self._inclExclValidator)

    def _created(self, user):
        super(TemplateRuleFlushAssociations, self)._created(user)
        self.include.commit()
        self.exclude.commit()

    def _loaded(self, data = None):
        super(TemplateRuleFlushAssociations, self)._loaded(data)
        self.include.preload(data)
        self.exclude.preload(data)

    def _inclExclValidator(self, value):
        if type(value) is not list:
            raise errors.SiptrackError('invalid include/exclude value')
        for ntype in value:
            if type(ntype) not in [str, unicode]:
                raise errors.SiptrackError('invalid include/exclude value')

    def validate(self, node, user):
        pass

    def apply(self, node, overwrite, user):
        include = ['attribute', 'versioned attribute']
        updated = [node]
        for assoc in list(node.listAssocRef(include = self.include.get(), exclude = self.exclude.get())):
            node.disAssocRef(assoc)
            updated.append(assoc)

o = object_registry.registerClass(DeviceTemplate)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(TemplateRuleText)
o.registerChild(TemplateRuleFixed)
o.registerChild(TemplateRuleRegmatch)
o.registerChild(TemplateRuleBool)
o.registerChild(TemplateRuleDeleteAttribute)
o.registerChild(TemplateRuleInt)
o.registerChild(TemplateRulePassword)
o.registerChild(TemplateRuleAssignNetwork)
o.registerChild(TemplateRuleSubdevice)
o.registerChild(TemplateRuleFlushNodes)
o.registerChild(TemplateRuleFlushAssociations)

o = object_registry.registerClass(NetworkTemplate)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)
o.registerChild(TemplateRuleText)
o.registerChild(TemplateRuleFixed)
o.registerChild(TemplateRuleRegmatch)
o.registerChild(TemplateRuleBool)
o.registerChild(TemplateRuleInt)
o.registerChild(TemplateRuleDeleteAttribute)
o.registerChild(TemplateRuleFlushNodes)
o.registerChild(TemplateRuleFlushAssociations)

o = object_registry.registerClass(TemplateRulePassword)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleAssignNetwork)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleSubdevice)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleText)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleFixed)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleRegmatch)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleBool)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleInt)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleDeleteAttribute)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleFlushNodes)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

o = object_registry.registerClass(TemplateRuleFlushAssociations)
o.registerChild(attribute.Attribute)
o.registerChild(attribute.VersionedAttribute)

