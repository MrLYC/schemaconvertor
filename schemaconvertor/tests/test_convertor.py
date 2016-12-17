#!/usr/bin/env python
# encoding: utf-8

from unittest import TestCase

from schemaconvertor import convertor


class TestObjAsDictAdapter(TestCase):

    def test_setitem(self):
        class MockObject(object):
            val = 1

        mock_object = MockObject()
        adapter = convertor.ObjAsDictAdapter(mock_object)
        adapter["val"] = 2
        self.assertEqual(mock_object.val, 2)


class TestSchema(TestCase):

    def test_compile(self):
        schema = convertor.Schema({
            "type": "dict",
            "properties": {
                "integer": {
                    "type": "integer",
                },
            },
        })
        schema.compile()
        schema.compile()  # compile twice

    def test_str_method(self):
        description = str(id(self))
        schema = convertor.Schema({"description": description})
        self.assertIn(description, str(schema))

    def test_repr_method(self):
        Schema = convertor.Schema
        schema = Schema({})
        eval(repr(schema))


class TestConvertor(TestCase):

    def test_check_version(self):
        with self.assertRaises(convertor.SchemaVersionError):
            convertor.SchemaConvertor({
                "version": "0.0.0.0",
            })
