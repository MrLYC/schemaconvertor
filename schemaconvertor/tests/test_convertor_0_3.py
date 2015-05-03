#!/usr/bin/env python
# encoding: utf-8

from unittest import TestCase
from datetime import datetime
from collections import namedtuple

from schemaconvertor.convertor import SchemaConvertor

Pair = namedtuple("Pair", ["key", "value"])


class TestHook(TestCase):
    def test_hook(self):
        pair = Pair("datetime", datetime(2015, 5, 3, 15, 55))
        cvtr = SchemaConvertor({
            "type": "object",
            "properties": {
                "key": "string",
                "value": {
                    "type": "string",
                    "hook": {
                        "pre-convert": ["format_date"],
                    },
                },
            },
        })
        self.assertEqual(cvtr(pair), {
            "key": "datetime",
            "value": pair.value.isoformat(),
        })
        self.assertNotEqual(cvtr(pair), {
            "key": "datetime",
            "value": str(pair.value),
        })

        def str_length_hook(s, schema):
            return len(s)

        cvtr = SchemaConvertor({
            "type": "object",
            "properties": {
                "key": "string",
                "value": {
                    "type": "string",
                    "hook": {
                        "pre-convert": ["format_date", str_length_hook],
                    },
                },
            },
        })
        self.assertEqual(cvtr(pair), {
            "key": "datetime",
            "value": str(len(pair.value.isoformat())),
        })

        def str2int_hook(s, schema):
            return int(s)

        cvtr = SchemaConvertor({
            "type": "object",
            "properties": {
                "key": "string",
                "value": {
                    "type": "string",
                    "hook": {
                        "pre-convert": ["func_result", "format_date"],
                    },
                },
            },
        })
        pair = Pair("datetime", lambda: datetime(2015, 5, 3, 15, 55))
        self.assertEqual(cvtr(pair), {
            "key": "datetime",
            "value": pair.value().isoformat(),
        })
