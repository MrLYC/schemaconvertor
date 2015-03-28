#!/usr/bin/env python
# encoding: utf-8

import types
import re

__version__ = '0.2.2.1'


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


class ObjectAsDict(object):
    def __init__(self, obj):
        self.__object = obj

    def __getitem__(self, name):
        return getattr(self.__object, name)

    def __setitem__(self, name, value):
        setattr(self.__object, name, value)

    def __iter__(self):
        return iter(dir(self.__object))


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

    # field states
    S_UNDEFINED = None
    S_DISABLED = frozenset()


class Schema(object):
    VERSION = __version__
    VERVERIFYREX = re.compile(r"0\.[1-2].*")

    def __init__(self, schema):
        if isinstance(schema, basestring):
            schema = {"type": schema}

        self.version = schema.get(SchemaConst.F_VERSION, self.VERSION)
        self.type = schema.get(SchemaConst.F_TYPE, SchemaConst.S_UNDEFINED)

        items = schema.get(SchemaConst.F_ITEMS)
        self.items = Schema(items) if items else SchemaConst.S_DISABLED

        properties = schema.get(SchemaConst.F_PROPERTIES)
        self.properties_schemas = SchemaConst.S_DISABLED \
            if properties is None else {
                k: Schema(s) for k, s in properties.iteritems()
            }

        typeof_schemas = schema.get(SchemaConst.F_TYPEOF)
        self.typeof_schemas = SchemaConst.S_DISABLED \
            if typeof_schemas is None else {
                types.NoneType if t is None else t: Schema(s)
                for t, s in typeof_schemas.iteritems()
                if isinstance(t, (type, tuple, types.NoneType))
            }
        self.typeof_default_schema = SchemaConst.S_DISABLED \
            if typeof_schemas is None else Schema(typeof_schemas.get(
                SchemaConst.F_DEFAULT, SchemaConst.T_DEFAULT))

        p_schemas = schema.get(SchemaConst.F_PATTERNPROPERTIES)
        self.pattern_properties_schemas = SchemaConst.S_DISABLED \
            if p_schemas is None else {
                re.compile(p): Schema(s) for p, s in p_schemas.iteritems()
            }

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
            if rex.match(name):
                return sch
        return SchemaConst.S_UNDEFINED


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

        return convertor(self, data, schema)

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
        return self._dict_convertor(ObjectAsDict(data), schema)

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

    CONVERTORS = {
        SchemaConst.T_STR: _type_convertor(types.UnicodeType),
        SchemaConst.T_INT: _type_convertor(types.IntType),
        SchemaConst.T_FLOAT: _type_convertor(types.FloatType),
        SchemaConst.T_BOOL: _type_convertor(types.BooleanType),
        SchemaConst.T_NUM: _number_convertor,
        SchemaConst.T_DICT: _dict_convertor,
        SchemaConst.T_OBJ: _object_convertor,
        SchemaConst.T_LIST: _array_convertor,
        SchemaConst.T_NULL: _null_convertor,
        SchemaConst.T_RAW: _raw_convertor,
        None: _auto_type_convertor,
    }


def to_dict_by_schema(data, schema):
    """a quick tool to convert data by schema
    """
    cvtr = SchemaConvertor(schema)
    return cvtr(data)
