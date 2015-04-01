# schemaconvertor
**schemaconvertor**提供了一种使用schema来转换对象的方法，通过schema，可以指定该对象序列化的部分和对应的类型，其结果可以进一步序列化为json。

安装：`pip install schemaconvertor`

项目：[github](https://github.com/MrLYC/schemaconvertor) [pypi](https://pypi.python.org/pypi/schemaconvertor/)

版本：0.3

## 演示
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

from schemaconvertor.convertor import convert_by_schema

print convert_by_schema(user, schema)
```

输出：
> {'age': 24, 'name': 'lyc'}

更多示例：[demo 0.3](https://github.com/MrLYC/schemaconvertor/blob/master/schemaconvertor/tests/test_demo.py)

## 说明
### 基本字段
#### version
**version**字段标识着Schema版本。

#### description
**description**字段标识着Schema说明。

#### encoding
**encoding**指定Schema的**string**字段的字符编码，默认是*utf-8*。

#### decoderrors
**decoderrors**指定Schema的**string**字段解码失败的操作，用于`str.decode`的第二个参数，主要有*strict*，*ignore*，*replace*三种可选参数，默认是`strict`。

#### type
**type**字段指定对应待转换数据的最终类型，主要类型对应如下表：

|     type     |     Python     |
|:------------:|:--------------:|
|    string    |     unicode    |
|    object    |      dict      |
|    integer   |      int       |
|    float     |      float     |
|    number    |    int/float   |
|    boolean   |      bool      |
|    dict      |      dict      |
|    array     |      list      |
|    null      |    NoneType    |
|    raw       |     object     |

**type**字段直接影响转换行为，因此基本上每个Schema都需指定**type**，为简化表达，当一个Schema仅有**type**一项时，可以直接使用**type**的值简化表示为Schema。

#### typeOf
当前仅在声明**typeOf**字段时可以不指定**type**，**typeOf**指示如何根据数据的类型选择对应的Schema。可以使用真实的Python类型或类型元组作为key（作为`isinstance`的第二个参数）。

#### default
**default**字段仅用在**typeOf**字段内，用于指示缺省类型表示的Schema。

#### items
**items**字段仅在**type**为array时生效，用于描述序列中的每一项对应的Schema。

#### properties
**items**字段仅在**type**为dict或object时生效，指定给出的项的Schema（没有指定的项不会处理）。

#### patternProperties
**items**字段仅在**type**为dict或object时生效，指定符合给定的正则表达式的项的Schema（使用`re.search`匹配）。

### 附加信息
1. Schema使用lazy compile方式，仅在转换使用时自动编译，初始化代价极小。
2. 子Schema中如无显式声明，*version*，*description*，*encoding*，*decoderrors*自动继承父Schema对应的值。
3. **typeOf**能够识别继承关系，但针对使用数据真实类型的情况有优化。
4. **typeOf**指定多种类型时不要使用`list`等非hashable类型。
5. 对于*object*的情况是使用`ObjAsDictAdapter`将数据包装成类`dict`对象进行转换的。
