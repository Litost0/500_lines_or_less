
'''liaoxuefeng.com'''

class Hello(object):
    def hello(self, name='world'):
        print('Hello, %s.' % name)

# 用type()创建class

def fn(self, name='world'):
    print('Hello, %s.' % name)

# Hello = type('Hello', (object,), dict(hello=fn)) # 创建Hello class

# metaclass是类的模版，必须从'type'类型派生：
class ListMetaclass(type):
    def __new__(cls, name, bases, attrs):
        # cls: 当前准备创建的类的对象
        # name: 类的名字 (MyList)
        # bases: 继承的父类 (list)
        # attrs: 类的方法集合
        print(cls)
        attrs['add'] = lambda self, value: self.append(value)
        return type.__new__(cls, name, bases, attrs)

class MyList(list, metaclass=ListMetaclass):
    pass

# 用元类编写一个ORM框架



class Field(object):

    # 负责保存数据库表的字段名和字段类型
    def __init__(self, name, column_type):
        self.name = name
        self.column_type = column_type

    def __str__(self):
        return '<%s:%s>' % (self.__class__.__name__, self.name) # self.__class__.__name__: self这个实例所属的类的名称


class StringField(Field):

    def __init__(self, name):
        super(StringField, self).__init__(name, 'varchar(100)')


class IntegerField(Field):

    def __init__(self, name):
        super(IntegerField, self).__init__(name, 'bigint')


class ModelMetaclass(type):

    def __new__(cls, name, bases, attrs):
        if name == 'Model': # 如果是父类，直接按默认方法创建
            return type.__new__(cls, name, bases, attrs)
        print('Found model: %s' % name)
        mappings = dict()
        # 在User类中查找定义的类的所有属性；
        # 如果找到一个Field属性，就把它保存到__mappings__这个dict中；
        # 之后要从类属性中删除该Field属性（实例属性会覆盖类的同名属性）
        for k,v in attrs.items():
            if isinstance(v, Field):
                print('Found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
        for k in mappings.keys():
            attrs.pop(k)
        attrs['__mappings__'] = mappings # 保存属性和列的映射关系
        attrs['__table__'] = name # 假设表名和类名一致 （User）
        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):
    # 继承自python的built-in: dict

    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError('Model object has no attribute %s' % key)

    def __setattr__(self, key, value):
        self[key] = value

    def save(self):
        fields = []
        params = []
        args = []
        for k,v in self.__mappings__.items(): # k: User class field name; v: User class field object
            fields.append(v.name)
            params.append('?')
            args.append(getattr(self, k, None)) # 若不存在k这个attribute，返回None，即实例中定义的attribute若在mapping中找不到，则返回None
        sql = 'insert into %s (%s) values (%s)' % (self.__table__, ','.join(fields), ','.join(params))
        print('SQL: %s' % sql)
        print('ARGS: %s' % str(args))

# 调用示例:

    class User(Model):

        id = IntegerField('id')
        name = StrignField('username')
        email = StringField('email')
        password = StringField('password')

    # User类的__init__继承的是dict的__init__

    u = User(id=12345, name='Michael', email='test@orm.org', password='my_pwd')

    # u.save()



# -------- TEST CODE ----------

if __name__ == '__main__':
    # h = Hello()
    # h.hello()
    # print(type(Hello))
    # print(type(h))
    # print(type(Hello) == type)

    # h = Hello()
    # print(h.hello())
    # assert type(Hello) == type
    # assert type(h) == Hello

    # L = MyList()
    # L.add(1)
    # assert L == [1]

    class User(Model):

        id = IntegerField('id')
        name = StringField('name')
        email = StringField('email')
        password = StringField('password')

    # u = User(id=12345, name='Michael', email='test@orm.org', password='my-pwd')
    # u.save()
    # print(hasattr(User, '__mappings__'))

    # class A(object):

    #     def __new__(cls, name, bases, attrs):

    #         return type.__new__(cls, name, bases, attrs)

    # a = A()
    class MetaClass(type):

        def __new__(cls, name, bases, attrs):

            if name == 'Base':
                print('a')
                return type.__new__(cls, name, bases, attrs)

            print('c')

            mappings = {}

            for k, v in attrs.items():
                if isinstance(v, Field):
                    mappings[k] = v

            for k in mappings.keys():
                attrs.pop(k)


            attrs['__mappings__'] = mappings
            attrs['__table__'] = name

            return type.__new__(cls, name, bases, attrs)


    class Base(dict, metaclass=MetaClass):


        def __init__(self, **kw):
            print('d')
            super(Base, self).__init__(**kw)

        def __getattr__(self, key):

            try:
                return self[key]
            except KeyError:
                raise AttributeError('The model has no attribute {}'.format(key))

        def __setattr__(self, key, value):

            self[key] = value

        def save(self):

            fields = []
            params = []
            args = []

            for k, v in self.__mappings__.items():
                fields.append(v.name)
                params.append('?')
                args.append(getattr(self, k, None))
            
            sql = 'insert into %s (%s) values (%s)' % (self.__table__, ','.join(fields), ','.join(params))
            print('SQL: %s' % sql)
            print('ARGS: %s' % str(args))




    class User(Base):

        print('b')

        id = IntegerField('id')
        name = StringField('name')
        email = StringField('email')
        password = StringField('password')



    class Field(object):

        def __init__(self, name, column_type):

            self.name = name
            self.column_type = column_type

        def __str__(self):

            return '{0}: {1}'.format(self.__class__.__name__, self.name)


    class StringField(Field):

        def __init__(self, name, column_type):

            super(StringField, self).__init__(name, 'varchar(100)')


    class IntegerField(Field):

        def __init__(self, name, column_type):

            super(IntegerField, self).__init__(name, 'bigint')

    u = User(id=12345, name='Fubuki', email='fubuki@outlook.com', password='nekodesu')
    u.save()


















