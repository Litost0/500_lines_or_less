'''

A simple object model by Carl Friedrich Bolz
'''

class Base(object):
    ''' The base class that all of the object model classes inherit from.'''

    def __init__(self, cls, fields):
        '''Every object has a class.'''
        # cls: A class object
        # fields: dictionary of fields and their values
        self.cls = cls
        self._fields = fields

    def read_attr(self, fieldname):
        '''read field 'fieldname' out of the object'''
        # return self._read_dict(fieldname)
        # 调用method时返回的是一个函数
        # --------for attributed based model---------
        result = self._read_dict(fieldname)
        if result is not MISSING:
            return result
        result = self.cls._read_from_class(fieldname)
        if _is_bindable(result): 
            return _make_boundmethod(result, self)
        if result is not MISSING: 
            return result

        # -------for meta-object protocols(plus the following codes)----------
        meth = self.cls._read_from_class('__getattr__') # 从instance对应的类上找到__getattr__这个函数
        if meth is not MISSING:
            return meth(self, fieldname) # 返回get到的值
        raise AttributeError(fieldname)


    def write_attr(self, fieldname, value):
        '''write field 'fieldname' into the object '''
        # --------for attributed based model---------
        # self._write_dict(fieldname, value)

        # -------for meta-object protocols----------
        meth = self.cls._read_from_class('__setattr__') # 同理找到__setattr__这个函数
        return meth(self, fieldname, value)



    def isinstance(self, cls):
        '''return True if the object is an instance of class clf'''
        return self.cls.issubclass(cls)

    def callmethod(self, methname, *args):
        ''' call method 'methname' with arguments 'args' on object '''
        # meth = self.cls._read_from_class(methname)
        meth = self.read_attr(fieldname)
        return meth(self, *args)

    def _read_dict(self, fieldname):
        ''' read an field 'fieldname' out of th object's dict  '''
        return self._fields.get(fieldname, MISSING)

    def _write_dict(self, fieldname, value):
        ''' write a field 'fieldname' into the object's dict'''
        self._fields[fieldname] = value

def _is_bindable(meth):
    # for attribute-based model
    # return callable(meth)

    # for descriptor protocol

    return hasattr(meth, '__get__') # 判断是不是一个descriptor

def _make_boundmethod(meth, self):
    # for attribute-based model
    # Use a closure to emulate a bound method
    # 这里面用闭包的原因：_read_from_class函数返回一个f_A函数，该函数要穿入self和a两个参数，而调用的时候不显式地传入self，因此要把这个参数“隐藏”起来
    # def bound(*args):
    #     return meth(self, *args)
    # return bound # 返回一个不需要传入self的函数

    # for descriptor protocol
    return meth.__get__(self, None)


MISSING = object()


class Instance(Base):
    ''' Instance of a user-defined class.'''

    # def __init__(self, cls):
    #     assert isinstance(cls, Class)
    #     Base.__init__(self, cls, {})

    # The following codes are for the map optimization implementation

    def __init__(self, cls):
        assert isinstance(cls, Class)
        Base.__init__(self, cls, None)
        self.map = EMPTY_MAP
        self.storage = []

    def _read_dict(self, fieldname):
        index = self.map.get_index(fieldname)
        if index == -1:
            return MISSING
        return self.storage[index]

    def _write_dict(self, fieldname, value):
        index = self.map.get_index(fieldname)
        if index != -1:
            self.storage[index] = value
        else:
            new_map = self.map.next_map(fieldname)
            self.storage.append(value)
            self.map = new_map

class Class(Base):
    ''' A user-defined class.'''
    # The Class class has attribute cls inherited from Base class, so it can be an instance of other class.

    def __init__(self, name, base_class, fields, metaclass):
        Base.__init__(self, metaclass, fields)
        self.name = name
        self.base_class = base_class

    def method_resolution_order(self):
        ''' compute the method resolution order of the class'''
        # 找父类
        if self.base_class is None:
            return [self]
        else:
            return [self] + self.base_class.method_resolution_order()

    def issubclass(self, cls):
        ''' is self a subclass of cls'''
        return cls in self.method_resolution_order()

    def _read_from_class(self, methname):
        # 找自己和所有父类中是否有methname方法，返回那个方法
        for cls in self.method_resolution_order():
            if methname in cls._fields:
                return cls._fields[methname]
        return MISSING


# set up the base hierarchy as in Python (the ObjVLisp model)
# the ultimate base class is OBJECT
OBJECT = Class(name='object', base_class=None, fields={}, metaclass=None)
# TYPE is a subclass of OBJECT
TYPE = Class(name='type', base_class=OBJECT, fields={}, metaclass=None)
# TYPE is an instance of itself
TYPE.cls = TYPE
# OBJECT is an instance of TYPE
OBJECT.cls = TYPE

#----The following codes are specifically for meta-object model-------
def OBJECT__setattr__(self, fieldname, value):
    # 给self实例增加一个fieldname属性，并赋上value
    self._write_dict(fieldname, value)
OBJECT = Class('object', None, {'__setattr__': OBJECT__setattr__}, None)


class Map(object):
    def __init__(self, attrs):
        self.attrs = attrs
        self.next_maps = {}

    def get_index(self, fieldname):
        return self.attrs.get(fieldname, -1)

    def next_map(self, fieldname):
        assert fieldname not in self.attrs
        if fieldname in self.next_maps:
            return self.next_maps[fieldname]
        attrs = self.attrs.copy()
        attrs[fieldname] = len(attrs)
        result = self.next_maps[fieldname] = Map(attrs)
        return result

EMPTY_MAP = Map({})

#------------------------------------------TEST CODE OF SIMPLE OBJECT MODEL-----------------------------------------------------

def test_read_write_field():
    # Python code
    class A(object):
        pass
    obj = A()
    obj.a = 1
    assert obj.a == 1

    obj.b = 5
    assert obj.a == 1
    assert obj.b == 5

    obj.a = 2
    assert obj.a == 2
    assert obj.b == 5


    # Object model code
    A = Class(name='A', base_class=OBJECT, fields={}, metaclass=TYPE)
    obj = Instance(A)
    obj.write_attr('a', 1)
    assert obj.read_attr('a') == 1

    obj.write_attr('b', 5)
    assert obj.read_attr('a') == 1
    assert obj.read_attr('b') == 5

    obj.write_attr('a', 2)
    assert obj.read_attr('a') == 2
    assert obj.read_attr('b') == 5


def test_read_write_field_class():
    # classes are objects too
    # Python code
    class A(object):
        pass
    A.a = 1
    assert A.a == 1
    A.a = 6
    assert A.a == 6

    # Object model code
    A = Class(name='A', base_class=OBJECT, fields={'a':1}, metaclass=TYPE)
    assert A.read_attr('a') == 1
    A.write_attr('a', 5)
    assert A.read_attr('a') == 5

def test_isinstance():
    # Python code
    class A(object):
        pass
    class B(A):
        pass
    b = B()
    assert isinstance(b, B)
    assert isinstance(b, A)
    assert isinstance(b, object)
    assert not isinstance(b, type)

    # Object model code
    A = Class(name='A', base_class=OBJECT, fields={}, metaclass=TYPE)
    B = Class(name='B', base_class=A, fields={}, metaclass=TYPE)
    b = Instance(B)
    assert b.isinstance(B)
    assert b.isinstance(A)
    assert b.isinstance(OBJECT)
    assert not b.isinstance(TYPE)


def test_callmethod_simple():
    # Python code
    class A(object):
        def f(self):
            return self.x + 1
    obj = A()
    obj.x = 1
    assert obj.f() == 2

    class B(A):
        pass
    obj = B()
    obj.x = 1
    assert obj.f() == 2

    # Object model code
    def f_A(self):
        return self.read_attr('x') + 1
    A = Class(name='A', base_class=OBJECT, fields={'f': f_A}, metaclass=TYPE)
    obj = Instance(A)
    obj.write_attr('x', 1)
    assert obj.callmethod('f') == 2

    B = Class(name='B', base_class=A, fields={}, metaclass=TYPE)
    obj = Instance(B)
    obj.write_attr('x', 2)
    assert obj.callmethod('f') == 3


def test_callmethod_subclassing_and_arguments():
    # Python code
    class A(object):
        def g(self, arg):
            return self.x + arg
    obj = A()
    obj.x = 1
    assert obj.g(4) == 5

    class B(A):
        def g(self, arg):
            return self.x + arg * 2
    obj = B()
    obj.x = 4
    assert obj.g(4) == 12

    # Object model code
    def g_A(self, arg):
        return self.read_attr('x') + arg
    A = Class(name='A', base_class=OBJECT, fields={'g': g_A}, metaclass=TYPE)
    obj = Instance(A)
    obj.write_attr('x', 1)
    assert obj.callmethod('g', 4) == 5

    def g_B(self, arg):
        return self.read_attr('x') + arg * 2
    B = Class(name='B', base_class=A, fields={'g': g_B}, metaclass=TYPE)
    obj = Instance(B)
    obj.write_attr('x', 4)
    assert obj.callmethod('g', 4) == 12


'''Differences between attribute-based model and method-based model'''

def test_bound_method():
    # Python code
    class A(object):
        def f(self, a):
            return self.x + a + 1
    obj = A()
    obj.x = 2
    m = obj.f
    assert m(4) == 7

    class B(A):
        pass
    obj = B()
    obj.x = 1
    m = obj.f
    assert  m(10) == 12

    # Object model code
    def f_A(self, a):
        return self.read_attr('x') + a + 1
    A = Class(name='A', base_class=OBJECT, fields={'f': f_A}, metaclass=TYPE)
    obj = Instance(A)
    obj.write_attr('x', 2)
    m = obj.read_attr('f') # return a function
    assert m(4) == 7

    a = obj.read_attr('x')
    assert a == 2

    obj.write_attr('x', 5)
    a = obj.read_attr('x')
    assert a == 5


    B = Class(name='B', base_class=A, fields={}, metaclass=TYPE)
    obj = Instance(B)
    obj.write_attr('x', 1)
    m = obj.read_attr('f') # m是一个函数名
    assert m(10) == 12

def test_getattr():
    # Python code
    class A(object):
        def __getattr__(self, name):
            if name == 'fahrenheit':
                return self.celsius * 9.0 / 5.0 + 32
            raise AttributeError(name)

        def __setattr__(self, name, value):
            if name == 'fahrenheit':
                self.celsius = (value - 32) * 5.0 / 9.0
            else:
                # call the base implementation
                object.__setattr__(self, name, value)

    obj = A()
    obj.celsius = 30
    assert obj.fahrenheit == 86 # test __getattr__
    obj.celsius = 40
    assert obj.fahrenheit == 104

    obj.fahrenheit = 86 # test __setattr__
    assert obj.celsius == 30
    assert obj.fahrenheit == 86

    # Object model code
    def __getattr__(self, name):
        if name == 'fahrenheit':
            return self.read_attr('celsius') * 9.0 / 5.0 + 32
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name == 'fahrenheit':
            self.write_attr('celsius', (value - 32) * 5.0 / 9.0)
        else:
            # call the base implementation
            OBJECT.read_attr('__setattr__')(self, name, value)

    A = Class(name='A', base_class=OBJECT, 
            fields={'__getattr__': __getattr__, '__setattr__': __setattr__}, metaclass=TYPE)
    obj = Instance(A)
    obj.write_attr('celsius', 30)
    print('---')
    assert obj.read_attr('fahrenheit') == 86 # test __getattr__
    print(obj._fields)
    obj.write_attr('celsius', 40)
    assert obj.read_attr('fahrenheit') == 104
    obj.write_attr('fahrenheit', 86) # test __setattr__
    assert obj.read_attr('celsius') == 30
    assert obj.read_attr('fahrenheit') == 86

def test_get():
    # Python code
    class FahrenheitGetter(object):
        def __get__(self, inst, cls):
            return inst.celsius * 9.0 / 5.0 + 32

    class A(object):
        fahrenheit = FahrenheitGetter()
    obj = A()
    obj.celsius = 30
    assert obj.fahrenheit == 86

    # Object model code
    class FahrenheitGetter(object):
        # 这是一个descriptor，因为它定义了__get__()
        def __get__(self, inst, cls):
            return inst.read_attr('celsius') * 9.0 / 5.0 + 32

    A = Class(name='A', base_class=OBJECT, 
            fields={'fahrenheit': FahrenheitGetter()}, metaclass=TYPE)
    obj = Instance(A)
    obj.write_attr('celsius', 30)
    print(obj.read_attr('fahrenheit'))
    assert obj.read_attr('fahrenheit') == 86


def test_maps():
    # white box test inspecting the implementation
    Point = Class(name='Point', base_class=OBJECT, fields={}, metaclass=TYPE)
    p1 = Instance(Point)
    p1.write_attr('x', 1)
    p1.write_attr('y', 2)
    assert p1.storage == [1, 2]
    assert p1.map.attrs == {'x': 0, 'y': 1}


    p2 = Instance(Point)
    p2.write_attr('x', 5)
    p2.write_attr('y', 6)
    assert p1.map is p2.map
    assert p2.storage == [5, 6]


    p1.write_attr('x', -1)
    p1.write_attr('y', -2)
    assert p1.map is p2.map
    assert p1.storage == [-1, -2]


    p3 = Instance(Point)
    p3.write_attr('x', 100)
    p3.write_attr('z', -343)
    assert p3.map is not p1.map
    assert p3.map.attrs == {'x': 0, 'z': 1}



if __name__ == '__main__':
    # test_read_write_field()
    # test_read_write_field_class()
    # test_callmethod_simple()
    # test_callmethod_subclassing_and_arguments()
    # test_bound_method()
    # test_getattr()

    # def clouser(func, self):
    #     def bound(*args):
    #         return func(self, *args)
    #     return bound

    # test_get()
    # class A(object):
        
    #     def __init__(self, c=0):
    #         self.__c = c

    #     def __str__(self):
    #         return 'A'

    # a = A()
    # b = A()
    # a.x = 1
    # b.y = 2
    # print(hasattr(a, '_A__c'))
    # print(a.__str__())

    test_maps()



