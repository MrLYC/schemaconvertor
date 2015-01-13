#!/usr/bin/env python
# encoding: utf-8

import types
import re


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


class ObjectAsDict(object):
    def __init__(self, obj):
        self.__object = obj

    def __getitem__(self, name):
        return getattr(self.__object, name)

    def __setitem__(self, name, value):
        setattr(self.__object, name, value)


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

    # schema fields
    F_TYPE = "type"
    F_SOURCE = "source"
    F_VERSION = "version"
    F_DEFAULT = "default"
    F_PROPERTIES = "properties"
    F_ITEMS = "items"
    F_TYPEOF = "typeOf"
    F_PATTERNPROPERTIES = "patternProperties"


class Schema(object):
    VERSION = "0.2"

    def __init__(self, schema):
        if isinstance(schema, basestring):
            schema = {"type": schema}

        self.version = schema.get(SchemaConst.F_VERSION, self.VERSION)
        self.type = schema.get(SchemaConst.F_TYPE, SchemaConst.T_STR)
        self.source = schema.get(SchemaConst.F_SOURCE)

        items = schema.get(SchemaConst.F_ITEMS)
        self.items = items and Schema(items)

        properties = schema.get(SchemaConst.F_PROPERTIES)
        self.properties = properties and {
            k: Schema(s) for k, s in properties.iteritems()
        }

        typeof_schemas = schema.get(SchemaConst.F_TYPEOF)
        self.typeof_schemas = typeof_schemas and {
            t: Schema(s) for t, s in typeof_schemas.iteritems()
        }

        pattern_schemas = schema.get(SchemaConst.F_PATTERNPROPERTIES)
        self.pattern_properties_schemas = pattern_schemas and {
            re.compile(p): Schema(s) for p, s in pattern_schemas.iteritems()
        }

    def check_version(self):
        """Check version if is available
        """
        return self.version == self.VERSION

    def typeof_sub_schema(self, data):
        """Get sub schema by data type
        """
        for typ, sch in self.typeof_schemas.iteritems():
            if isinstance(typ, (type, tuple)) and isinstance(data, typ):
                return sch
        return self.typeof_schemas.get(SchemaConst.F_DEFAULT)

    def pattern_sub_schema(self, name):
        """Get sub schema by name pattern
        """
        for rex, sch in self.pattern_properties_schemas.iteritems():
            if rex.match(name):
                return sch
        return None

    def real_schema(self, name, data):
        """Get real schema
        """
        if self.typeof_schemas:
            sch = self.typeof_sub_schema(data)
            if sch is not None:
                return sch
        if isinstance(name, basestring) and self.pattern_properties_schemas:
            sch = self.pattern_sub_schema(name)
            if sch is not None:
                return sch
        return self


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
        for key, sch in schema.properties.iteritems():
            name = sch.source or key
            real_data = data[name]
            real_schema = sch.real_schema(name, real_data)
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
        for item in data:
            real_schema = schema.items.real_schema(None, item)
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

    CONVERTORS = {
        SchemaConst.T_STR: _type_convertor(types.StringType),
        SchemaConst.T_INT: _type_convertor(types.IntType),
        SchemaConst.T_FLOAT: _type_convertor(types.FloatType),
        SchemaConst.T_BOOL: _type_convertor(types.BooleanType),
        SchemaConst.T_NUM: _number_convertor,
        SchemaConst.T_DICT: _dict_convertor,
        SchemaConst.T_OBJ: _object_convertor,
        SchemaConst.T_LIST: _array_convertor,
        SchemaConst.T_NULL: _null_convertor,
        SchemaConst.T_RAW: _raw_convertor,
    }
    DEFAULT_TYPE = SchemaConst.T_STR
