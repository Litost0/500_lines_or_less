import logging
import time

logging.basicConfig(level=logging.INFO)

class Field(object):

    pass

class IntegerField(Field):

    def __init__(self, val):
        self.val = val

class StringField(Field):

    def __init__(self, val):
        self.val = val



class MetaClass(type):

    def __new__(cls, name, bases, attrs):

        logging.info('new MetaClass:{}'.format(name))

        if name == 'Base':
            return type.__new__(cls, name, bases, attrs)
        
        mappings = dict()

        for k,v in attrs.items():

            if isinstance(v, Field):
                mappings[k] = v

        for key in mappings.keys():
            attrs.pop(key)
        
        
        attrs['__mappings__'] = mappings

        return type.__new__(cls, name, bases, attrs)


class Base(dict, metaclass=MetaClass):
    def __init__(self, **kw):

        logging.info('init Base:{}'.format(self.__class__.__name__))

        super().__init__(**kw)

    def __getattr__(self, k):

        logging.info('construct attr:{}'.format(k))

        try:
            return self[k]
        except KeyError:
            raise AttributeError('Attribute not found')

    def __setattr__(self, k, v):

        self[k] = v





class User(Base):

    # first __new__ Base

    user_id = IntegerField(0)
    user_name = StringField('a')

    logging.info('load User class attrs')



user = User(user_id=0, user_name='sasaki')
logging.info('create user instance')
# print(User.__dict__)

name = user.user_name

time.sleep(0.5)

print(name)

print('attrs only to users:{}'.format(user.__dict__))

print('attrs to Users:{}'.format(User.__dict__))

print(hasattr(user, 'user_name'))

time.sleep(0.5)

print(getattr(user, 'user_name', None))

time.sleep(0.5)

print(getattr(user, 'user_score', None))





