import bisect

DEFAULT = ((),) 

class Settings(object):
    levels = ["user", "config", "default"]
    
    def __init__(self, fieldsets=()):
        self.fieldsets = []
        self.fields = {}
        self.values = [{}] * len(self.levels)
        self.level_map = dict((str(x), i) for i, x in enumerate(self.levels))
        self.extend(fieldsets)

    def __iter__(self):
        return iter(self.fieldsets)
    
    def add(self, fieldset):
        for field in tuple( fieldset.values() ):
            for other in self.fieldsets:
                if field.key in other:
                    other.add(field)
                    fieldset.remove(field.key)
            self.fields[field.key] = field
            self.values[-1][field.key] = field.default
        if fieldset._keys:
            self.fieldsets.append(fieldset)
    
    def extend(self, fieldsets):
        for fieldset in fieldsets:
            self.add(fieldset)
    
    def defaults(self):
        return self.values[-1]
    
    def get(self, k, default=None, level=None):
        if level is not None:
            return self.values[self.level_map[level]].get(k, default)
        for dct in self.values:
            v = dct.get(k, DEFAULT)
            if v is not DEFAULT:
                return v
        return default
    
    def __getitem__(self, k):
        for dct in self.values:
            v = dct.get(k, DEFAULT)
            if v is not DEFAULT:
                return v
        raise KeyError(k)
    
    def set(self, k, v, level=None):
        if level is None:
            dct = self.values[0]
        else:
            dct = self.values[self.level_map[level]]
        dct[k] = v
    
    def __setitem__(self, k, v):
        self.set(k, v)
    
    def flat(self, level=None):
        results = {}
        if level is None:
            for dct in self.values:
                results.update(dct)
        else:
            dct = self.values[self.level_map[level]]
            results.update(dct)
        return results

    def update(self, o, level=None):
        if level is None:
            dct = self.values[0]
        else:
            dct = self.values[self.level_map[level]]
        dct.update(o)


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
