#!/usr/bin/env python
# encoding: utf-8

import re
import collections

from schemaconvertor import builtin_hooks

try:
    unicode = unicode
except NameError:
    unicode = str


class Types:
    NoneType = type(None)
    IntType = int
    FloatType = float
    BooleanType = bool

__version__ = '0.3.1.2'


def _type_convertor(type_):
    """Type convertor builder
    """
    def _base_convertor(self, data, schema):
        """Convert data to given type
        """
        return type_(data)
    return _base_convertor


SchemaVersionError = type("SchemaVersionError", (ValueError,), {})
FieldTypeError = type("FieldTypeError", (TypeError,), {})
FieldMissError = type("FieldMissError", (KeyError,), {})


class ObjAsDictAdapter(collections.Mapping):
    def __init__(self, obj):
        self.__object = obj

    def __getitem__(self, name):
        try:
            return getattr(self.__object, name)
        except AttributeError:
            raise KeyError(name)

    def __setitem__(self, name, value):
        setattr(self.__object, name, value)

    def __iter__(self):
        return iter(dir(self.__object))

    def __len__(self):
        return len(dir(self.__object))


class SchemaConst(object):
    # schema types
    T_STR = "string"
    T_OBJ = "object"
    T_INT = "integer"
    T_FLOAT = "float"
    T_NUM = "number"
    T_BOOL = "boolean"
    T_DICT = "dict"
    T_LIST = "array"
    T_NULL = "null"
    T_RAW = "raw"
    T_DEFAULT = T_STR

    # schema fields
    F_TYPE = "type"
    F_VERSION = "version"
    F_DEFAULT = "default"
    F_PROPERTIES = "properties"
    F_ITEMS = "items"
    F_TYPEOF = "typeOf"
    F_PATTERNPROPERTIES = "patternProperties"
    F_ENCODING = "encoding"
    F_DECODERR = "decoderrors"
    F_DESCRIPTION = "description"
    F_HOOK = "hook"
    F_HOOK_PRECONVERT = "pre-convert"
    F_HOOK_POSTCONVERT = "post-convert"

    # field states
    S_UNDEFINED = None
    S_DISABLED = frozenset()

    # const values
    V_ENCODING = "utf-8"
    V_DECODERR = "strict"


class SchemaBuiltinHook(object):
    Pre_Convert_Hook = {
        "format_date": builtin_hooks.format_date,
        "func_result": builtin_hooks.func_result,
    }
    Post_Convert_Hook = {
    }


class Schema(object):
    VERSION = __version__
    VERVERIFYREX = re.compile(r"0\.[1-3].*")

    def __init__(self, schema, parent=None):
        if isinstance(schema, (str, unicode)):
            schema = {"type": schema}

        self.origin_schema = schema
        self.parent = parent
        self.version = schema.get(
            SchemaConst.F_VERSION,
            parent.version if parent else self.VERSION)
        self.description = str(schema.get(
            SchemaConst.F_DESCRIPTION,
            parent.description if parent else self.__class__))
        self.compiled = False

    def __getattr__(self, name):
        self.compile()
        return super(Schema, self).__getattribute__(name)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.origin_schema)

    def __str__(self):
        return "<Schema: %s>" % self.description

    def compile(self):
        """compile schema
        """
        if self.compiled:
            return

        schema = self.origin_schema
        self.type = schema.get(SchemaConst.F_TYPE, SchemaConst.S_UNDEFINED)

        items = schema.get(SchemaConst.F_ITEMS)
        self.items = self.subschema(items) if items else SchemaConst.S_DISABLED

        properties = schema.get(SchemaConst.F_PROPERTIES)
        self.properties_schemas = SchemaConst.S_DISABLED \
            if properties is None else {
                k: self.subschema(s) for k, s in properties.iteritems()
            }

        typeof_schemas = schema.get(SchemaConst.F_TYPEOF)
        self.typeof_schemas = SchemaConst.S_DISABLED \
            if typeof_schemas is None else {
                Types.NoneType if t is None else t: self.subschema(s)
                for t, s in typeof_schemas.iteritems()
                if isinstance(t, (type, tuple, Types.NoneType))
            }
        self.typeof_default_schema = SchemaConst.S_DISABLED \
            if typeof_schemas is None else self.subschema(typeof_schemas.get(
                SchemaConst.F_DEFAULT, SchemaConst.T_DEFAULT))

        p_schemas = schema.get(SchemaConst.F_PATTERNPROPERTIES)
        self.pattern_properties_schemas = SchemaConst.S_DISABLED \
            if p_schemas is None else {
                re.compile(p): self.subschema(s)
                for p, s in p_schemas.iteritems()
            }

        self.encoding = schema.get(
            SchemaConst.F_ENCODING,
            self.parent.encoding if self.parent else SchemaConst.V_ENCODING)
        self.decoderrors = schema.get(
            SchemaConst.F_DECODERR,
            self.parent.decoderrors if self.parent else SchemaConst.V_DECODERR)

        self.hooks = schema.get(SchemaConst.F_HOOK, {})

        self.hooks[SchemaConst.F_HOOK_PRECONVERT] = [
            SchemaBuiltinHook.Pre_Convert_Hook.get(hook, hook)
            for hook in self.hooks.get(SchemaConst.F_HOOK_PRECONVERT, [])
        ]
        self.hooks[SchemaConst.F_HOOK_POSTCONVERT] = [
            SchemaBuiltinHook.Post_Convert_Hook.get(hook, hook)
            for hook in self.hooks.get(SchemaConst.F_HOOK_POSTCONVERT, [])
        ]

        self.compiled = True

    def check_version(self):
        """Check version if is available
        """
        return self.VERVERIFYREX.match(self.version) is not None

    def properties(self, name, istry=False):
        """Get sub shcema by name
        """
        if self.properties_schemas is SchemaConst.S_DISABLED:
            return SchemaConst.S_UNDEFINED

        if name in self.properties_schemas:
            return self.properties_schemas.get(name, SchemaConst.S_UNDEFINED)
        if not istry:
            raise FieldMissError(
                "field %s is miss in %s" % (name, SchemaConst.F_PROPERTIES))

    def typeof(self, data, istry=False):
        """Get sub schema by data type
        """
        if self.typeof_schemas is SchemaConst.S_DISABLED:
            if istry:
                return SchemaConst.S_UNDEFINED
            raise FieldMissError("field %s is miss" % SchemaConst.F_TYPEOF)

        sch = self.typeof_schemas.get(type(data), SchemaConst.S_UNDEFINED)
        if sch is not SchemaConst.S_UNDEFINED:
            return sch

        for typ, sch in self.typeof_schemas.iteritems():
            if isinstance(data, typ):
                return sch
        return self.typeof_default_schema

    def pattern_properties(self, name, istry=False):
        """Get sub schema by name pattern
        """
        if self.pattern_properties_schemas is SchemaConst.S_DISABLED:
            if istry:
                return SchemaConst.S_UNDEFINED
            raise FieldMissError(
                "field %s is miss" % SchemaConst.F_PATTERNPROPERTIES)

        for rex, sch in self.pattern_properties_schemas.iteritems():
            if rex.search(name):
                return sch
        return SchemaConst.S_UNDEFINED

    def subschema(self, sch):
        """create a subschema
        """
        return Schema(sch, self)


class SchemaConvertor(object):
    def __init__(self, schema):
        if not isinstance(schema, Schema):
            schema = Schema(schema)

        if schema.check_version() is False:
            raise SchemaVersionError()

        self.schema = schema

    def __call__(self, data):
        return self._convertor(data, self.schema)

    def _convertor(self, data, schema):
        """Main convertor
        """
        convertor = self.CONVERTORS.get(schema.type)
        if convertor is None:
            raise TypeError("Unknown type: %s" % schema.type)

        for hook in schema.hooks[SchemaConst.F_HOOK_PRECONVERT]:
            data = hook(data, schema)

        result = convertor(self, data, schema)

        for hook in schema.hooks[SchemaConst.F_HOOK_POSTCONVERT]:
            result = hook(result, schema)

        return result

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, repr(self.schema))

    def __str__(self):
        return "<SchemaConvertor: %s>" % self.schema

    def _dict_convertor(self, data, schema):
        """Dict convertor
        """
        result = {}
        if schema.pattern_properties_schemas is not SchemaConst.S_DISABLED:
            for key in data:
                real_data = data[key]
                real_schema = schema.pattern_properties(key, istry=True)
                if real_schema:
                    result[key] = self._convertor(real_data, real_schema)

        if schema.properties_schemas is not SchemaConst.S_DISABLED:
            for key in schema.properties_schemas:
                real_data = data[key]
                real_schema = schema.properties(key)
                if real_schema:
                    result[key] = self._convertor(real_data, real_schema)

        return result

    def _object_convertor(self, data, schema):
        """Object convertor
        """
        return self._dict_convertor(ObjAsDictAdapter(data), schema)

    def _array_convertor(self, data, schema):
        """iterable object convertor
        """
        result = []
        real_schema = schema.items
        if real_schema is not SchemaConst.S_DISABLED:
            for item in data:
                result.append(self._convertor(item, real_schema))
        return result

    def _number_convertor(self, data, schema):
        """Auto number convertor
        """
        num = float(data)
        if num.is_integer():
            num = int(num)
        return num

    def _null_convertor(self, data, schema):
        """Return None forever
        """
        return None

    def _raw_convertor(self, data, schema):
        """Return the raw object forever
        """
        return data

    def _auto_type_convertor(self, data, schema):
        """when schema.type is None
        """
        real_schema = schema.typeof(data, istry=True)
        if real_schema is not SchemaConst.S_UNDEFINED:
            return self._convertor(data, real_schema)
        return self._null_convertor(data, schema)

    def _str_convertor(self, data, schema):
        """auto unicode string convertor
        """
        if schema.encoding is None:
            return data

        if isinstance(data, unicode):
            return data

        data = str(data)
        return data.decode(schema.encoding, schema.decoderrors)

    CONVERTORS = {
        SchemaConst.T_STR: _str_convertor,
        SchemaConst.T_INT: _type_convertor(Types.IntType),
        SchemaConst.T_FLOAT: _type_convertor(Types.FloatType),
        SchemaConst.T_BOOL: _type_convertor(Types.BooleanType),
        SchemaConst.T_NUM: _number_convertor,
        SchemaConst.T_DICT: _dict_convertor,
        SchemaConst.T_OBJ: _object_convertor,
        SchemaConst.T_LIST: _array_convertor,
        SchemaConst.T_NULL: _null_convertor,
        SchemaConst.T_RAW: _raw_convertor,
        None: _auto_type_convertor,
    }


def convert_by_schema(data, schema):
    """a quick tool to convert data by schema
    """
    cvtr = SchemaConvertor(schema)
    return cvtr(data)
