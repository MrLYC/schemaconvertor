# schemaconvertor
schemaconvertor提供了一种使用schema来转换对象的方法，通过schema，可以指定该对象序列化的部分和对应的类型。

# Features
假设有个简单的数据类型`User`：
```py
from collections import namedtuple

User = namedtuple("User", ["name", "password", "age"])
```

可以通过指定schema来转换对象：
```py
schema = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        },
        "age": {
            "type": "integer"
        }
    }
}

user = User(name="lyc", password="schemaconvertor", age="24")

from schemaconvertor.convertor import to_dict_by_schema

print to_dict_by_schema(user, schema)
```

输出：
> {'age': 24, 'name': 'lyc'}


当仅有**type**一项时，可以将schema省略表示为：
```py
schema = {
    "type": "object",
    "properties": {
        "name": "string",
        "age": "integer"
    }
}
```

## 基本数据类型
| schema | python | comments |
|--------|--------|--------|
| string | types.StringType |        |
| integer | types.IntType |        |
| float | types.FloatType |        |
| boolean | types.BooleanType |        |
| number | int or float | int or float automatic |
| dict | dict like object |        |
| object | object |        |
| array | list | same type of each elements |
| null | None |        |
| raw | raw object | return object directly |

## 基本字段
### type
指定生成的dict的对应字段的类型。

### properties
仅在指定**type**为`dict`或`object`时生效，当为`dict`是对应着字典的每一项，为`object`时则对应着每一个属性。

### items
仅在指定**type**为`array`时生效，描述着数组每一项的schema。

### typeOf
该项指示如何根据数据元素类型来处理数据：
```py
schema = {
    "type": "array",
    "items": {
        "typeOf": {
            User: {
                "name": "string",
                "age": "integer"
            },
            (int, float): "float",
            "default": "string"
        }
    }
}

schema = {
    "type": "object",
    "properties": {
        "key": "string",
        "value": {
            "typeOf": {
                int: "float",
                str: "integer",
                float: "string"
            }
        }
    }
}
```
其中，**default**用来指示没有被列出的类型对应的数据的处理方式。
