import collections

import jinja2

TYPES = {
    'boolean': 'BooleanNode',
    'string': 'StringNode',
    'choice': 'ChoiceNode',
    'hidden': 'HiddenNode',
    'plugin': 'PluginNode'
}


class Node(object):
    def __init__(self, parent, data):
        self.data = data
        self.parent = parent
        self.children = collections.OrderedDict()
        self.root = self.parent.root

        self.name = data['name']
        self.path = (self.parent.path + '.' + self.name
                     if self.parent.path else self.name)
        self.desc = data.get('desc')
        self.templates = data.get('templates', [])
        self.when_parent_is = data.get('when_parent_is', None)
        for child in data.get('children', []):
            cls = globals()[TYPES[child['type']]]
            self.children[child['name']] = cls(self, child)

        self.set_default_value()

    def set_value(self, value):
        self.value = value

    def set_default_value(self):
        raise NotImplementedError

    def _get_child_attr(self, key):
        items = key.split('.')
        src = self
        for item in items:
            src = getattr(src, 'children')[item]
        return src

    def get_child_value(self, key):
        return self._get_child_attr(key).value

    def set_child_value(self, key, value):
        self._get_child_attr(key).set_value(value)

    def set_children_values(self, new_data):
        for k, v in new_data.items():
            self.set_child_value(k, v)

    def get_value_tree(self, vtree={}):
        # FIXME: cache the data?
        for name, child in self.children.items():
            vtree[child.path] = child.value
            child.get_value_tree(vtree)
        return vtree

    def dump_value_tree(self, indent=0):
        for name, child in self.children.items():
            print "%s%s : %s" % (indent * ' ', name, child.value)
            child.dump_value_tree(indent + 2)

    def get_local_conf_lines(self):
        vtree = self.root.get_value_tree()
        lines = []
        for template_str in self.templates:
            j2_tmpl = jinja2.Template(template_str)
            line = j2_tmpl.render(data=vtree)
            if line:
                lines.append(line)

        if lines and hasattr(self, 'desc'):
            lines.insert(0, "# %s" % self.desc)
            lines.insert(0, "")

        # manage running through children
        for name, child in self.children.items():
            if (child.when_parent_is is not None and
               child.when_parent_is != self.value):
                continue
            child_lines = child.get_local_conf_lines()
            lines.extend(child_lines)

        return lines

    def get_form(self):
        raise NotImplementedError

    def get_tree_form(self):
        form = self.get_form()
        if self.children:
            subform = ''
            for name, child in self.children.items():
                subform += child.get_tree_form()
            if self.parent is not None:
                subform = '<div class="form-indent">%s</div>' % subform

            form += subform

        return form


class BooleanNode(Node):
    type = 'boolean'

    def set_default_value(self):
        self.value = self.data.get('default', True)

    def set_value(self, value):
        self.value = True if value in ['on', True, 1] else False

    def get_form(self):
        checked = 'checked="checked"' if self.value else ''
        s = ('<div class="checkbox">'
             '<label>'
             '<input type="checkbox" %(c)s id="%(path)s" name="%(path)s"/>'
             ' %(desc)s</label>'
             '</div>' % {
                 'c': checked,
                 'path': self.path,
                 'desc': self.desc
             })
        h = ('<input type="hidden" value="0" name="%s">' %
             self.path)
        return s + h


class PluginNode(BooleanNode):
    type = 'plugin'

    def __init__(self, parent, data):
        super(PluginNode, self).__init__(parent, data)
        self.services = data.get('services', [])
        self.templates = [
            ('{%% if data["%(path)s"] %%}enable_plugin %(name)s '
             'https://git.openstack.org/openstack/%(name)s.git{%% endif %%}' %
             {'name': self.name, 'path': self.path}),
            ('{%% if data["%(path)s"] %%}enable_service %(services)s'
             '{%% endif %%}' %
             {'path': self.path, 'services': ','.join(self.services)})
        ]


class StringNode(Node):
    type = 'string'

    def set_default_value(self):
        self.value = self.data.get('default', '')

    def get_form(self):
        return ('<div class="form-group">'
                '<label for="%(path)s">%(desc)s:</label>'
                '<input class="form-control" name="%(path)s" '
                'value="%(value)s" id="%(path)s"/>'
                '</div>' % {
                    'path': self.path,
                    'desc': self.desc,
                    'value': self.value
                })


class ChoiceNode(StringNode):
    type = 'choice'

    def __init__(self, parent, data):
        super(ChoiceNode, self).__init__(parent, data)
        self.choices = data['choices']

    def get_form(self):
        s = ('<div class="form-group">'
             '<label for="%(path)s">%(desc)s:</label>'
             '<select class="form-control" name="%(path)s" id="%(path)s">' % {
                 'path': self.path,
                 'desc': self.desc
             })
        for choice in self.choices:
            selected = 'selected="selected"' if choice == self.value else ''
            s += '<option value="%(choice)s" %(s)s>%(choice)s</option>' % {
                'choice': choice,
                's': selected
            }
        s += '</select></div>'
        return s


class HiddenNode(Node):
    type = 'hidden'

    def set_default_value(self):
        self.value = None

    def get_form(self):
        return ''


class RootNode(Node):
    type = 'root'

    def __init__(self, data):
        self.data = data
        self.parent = None
        self.children = collections.OrderedDict()
        self.root = self
        self.path = ''
        self.templates = []
        self.when_parent_is = None
        for child in self.data:
            cls = globals()[TYPES[child['type']]]
            self.children[child['name']] = cls(self, child)

    def get_form(self):
        return ''

    def get_local_conf(self, data):
        self.set_children_values(data)
        lines = self.get_local_conf_lines()
        local_conf = '[[local|localrc]]\n'
        for line in lines:
            local_conf += line + '\n'

        return local_conf
