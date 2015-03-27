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


class Schema(object):
    VERSION = "0.2"

    def __init__(self, schema):
        if isinstance(schema, basestring):
            schema = {"type": schema}

        self.version = schema.get(SchemaConst.F_VERSION, self.VERSION)
        self.type = schema.get(SchemaConst.F_TYPE)

        items = schema.get(SchemaConst.F_ITEMS)
        self.items = Schema(items) if items else None

        properties = schema.get(SchemaConst.F_PROPERTIES)
        self.properties_schemas = None if properties is None else {
            k: Schema(s) for k, s in properties.iteritems()
        }

        typeof_schemas = schema.get(SchemaConst.F_TYPEOF)
        self.typeof_schemas = None if typeof_schemas is None else {
            types.NoneType if t is None else t: Schema(s)
            for t, s in typeof_schemas.iteritems()
            if isinstance(t, (type, tuple))
        }
        self.typeof_default_schema = None if typeof_schemas is None \
            else Schema(typeof_schemas.get(
                SchemaConst.F_DEFAULT, SchemaConst.T_DEFAULT))

        p_schemas = schema.get(SchemaConst.F_PATTERNPROPERTIES)
        self.pattern_properties_schemas = None if p_schemas is None else {
            re.compile(p): Schema(s) for p, s in p_schemas.iteritems()
        }

    def check_version(self):
        """Check version if is available
        """
        return self.version in ("0.2", "0.1")

    def properties(self, name, istry=False):
        """Get sub shcema by name
        """
        if name in self.properties_schemas:
            return self.properties_schemas.get(name)
        if not istry:
            raise FieldMissError(
                "field %s is miss in %s" % (name, SchemaConst.F_PROPERTIES))

    def typeof(self, data, istry=False):
        """Get sub schema by data type
        """
        if self.typeof_schemas is None:
            if istry:
                return None
            raise FieldMissError("field %s is miss" % SchemaConst.F_TYPEOF)

        for typ, sch in self.typeof_schemas.iteritems():
            if isinstance(data, typ):
                return sch
        return self.typeof_default_schema

    def pattern_properties(self, name, istry=False):
        """Get sub schema by name pattern
        """
        if self.pattern_properties_schemas is None:
            if istry:
                return None
            raise FieldMissError(
                "field %s is miss" % SchemaConst.F_PATTERNPROPERTIES)

        for rex, sch in self.pattern_properties_schemas.iteritems():
            if rex.match(name):
                return sch
        return None


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
        for key in data:
            real_data = data[key]
            real_schema = schema.properties(key, istry=True)
            if not real_schema:
                real_schema = schema.pattern_properties(key, istry=True)
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
        for item in data:
            real_schema = schema.items or schema.typeof(item)
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
        if real_schema:
            return self._convertor(data, real_schema)
        return self._null_convertor(data, schema)

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
        None: _auto_type_convertor,
    }
