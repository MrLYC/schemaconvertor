#!/usr/bin/env python
# encoding: utf-8

from unittest import TestCase
from collections import namedtuple

from schemaconvertor import convertor

Pair = namedtuple("Pair", ["key", "value"])


class TestSimple(TestCase):
    def test_base_type(self):
        data = {
            "string": "1",
            "integer": 2,
            "float": 3.4,
            "number_integer": 5,
            "number_float": 6.7,
            "number_str": "8.9",
            "number_asinteger": 10.0,
            "boolean": True,
            "null": None,
        }

        schema = {
            "type": "dict",
            "properties": {
                "string": {
                    "type": "string"
                },
                "integer": {
                    "type": "integer"
                },
                "float": {
                    "type": "float"
                },
                "number_integer": {
                    "type": "number"
                },
                "number_float": {
                    "type": "number"
                },
                "number_str": {
                    "type": "number"
                },
                "number_asinteger": {
                    "type": "number"
                },
                "boolean": {
                    "type": "boolean"
                },
                "null": {
                    "type": "null"
                },
            }
        }
        cvtr = convertor.SchemaConvertor(schema)
        result = cvtr(data)
        self.assertDictEqual(result, {
            "string": "1",
            "integer": 2,
            "float": 3.4,
            "number_integer": 5,
            "number_float": 6.7,
            "number_str": 8.9,
            "number_asinteger": 10.0,
            "boolean": True,
            "null": None,
        })

        schema = {
            "type": "dict",
            "properties": {
                "string": "string",
                "integer": "integer",
                "float": "float",
                "number_integer": "number",
                "number_float": "number",
                "number_str": "number",
                "number_asinteger": "number",
                "boolean": "boolean",
                "null": "null",
            }
        }
        cvtr = convertor.SchemaConvertor(schema)
        result = cvtr(data)
        self.assertDictEqual(result, {
            "string": "1",
            "integer": 2,
            "float": 3.4,
            "number_integer": 5,
            "number_float": 6.7,
            "number_str": 8.9,
            "number_asinteger": 10.0,
            "boolean": True,
            "null": None,
        })

        schema = {
            "type": "dict",
            "properties": {
                "string": "integer",
                "float": "integer",
            }
        }
        cvtr = convertor.SchemaConvertor(schema)
        result = cvtr(data)
        self.assertDictEqual(result, {
            "string": 1,
            "float": 3,
        })

    def test_raw_type(self):
        schema = {"type": "raw"}
        cvtr = convertor.SchemaConvertor(schema)

        self.assertEqual(cvtr(1), 1)
        self.assertEqual(cvtr(2.3), 2.3)
        self.assertEqual(cvtr("345"), "345")
        self.assertEqual(cvtr([6, 7.8]), [6, 7.8])
        self.assertEqual(cvtr({9: 0}), {9: 0})

    def test_complex_type(self):
        data = Pair(key="test", value="test value")
        schema = {
            "type": "object",
            "properties": {
                "key": "string",
                "value": "string"
            }
        }
        cvtr = convertor.SchemaConvertor(schema)
        self.assertEqual(cvtr(data), {
            "key": "test",
            "value": "test value"
        })

        schema = {
            "type": "array",
            "items": "string"
        }
        cvtr = convertor.SchemaConvertor(schema)
        self.assertEqual(cvtr(data), ["test", "test value"])

        data = Pair(key=1, value={
            "array": [Pair(key=2, value=3), Pair(key=4, value=5)],
            "dict": {"key": 6, "value": 7},
            "object": Pair(key=8, value=9),
            "int": 10,
        })
        schema = {
            "type": "object",
            "properties": {
                "key": "string",
                "value": {
                    "type": "dict",
                    "properties": {
                        "array": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "key": "string",
                                    "value": "integer"
                                }
                            }
                        },
                        "dict": {
                            "type": "dict",
                            "properties": {
                                "key": "string",
                                "value": "integer"
                            }
                        },
                        "object": {
                            "type": "object",
                            "properties": {
                                "key": "string",
                                "value": "integer"
                            }
                        },
                        "int": "integer"
                    }
                }
            }
        }
        cvtr = convertor.SchemaConvertor(schema)
        self.assertEqual(cvtr(data), {
            "key": "1",
            "value": {
                "array": [
                    {"key": "2", "value": 3},
                    {"key": "4", "value": 5},
                ],
                "dict": {"key": "6", "value": 7},
                "object": {"key": "8", "value": 9},
                "int": 10
            }
        })

    def test_list_type(self):
        data = [
            Pair(key=1, value=2),
            3, 4.5, "6"
        ]
        schema = {
            "type": "list",
            "typeOf": {
                (int, str): "string",
                float: "integer",
                Pair: {
                    "type": "object",
                    "properties": {
                        "key": "string",
                        "value": "integer"
                    }
                }
            }
        }
        cvtr = convertor.SchemaConvertor(schema)
        self.assertEqual(cvtr(data), [
            {"key": "1", "value": 2},
            "3", 4, "6"
        ])

        data = range(10)
        schema = {
            "type": "list",
            "items": "string"
        }
        cvtr = convertor.SchemaConvertor(schema)
        self.assertEqual(cvtr(data), map(str, range(10)))
