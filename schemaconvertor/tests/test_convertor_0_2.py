#!/usr/bin/env python
# encoding: utf-8

from unittest import TestCase

from schemaconvertor.convertor import (
    Schema, SchemaConst, ObjAsDictAdapter)


class TestObjAsDictAdapter(TestCase):
    class Parent(object):
        pclsval = 1

        def __init__(self):
            self.pinsval = 2

    class Child(Parent):
        cclsval = 3

        def __init__(self):
            super(TestObjAsDictAdapter.Child, self).__init__()
            self.cinsval = 4

        def __getattr__(self, name):
            if name == "dynamicval":
                return 5

    def test_base_method(self):
        parent = self.Parent()
        parent_dict = ObjAsDictAdapter(parent)

        self.assertEqual(parent_dict["pclsval"], parent.pclsval)
        self.assertEqual(parent_dict["pinsval"], parent.pinsval)
        self.assertIn("pclsval", iter(parent_dict))
        self.assertIn("pinsval", iter(parent_dict))

    def test_inherit(self):
        child = self.Child()
        child_dict = ObjAsDictAdapter(child)

        self.assertEqual(child_dict["pclsval"], child.pclsval)
        self.assertEqual(child_dict["pinsval"], child.pinsval)
        self.assertEqual(child_dict["cclsval"], child.cclsval)
        self.assertEqual(child_dict["cinsval"], child.cinsval)
        self.assertIn("pclsval", iter(child_dict))
        self.assertIn("pinsval", iter(child_dict))
        self.assertIn("cclsval", iter(child_dict))
        self.assertIn("cinsval", iter(child_dict))

    def test_dynamic_attr(self):
        child = self.Child()
        child_dict = ObjAsDictAdapter(child)

        self.assertEqual(child_dict["dynamicval"], child.dynamicval)
        self.assertNotIn("dynamicval", iter(child_dict))

        child.dynamicval = 6
        self.assertEqual(child_dict["dynamicval"], child.dynamicval)
        self.assertIn("dynamicval", iter(child_dict))


class TestSchema(TestCase):
    def test_field_default_value(self):
        schema = Schema({})
        self.assertEqual(schema.version, schema.VERSION)
        self.assertEqual(schema.origin_schema, {})
        self.assertEqual(schema.parent, None)
        self.assertEqual(schema.compiled, False)  # lazy
        self.assertEqual(schema.type, SchemaConst.S_UNDEFINED)
        self.assertEqual(schema.items, SchemaConst.S_DISABLED)
        self.assertEqual(schema.properties_schemas, SchemaConst.S_DISABLED)
        self.assertEqual(schema.pattern_properties_schemas, SchemaConst.S_DISABLED)
        self.assertEqual(schema.typeof_schemas, SchemaConst.S_DISABLED)
        self.assertEqual(schema.typeof_default_schema, SchemaConst.S_DISABLED)
        self.assertEqual(schema.compiled, True)

    def test_version(self):
        schema = Schema({
            "type": "string"
        })
        self.assertEqual(schema.version, Schema.VERSION)
        self.assertTrue(schema.check_version())

        schema = Schema({
            "version": Schema.VERSION,
            "type": "string"
        })
        self.assertEqual(schema.version, Schema.VERSION)
        self.assertTrue(schema.check_version())

        schema = Schema({
            "version": "0.2",
            "type": "string"
        })
        self.assertNotEqual(schema.version, Schema.VERSION)
        self.assertTrue(schema.check_version())

        schema = Schema({
            "version": "0.0.0.0",
            "type": "string"
        })
        self.assertEqual(schema.version, "0.0.0.0")
        self.assertFalse(schema.check_version())

        schema = Schema({
            "version": "0.0.0.0",
            "type": "array",
            "items": {
                "type": "string"
            }
        })
        self.assertEqual(schema.version, "0.0.0.0")
        self.assertEqual(schema.items.version, "0.0.0.0")

    def test_parent(self):
        schema = Schema({
            "version": "0.2",
            "type": "array",
            "items": {
                "type": "string"
            }
        })
        self.assertIs(schema.items.parent, schema)
        self.assertIs(schema.parent, None)

    def test_short(self):
        schema1 = Schema({
            "version": "0.2",
            "type": "array",
            "items": "string"
        })
        schema2 = Schema({
            "version": "0.2",
            "type": "array",
            "items": {
                "type": "string"
            }
        })
        self.assertEqual(schema1.items.type, schema2.items.type)

        schema = Schema("string")
        self.assertEqual(schema.type, "string")
