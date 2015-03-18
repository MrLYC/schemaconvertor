#!/usr/bin/env python
# encoding: utf-8

import types


def _type_convertor(type_):
    def _base_convertor(self, schema, data):
        return type_(data)
    return _base_convertor


class SchemaConvertor(object):
    def _convertor(self, schema, data):
        type_ = schema if isinstance(schema, (str, unicode)) \
            else schema.get("type", self.DEFAULT_TYPE)

        convertor = self.CONVERTORS.get(type_)
        if convertor is None:
            raise TypeError("Unknown type: %s" % type_)

        return convertor(self, schema, data)

    def _dict_convertor(self, schema, data):
        properties = schema.get("properties", {})
        return {
            k: self._convertor(s, data[k])
            for k, s in properties.iteritems()}

    def _object_convertor(self, schema, data):
        properties = schema.get("properties", {})
        return {
            k: self._convertor(s, getattr(data, k))
            for k, s in properties.iteritems()}

    def _array_convertor(self, schema, data):
        sub_schema = schema.get("items", {})
        return [
            self._convertor(sub_schema, d) for d in data]

    def _number_convertor(self, schema, data):
        num = types.FloatType(data)
        if num.is_integer():
            num = int(num)
        return num

    def _null_convertor(self, schema, data):
        return None

    def _raw_convertor(self, schema, data):
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
        return self._convertor(self.schema, data)


def to_dict_by_schema(data, schema):
    cvtr = SchemaConvertor(schema)
    return cvtr(data)
