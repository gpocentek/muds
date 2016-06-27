import collections

import jinja2
import yaml

TYPES = {
    'boolean': 'BooleanNode',
    'string': 'StringNode',
    'choice': 'ChoiceNode'
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
        self.templates = data['templates']
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

    def get_local_conf_data(self):
        vtree = self.root.get_value_tree()
        data = {}
        for section, template_str in self.templates.items():
            data.setdefault(section, '')
            j2_tmpl = jinja2.Template(template_str)
            lines = j2_tmpl.render(data=vtree)
            data[section] += lines

        # manage running through children
        for name, child in self.children.items():
            if (child.when_parent_is is not None and
               child.when_parent_is != self.value):
                continue
            child_data = child.get_local_conf_data()

            for child_section, child_lines in child_data.items():
                data[child_section] = (data.setdefault(child_section, '') +
                                       '\n' + child_lines)
        return data

    def get_form(self):
        raise NotImplementedError

    def get_tree_form(self):
        vtree = self.root.get_value_tree()
        form = self.get_form()
        form += '<div class="subform">'
        for name, child in self.children.items():
            form += child.get_tree_form()
        form += '</div>'

        return form


class BooleanNode(Node):
    type = 'boolean'

    def set_default_value(self):
        self.value = self.data.get('default', True)

    def set_value(self, value):
        self.value = True if value in ['on', True, 1] else False

    def get_form(self):
        checked = 'checked="checked"' if self.value else ''
        s = ('%s <input type="checkbox" %s name="%s">' %
             (self.desc, checked, self.path))
        h = '<input type="hidden" value="0" name="%s">' % self.path
        return s + h


class StringNode(Node):
    type = 'string'

    def set_default_value(self):
        self.value = self.data.get('default', '')

    def get_form(self):
        return ('%s <input name="%s" value="%s">' %
                (self.desc, self.path, self.value))


class ChoiceNode(StringNode):
    type = 'choice'

    def __init__(self, parent, data):
        super(ChoiceNode, self).__init__(parent, data)
        self.choices = data['choices']

    def get_form(self):
        s = '%s <select name="%s">' % (self.desc, self.path)
        for choice in self.choices:
            selected = 'selected="selected"' if choice == self.value else ''
            s += '<option value="%s" %s>%s</option>' % (choice, selected,
                                                        choice)
        s += '</select>'
        return s


class RootNode(Node):
    type = 'root'

    def __init__(self, data):
        self.data = data
        self.parent = None
        self.children = collections.OrderedDict()
        self.root = self
        self.path = ''
        self.templates = {}
        self.when_parent_is = None
        for child in self.data:
            cls = globals()[TYPES[child['type']]]
            self.children[child['name']] = cls(self, child)

    def get_form(self):
        return ''


if __name__ == '__main__':
    data = yaml.load(open('opts.yml'))
    root = RootNode(data)

    #for name, obj in root.children.items():
    #    print name, obj
    #print(root.children)
    #print root.children['rabbitmq'].get_child_value('password')
    #root.dump_value_tree()
    #print root.get_value_tree()
    #print root.children['mysql'].children['password'].get_local_conf_data()

    new_values = {
        'mysql': False,
        'rabbitmq.password': 'SBDJLFBSJDLF',
        'test': 'three'
    }
    root.set_children_values(new_values)

    data = root.get_local_conf_data()
    for section, lines in data.items():
        print section
        print lines
        print
