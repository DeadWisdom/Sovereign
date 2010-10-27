
class Field(object):
    """
    Base field for settings.
    """
    def __init__(self, key=None, default=None, help=None):
        self.key = str(key)
        self.default = default
        self.help = str(help or '')
        
        self.from_simple(self.to_simple(default))
    
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
