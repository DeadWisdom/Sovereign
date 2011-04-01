import bisect

DEFAULT = ((),)

class Settings(object):
    def __init__(self, levels):
        self.fieldsets = []
        self.fields = {}
        self.values = {}
        self.levels = dict((str(x), i) for i, x in enumerate(levels))
        self.order = tuple(range(len(levels) - 1, -1, -1))

    def __iter__(self):
        return iter(self.fieldsets)
    
    def add(self, fieldset):
        for field in fieldset:
            for other in self.fieldsets:
                if field.key in other:
                    other.add(field)
                    fieldset.remove(field.key)
            self.fields[field.key] = field
            self.values.setdefault(field.key, {})[0] = field.default
        if fieldset._keys:
            self.fieldsets.append(fieldset)
    
    def extend(self, fieldsets):
        for fieldset in fieldsets:
            self.add(fieldset)
    
    def defaults(self):
        defaults = {}
        for fieldset in self:
            for k, field in fieldset.items():
                defaults[k] = field.default
        return defaults
    
    def get(self, k, default=None, level=None):
        values = self.values.get(k, DEFAULT)
        if values is DEFAULT:
            return default
        if level is not None:
            return values.get(self.levels[level], default)
        for level in self.order:
            answer = values.get(level, DEFAULT)
            if answer is not DEFAULT:
                return answer
        return default
    
    def __getitem__(self, k):
        answer = self.get(k, DEFAULT)
        if answer is DEFAULT:
            raise KeyError(k)
        return answer
    
    def set(self, k, v, level=None):
        if level is None:
            level = self.order[0]
        else:
            level = self.levels[level]
        self.values.setdefault(k, {})[level] = v
    
    def __setitem__(self, k, v):
        self.set(k, v)
    
    def flat(self, level=None):
        results = {}
        for k, values in self.values.items():
            v = self.get(k, DEFAULT, level)
            if v is DEFAULT:
                continue
            results[k] = v
        return results

    def update(self, dct, level=None):
        for k, v in dct.items():
            self.set(k, v, level)


class Fieldset(object):
    __slots__ = ['name', '_dict', '_keys']
    
    def __unicode__(self):
        items = "\n".join("%s: %r" % pair for pair in self.items())
        return "%s {\n%s\n}" % (self.name, items)

    def __init__(self, name, fields=None):
        self.name = name
        self._dict = {}
        self._keys = []
        for field in fields:
            self.add(field)
    
    def add(self, field):
        k = field.key
        if (k in self._dict):
            del self._dict[k]
        else:
            self._keys.append(k)
        self._dict[k] = field

    def remove(self, key):
        del self._dict[key]
        self._keys.remove(key)

    def __getitem__(self, k):
        return self._dict[k]
    
    def __iter__(self):
        return self.values()

    def __contains__(self, k):
        return k in self._dict

    def keys(self):
        return self._keys
    
    def values(self):
        return (self._dict[k] for k in self._keys)
    
    def items(self):
        return ((k, self._dict[k]) for k in self._keys)


class Field(object):
    """
    Base field for settings.
    """
    def __init__(self, key=None, default=None, help=None):
        self.key = str(key)
        self.default = default
        self.help = str(help or '')
        
        #For Debugging:
        #self.from_simple(self.to_simple(default))
    
    def get_simple(self, val):
        if (val is None): return None
        return self.to_simple(val)
    
    def to_simple(self, val):
        return val
    
    def from_simple(self, val):
        return self.to_simple(val)
    
    def to_yaml(self, val):
        return "%s: %r" % (self.key, self.to_simple(val))


class StringField(Field):
    def to_simple(self, val):
        return unicode(val)


class IdField(StringField):
    def to_simple(self, val):
        return str(val).lower()


class BoolField(Field):
    def to_simple(self, val):
        return bool(val)


class NoteField(StringField):
    """
    Exactly like a StringField, but expected to be long.
    """
    def to_yaml(self, val):
        return "%s:\n    %s" % (self.key, self.to_simple(val))


class IntegerField(Field):
    def to_simple(self, val):
        return int(val)


class FloatField(Field):
    def to_simple(self, val):
        return float(val)


class AddressField(Field):
    """
    Represents an internet address: [hostname -> str, port -> int]
    """
    def to_simple(self, val):
        return str(val[0] or '*'), int(val[1])
    

class StringList(Field):
    """
    A list of strings.
    """
    def to_simple(self, val):
        return [str(x) for x in val]
    

class StringDict(Field):
    """
    A dictionary of mapping str -> str.
    """
    def to_simple(self, val):
        return dict((k, v) for k, v in val.items())

    def to_yaml(self, val):
        val = self.to_simple(val)
        items = ["%s: %r" % t for t in val.items()]
        return "%s:\n    %s" % (self.key, "\n     ".join(items))
