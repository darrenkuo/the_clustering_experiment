"""
HTML forms
(part of web.py)
"""

import copy, re
import webapi as web
import utils, net

def attrget(obj, attr, value=None):
    if hasattr(obj, 'has_key') and obj.has_key(attr): return obj[attr]
    if hasattr(obj, attr): return getattr(obj, attr)
    return value

class Form(object):
    r"""
    HTML form.
    
        >>> f = Form(Textbox("x"))
        >>> f.render()
        '<table>\n    <tr><th><label for="x">x</label></th><td><input type="text" id="x" name="x"/></td></tr>\n</table>'
    """
    def __init__(self, *inputs, **kw):
        self.inputs = inputs
        self.valid = True
        self.note = None
        self.js = kw.pop('js', False)
        self.validators = kw.pop('validators', [])

    def __call__(self, x=None):
        o = copy.deepcopy(self)
        if x: o.validates(x)
        return o
    
    def render(self):
        out = ''
        if self.js:
            out = self.js.render()

        out += self.rendernote(self.note)
        out += '<table>\n<tr>'
        
        for i in self.inputs:
            html = utils.safeunicode(i.pre) + i.render() + self.rendernote(i.note) + utils.safeunicode(i.post)
            
            if i.is_hidden():
                out += '    <th></th><td>%s</td>\n' % (html)
            else:
                out += '    <th><label for="%s">%s</label></th><td>%s</td>\n' % (i.id, net.websafe(i.description), html)
        out += "</tr></table>"
        return out
        
    def render_css(self): 
        out = [] 
        out.append(self.rendernote(self.note)) 
        for i in self.inputs:
            if not i.is_hidden():
                out.append('<label for="%s">%s</label>' % (i.id, net.websafe(i.description))) 
            out.append(i.pre)
            out.append(i.render()) 
            out.append(self.rendernote(i.note))
            out.append(i.post) 
            out.append('\n')
        return ''.join(out) 
        
    def rendernote(self, note):
        if note: return '<strong class="wrong">%s</strong>' % net.websafe(note)
        else: return ""
    
    def validates(self, source=None, _validate=True, **kw):
        source = source or kw or web.input()
        out = True
        for i in self.inputs:
            v = attrget(source, i.name)
            if _validate:
                out = i.validate(v) and out
            else:
                i.set_value(v)
        if _validate:
            out = out and self._validate(source)
            self.valid = out
        return out

    def _validate(self, value):
        self.value = value
        for v in self.validators:
            if not v.valid(value):
                self.note = v.msg
                return False
        return True

    def fill(self, source=None, **kw):
        return self.validates(source, _validate=False, **kw)
    
    def __getitem__(self, i):
        for x in self.inputs:
            if x.name == i: return x
        raise KeyError, i

    def __getattr__(self, name):
        # don't interfere with deepcopy
        inputs = self.__dict__.get('inputs') or []
        for x in inputs:
            if x.name == name: return x
        raise AttributeError, name
    
    def get(self, i, default=None):
        try:
            return self[i]
        except KeyError:
            return default
            
    def _get_d(self): #@@ should really be form.attr, no?
        return utils.storage([(i.name, i.get_value()) for i in self.inputs])
    d = property(_get_d)

class Input(object):
    def __init__(self, name, *validators, **attrs):
        self.name = name
        self.validators = validators
        self.attrs = attrs = AttributeList(attrs)
        
        self.description = attrs.pop('description', name)
        self.value = attrs.pop('value', None)
        self.pre = attrs.pop('pre', "")
        self.post = attrs.pop('post', "")
        self.note = None
        
        self.id = attrs.setdefault('id', self.get_default_id())
        
        if 'class_' in attrs:
            attrs['class'] = attrs['class_']
            del attrs['class_']
        
    def is_hidden(self):
        return False
        
    def get_type(self):
        raise NotImplementedError
        
    def get_default_id(self):
        return self.name

    def validate(self, value):
        self.set_value(value)

        for v in self.validators:
            if not v.valid(value):
                self.note = v.msg
                return False
        return True

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def render(self):
        attrs = self.attrs.copy()
        attrs['type'] = self.get_type()
        if self.value is not None:
            attrs['value'] = self.value
        attrs['name'] = self.name
        return '<input %s/>' % attrs

    def rendernote(self, note):
        if note: return '<strong class="wrong">%s</strong>' % net.websafe(note)
        else: return ""
        
    def addatts(self):
        # add leading space for backward-compatibility
        return " " + str(self.attrs)

class Generic(Input):
    def __init__(self, txt, *validators, **attrs):
        self.txt = txt
        Input.__init__(self, str('', *validators, **attrs))

    def render(self):
        return self.txt

class js(Input):
    def __init__(self, name, txt, *validators, **attrs):
        self.txt = txt
        Input.__init__(self, str(name, *validators, **attrs))

    def render(self):
        return '<script txt="text/javascript">\n' + self.txt + '</script>\n'    

class Table(Input):

    def __init__(self, name, *validators, **attrs):
        self.pairs = attrs.pop('pairs', [])
        self.h_category = attrs.pop('h_category', None)
        self.v_category = attrs.pop('v_category', None)

        if self.h_category:
            cross = attrs.pop('cross', None)
            if cross != None:
                self.h_category.insert(0, cross)
            else:
                if (self.v_category and 
                    len(self.h_category) == len(self.pairs[0])):
                    self.h_category.insert(0, '')

        self.use_id = attrs.pop('use_id', False)

        self.validate_categories()

        if self.pairs and self.use_id:
            self.ids = []
            total = 0
            for i in range(len(self.pairs)):
                total += len(self.pairs[i])
                for j in range(len(self.pairs[i])):
                    (v, h) = self.getId(i, j)
                    self.ids.append('%s@%s@%s@%s' % (
                            name, str(v), str(h), str(self.pairs[i][j])))

            self.ids.reverse()
        Input.__init__(self, name, *validators, **attrs)

    def validate_categories(self):
        if self.v_category and self.h_category:
            if (len(self.v_category) != len(self.pairs) or
                len(self.h_category) != len(self.pairs[0]) + 1):
                raise Exception('Mis-match length in category arrays')
            self.type = 0
        elif self.v_category and not self.h_category:
            if len(self.v_category) != len(self.pairs):
                raise Exception('Mis-match length in category arrays')
            self.type = 1            
        elif not self.v_category and self.h_category:
            if len(self.h_category) != len(self.pairs[0]):
                raise Exception('Mis-match length in category arrays')
            self.type = 2
        else:
            self.type = 3

    def getId(self, i, j):
        if self.type == 0:
            return (self.v_category[i], self.h_category[j + 1])
        elif self.type == 1:
            return (self.v_category[i], None)
        elif self.type == 2:
            return (None, self.h_category[j])
        else:
            return (None, None)

    def render(self):
        def format_td(value):
            if self.use_id:
                id = self.ids.pop()
                return '<td id="%s" onclick="create_graph(this.id);"><center>%s</center></td>\n' % (id, value)
            return '<td><center>%s</center></td>\n' % (value)

        attrs = self.attrs.copy()
        text = '<table %s>\n' % (attrs)
        
        text += '<tr>'

        if self.h_category:
            for i in self.h_category:
                text += '<td><center>%s</center></td>' % (i)
            text += '</tr>\n'

        for i in range(len(self.pairs)):
            if self.v_category:
                text += ('<tr>\n<td><center>%s</center></td>\n' % 
                         (self.v_category[i]))
            for j in self.pairs[i]:
                text += format_td(j)
            text += '</tr>\n'
                
        text += '</table>'
        return text

class AttributeList(dict):
    """List of atributes of input.
    
    >>> a = AttributeList(type='text', name='x', value=20)
    >>> a
    <attrs: 'type="text" name="x" value="20"'>
    """
    def copy(self):
        return AttributeList(self)
        
    def __str__(self):
        return " ".join(['%s="%s"' % (k, net.websafe(v)) for k, v in self.items()])
        
    def __repr__(self):
        return '<attrs: %s>' % repr(str(self))

class Textbox(Input):
    """Textbox input.
    
        >>> Textbox(name='foo', value='bar').render()
        '<input type="text" id="foo" value="bar" name="foo"/>'
        >>> Textbox(name='foo', value=0).render()
        '<input type="text" id="foo" value="0" name="foo"/>'
    """        
    def get_type(self):
        return 'text'

class tr(Input):
    def is_hidden(self):
        return True
    
    def render(self):
        return'</tr><tr>'
    
class Password(Input):
    """Password input.

        >>> Password(name='password', value='secret').render()
        '<input type="password" id="password" value="secret" name="password"/>'
    """
    
    def get_type(self):
        return 'password'

class Selectlist(Input):
    
    """
    <select multiple="yes" size="3">
    <option>California -- CA</option>
    <option>Colorado -- CO</option>
    <option>Connecticut -- CN</option>
    </select>
    """
    def __init__(self, name, datasets, *validators, **attrs):
        super(Selectlist, self).__init__(name, *validators, **attrs)
        self.datasets = datasets

    def render(self):
        option = '<option>%s</option>'
        return ('<select multiple="yes" size="3">' + 
                '\n'.join(map(lambda x: option % (str(x)), self.datasets)) +
                '</select>')

class Textarea(Input):
    """Textarea input.
    
        >>> Textarea(name='foo', value='bar').render()
        '<textarea id="foo" name="foo">bar</textarea>'
    """
    def __init__(self, name, *validators, **attrs):
        super(Textarea, self).__init__(name, *validators, **attrs)

    def render(self):
        attrs = self.attrs.copy()
        attrs['name'] = self.name
        value = net.websafe(self.value or '')
        return '<textarea %s>%s</textarea>' % (attrs, value)

class Link(Input):
    """ Link(link='http://....', value='the link').render()
    '<a href='http://...'>the link</.a>'
    """
    def render(self):
        attrs = self.attrs.copy()
        attrs['link'] = attrs.pop('link', None)
        value = net.websafe(self.value or '')
        return '<a href="%s">%s</a>' % (attrs['link'], value)

class Dropdown(Input):
    r"""Dropdown/select input.
    
        >>> Dropdown(name='foo', args=['a', 'b', 'c'], value='b').render()
        '<select id="foo" name="foo">\n  <option value="a">a</option>\n  <option selected="selected" value="b">b</option>\n  <option value="c">c</option>\n</select>\n'
        >>> Dropdown(name='foo', args=[('a', 'aa'), ('b', 'bb'), ('c', 'cc')], value='b').render()
        '<select id="foo" name="foo">\n  <option value="a">aa</option>\n  <option selected="selected" value="b">bb</option>\n  <option value="c">cc</option>\n</select>\n'
    """
    def __init__(self, name, args, *validators, **attrs):
        self.args = args
        super(Dropdown, self).__init__(name, *validators, **attrs)

    def render(self):
        attrs = self.attrs.copy()
        attrs['name'] = self.name
        
        x = '<select %s>\n' % attrs
        
        for arg in self.args:
            if isinstance(arg, (tuple, list)):
                value, desc= arg
            else:
                value, desc = arg, arg 

            if self.value == value or (isinstance(self.value, list) and value in self.value):
                select_p = ' selected="selected"'
            else: select_p = ''
            x += '  <option%s value="%s">%s</option>\n' % (select_p, net.websafe(value), net.websafe(desc))
            
        x += '</select>\n'
        return x

class Radio(Input):
    def __init__(self, name, args, *validators, **attrs):
        self.args = args
        super(Radio, self).__init__(name, *validators, **attrs)

    def render(self):
        x = '<span>'
        for arg in self.args:
            if isinstance(arg, (tuple, list)):
                value, desc= arg
            else:
                value, desc = arg, arg 
            attrs = self.attrs.copy()
            attrs['name'] = self.name
            attrs['type'] = 'radio'
            attrs['value'] = value
            if self.value == value:
                attrs['checked'] = 'checked'
            x += '<input %s/> %s' % (attrs, net.websafe(desc))
        x += '</span>'
        return x

class Checkbox(Input):
    """Checkbox input.

    >>> Checkbox('foo', value='bar', checked=True).render()
    '<input checked="checked" type="checkbox" id="foo_bar" value="bar" name="foo"/>'
    >>> Checkbox('foo', value='bar').render()
    '<input type="checkbox" id="foo_bar" value="bar" name="foo"/>'
    >>> c = Checkbox('foo', value='bar')
    >>> c.validate('on')
    True
    >>> c.render()
    '<input checked="checked" type="checkbox" id="foo_bar" value="bar" name="foo"/>'
    """
    def __init__(self, name, *validators, **attrs):
        self.checked = attrs.pop('checked', False)
        Input.__init__(self, name, *validators, **attrs)
        
    def get_default_id(self):
        value = utils.safestr(self.value or "")
        return self.name + '_' + value.replace(' ', '_')

    def render(self):
        attrs = self.attrs.copy()
        attrs['type'] = 'checkbox'
        attrs['name'] = self.name
        attrs['value'] = self.value

        if self.checked:
            attrs['checked'] = 'checked'            
        return '<input %s/>' % attrs

    def set_value(self, value):
        self.checked = bool(value)

    def get_value(self):
        return self.checked

class Button(Input):
    """HTML Button.
    
    >>> Button("save").render()
    '<button id="save" name="save">save</button>'
    >>> Button("action", value="save", html="<b>Save Changes</b>").render()
    '<button id="action" value="save" name="action"><b>Save Changes</b></button>'
    """
    def __init__(self, name, type, *validators, **attrs):
        super(Button, self).__init__(name, *validators, **attrs)
        self.description = ""
        self.type = type

    def render(self):
        attrs = self.attrs.copy()
        attrs['name'] = self.name
        attrs['type'] = net.websafe(self.type)
        if self.value is not None:
            attrs['value'] = self.value
        html = attrs.pop('html', None) or net.websafe(self.name)
        return '<button %s>%s</button>' % (attrs, html)

class Strong(Input):
    def __init__(self, c, message, *validators, **attrs):
        super(Strong, self).__init__('', *validators, **attrs)
        self.description = ""
        self.c = c
        self.message = message
    
    def render(self):
        return '<strong class="%s">%s</strong>' % (self.c, self.message)

class Hidden(Input):
    """Hidden Input.
    
        >>> Hidden(name='foo', value='bar').render()
        '<input type="hidden" id="foo" value="bar" name="foo"/>'
    """
    def is_hidden(self):
        return True
        
    def get_type(self):
        return 'hidden'

class File(Input):
    """File input.
    
        >>> File(name='f').render()
        '<input type="file" id="f" name="f"/>'
    """
    def get_type(self):
        return 'file'
    
class Validator:
    def __deepcopy__(self, memo): return copy.copy(self)
    def __init__(self, msg, test, jstest=None): utils.autoassign(self, locals())
    def valid(self, value): 
        try: return self.test(value)
        except: return False

notnull = Validator("Required", bool)

class regexp(Validator):
    def __init__(self, rexp, msg):
        self.rexp = re.compile(rexp)
        self.msg = msg
    
    def valid(self, value):
        return bool(self.rexp.match(value))

if __name__ == "__main__":
    import doctest
    doctest.testmod()
