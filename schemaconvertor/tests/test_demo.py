#!/usr/bin/env python
# encoding: utf-8

from unittest import TestCase
from collections import namedtuple

from schemaconvertor.convertor import convert_by_schema


Tag = namedtuple("Tag", ["name", "value"])


class User(object):
    Role = "Normal"

    def __init__(self, name, email):
        self.name = name
        self.email = email


class Admin(User):
    Role = "Admin"

    def __init__(self, name, email, wid):
        self.wid = wid
        super(Admin, self).__init__(name, email)


class Book(object):
    def __init__(self, name, owners=()):
        self.owners = list(owners)
        self.name = name
        self.tags = {}

SIMPLEUSERSCHEMA = {
    "version": "0.2",
    "encoding": "utf-8",
    "type": "object",
    "properties": {
        "name": "string",
    }
}

FULLUSERSCHEMA = {
    "version": "0.2",
    "encoding": "utf-8",
    "type": "object",
    "properties": {
        "name": "string",
        "email": "string",
        "Role": "string",
    }
}

SIMPLEADMINSCHEMA = {
    "version": "0.2",
    "encoding": "utf-8",
    "type": "object",
    "properties": {
        "name": "string",
        "wid": "integer"
    }
}

FULLADMINSCHEMA = {
    "version": "0.2",
    "encoding": "utf-8",
    "type": "object",
    "properties": {
        "name": "string",
        "email": "string",
        "wid": "integer",
        "Role": "string",
    }
}

USERMIXTYPELISTSCHEMA = {
    "version": "0.2",
    "encoding": "utf-8",
    "type": "array",
    "items": {
        "typeOf": {
            User: SIMPLEUSERSCHEMA,
            Admin: SIMPLEADMINSCHEMA
        }
    }
}

USERLISTSCHEMA = {
    "version": "0.2",
    "encoding": "utf-8",
    "type": "array",
    "items": SIMPLEUSERSCHEMA
}

SIMPLEBOOKSCHEMA = {
    "version": "0.2",
    "encoding": "utf-8",
    "type": "object",
    "properties": {
        "name": "string",
        "owners": {
            "type": "array",
            "items": SIMPLEUSERSCHEMA
        }
    }
}

FULLBOOKSCHEMA = {
    "version": "0.2",
    "encoding": "utf-8",
    "type": "object",
    "properties": {
        "name": "string",
        "owners": {
            "type": "array",
            "items": FULLUSERSCHEMA
        },
        "tags": {
            "type": "dict",
            "patternProperties": {
                "^[a-z]+$": {
                    "type": "object",
                    "properties": {
                        "name": "string",
                        "value": "string"
                    }
                },
                r"^\w+_cnt$": "integer",
                r"^\w+_val$": "number",
            }
        }
    }
}


class TestUser(TestCase):
    def test_convert_User(self):
        user = User("lyc", "imyikong@gmail.com")
        self.assertDictEqual(convert_by_schema(user, FULLUSERSCHEMA), {
            "name": "lyc",
            "email": "imyikong@gmail.com",
            "Role": "Normal"
        })

    def test_convert_Admin(self):
        admin = Admin("刘奕聪", "imyikong@gmail.com", 0)
        self.assertDictEqual(convert_by_schema(admin, FULLADMINSCHEMA), {
            "name": u"刘奕聪",
            "email": "imyikong@gmail.com",
            "wid": 0,
            "Role": "Admin"
        })

    def test_convert_User_list(self):
        user_lst = [
            User("u1", "xxx"),
            Admin("a1", "xxx", 1),
            User("u2", "xxx"),
        ]

        self.assertLessEqual(convert_by_schema(user_lst, USERMIXTYPELISTSCHEMA), [
            {"name": "u1"},
            {"name": "a1", "wid": 1},
            {"name": "u2"},
        ])


class TestBook(TestCase):
    def test_convert_Book(self):
        user1 = User("u1", "xxx")
        admin1 = Admin("a1", "xxx", 2)
        book = Book("b1", [user1, admin1])

        self.assertDictEqual(convert_by_schema(book, SIMPLEBOOKSCHEMA), {
            "name": "b1",
            "owners": [
                {"name": "u1"},
                {"name": "a1"}
            ]
        })

    def test_convert_Book_full(self):
        user1 = User("u1", "xxx")
        admin1 = Admin("a1", "xxx", 2)
        book = Book("b1", [user1, admin1])
        book.tags["visited_cnt"] = 56
        book.tags["owners_val"] = 2
        book.tags["attr"] = Tag("public", "yes")

        self.assertDictEqual(convert_by_schema(book, FULLBOOKSCHEMA), {
            "name": "b1",
            "owners": [
                {
                    "name": "u1",
                    "email": "xxx",
                    "Role": "Normal"
                },
                {
                    "name": "a1",
                    "email": "xxx",
                    "Role": "Admin"
                }
            ],
            "tags": {
                "visited_cnt": 56,
                "owners_val": 2,
                "attr": {
                    "name": "public",
                    "value": "yes"
                }
            }
        })
