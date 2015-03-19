#!/usr/bin/env python
# encoding: utf-8

import types


def _type_convertor(type_):
    """Type convertor builder
    """
    def _base_convertor(self, data, schema):
        """Convert data to given type
        """
        return type_(data)
    return _base_convertor


def _get_sub_schema(data, schema):
    """Get the real schema based on type(data)
    """
    sch = schema.get(type(data))
    if sch is not None:
        return sch

    default_schema = schema.get("default")
    for typ, sch in schema.iteritems():
        # can use None as NoneType directly
        if data is None and type is None:
            return sch
        # maybe is a subclass of typ
        if isinstance(typ, (type, tuple)) and isinstance(data, typ):
            return sch
    else:
        if default_schema is None:
            raise TypeError("Unknown type: %s", type(data))
    return default_schema


class SchemaConvertor(object):
    def _convertor(self, data, schema):
        """Main convertor
        """
        # "key": "string" == "key": {"type": "string"}
        is_short_schema = isinstance(schema, (str, unicode))

        if not is_short_schema:
            schemas = schema.get("typeOf")
            if schemas:
                return self._convertor(
                    data, _get_sub_schema(data, schemas))

        type_ = schema if is_short_schema \
            else schema.get("type", self.DEFAULT_TYPE)

        convertor = self.CONVERTORS.get(type_)
        if convertor is None:
            raise TypeError("Unknown type: %s" % type_)

        return convertor(self, data, schema)

    def _dict_convertor(self, data, schema):
        """Dict like object convertor(has __getitem__ attr)
        """
        properties = schema.get("properties", {})
        return {
            k: self._convertor(data[k], s)
            for k, s in properties.iteritems()}

    def _object_convertor(self, data, schema):
        """Object convertor
        """
        properties = schema.get("properties", {})
        return {
            k: self._convertor(getattr(data, k), s)
            for k, s in properties.iteritems()}

    def _array_convertor(self, data, schema):
        """iterable object convertor
        """
        sub_schema = schema.get("items", {})
        return [
            self._convertor(d, sub_schema) for d in data]

    def _number_convertor(self, data, schema):
        """Auto number convertor
        """
        num = types.FloatType(data)
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
        "string": _type_convertor(types.StringType),
        "integer": _type_convertor(types.IntType),
        "float": _type_convertor(types.FloatType),
        "boolean": _type_convertor(types.BooleanType),
        "number": _number_convertor,
        "dict": _dict_convertor,
        "object": _object_convertor,
        "array": _array_convertor,
        "null": _null_convertor,
        "raw": _raw_convertor,
    }
    DEFAULT_TYPE = "string"

    def __init__(self, schema):
        self.schema = schema

    def __call__(self, data):
        return self._convertor(data, self.schema)


def to_dict_by_schema(data, schema):
    """A shortcut to convert data by schema
    """
    cvtr = SchemaConvertor(schema)
    return cvtr(data)
