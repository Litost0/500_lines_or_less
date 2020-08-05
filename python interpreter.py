'''A Python Interpreter Written in Python'''
'''By Allison Kaptur'''

# A tiny interpreter

# three instructions:
#   LOAD_VALUE
#   ADD_TWO_VALUES
#   PRINT_ANSWER

import dis # A bytecode disassembler in Python standard library.
import sys
import collections



class Interpreter:
    def __init__(self):
        self.stack = [] # A stack based interpreter
        self.environment = {} # Keep tracking of what names are bound to what values

    def LOAD_VALUE(self, number):
        self.stack.append(number)

    def PRINT_ANSWER(self):
        answer = self.stack.pop()
        print(answer)

    def STORE_NAME(self, name):
        # 从栈中取出一个值，将其与name绑定，存入environment字典中
        val = self.stack.pop()
        self.environment[name] = val

    def LOAD_NAME(self, name):
        # 把变量名对应的值压入栈中
        val = self.environment[name]
        self.stack.append(val)

    def ADD_TWO_VALUES(self):
        first_num = self.stack.pop()
        second_num = self.stack.pop()
        total = first_num + second_num
        self.stack.append(total)

    def parse_argument(self, instruction, argument, what_to_execute):
        '''Understand what the argument to each instruction means.'''
        # 传入的argument：指令中的0，1，2，...(index)
        # 返回的argument：具体的值，如变量名称或栈中具体的数
        numbers = ['LOAD_VALUE']
        names = ['LOAD_NAME', 'STORE_NAME']

        if instruction in numbers:
            argument = what_to_execute['numbers'][argument]
        elif instruction in names:
            argument = what_to_execute['names'][argument]

        return argument

    # bad implementation:
    # def run_code(self, what_to_execute):
    #     instructions = what_to_execute['instructions']
        
    #     for each_step in instructions: # loop over each instructions
    #         instruction, argument = each_step
    #         argument = self.parse_argument(instruction, argument, what_to_execute)
    #         if instruction == 'LOAD_VALUE':
    #             self.LOAD_VALUE(argument)
    #         elif instruction == 'ADD_TWO_VALUES':
    #             self.ADD_TWO_VALUES()
    #         elif instruction == 'PRINT_ANSWER':
    #             self.PRINT_ANSWER()
    #         elif instruction == 'STORE_NAME':
    #             self.STORE_NAME(argument)
    #         elif instruction == 'LOAD_NAME':
    #             self.LOAD_NAME(argument)

    # good implementation:
    # make use of Python's dynamic method lookup, aka getattr()
    def execute(self, what_to_execute):
        instructions = what_to_execute['instructions']
        for each_step in instructions:
            instruction, argument = each_step
            argument = self.parse_argument(instruction, argument, what_to_execute)
            bytecode_method = getattr(self, instruction)
            if argument is None:
                bytecode_method()
            else:
                bytecode_method(argument)


# --------- The Byterun model ------------

# Four kinds of objects in Byterun:
# 1. VirtualMachine: stores the call stack
# 2. Frame: the frame is a collection of attributes with no methods, including code object, namespaces, stacks, and so on
# 3. Function
# 4. Block

class VirtualMachineError(Exception):
    pass


class VirtualMachine(object):

    def __init__(self):
        self.frames = [] # The call stack of frames
        self.frame = None # The current frame
        self.return_value = None
        self.last_exception = None

    def run_code(self, code, global_names=None, local_names=None):
        '''An entry point to execute code using the virtual machine.'''
        frame = self.make_frame(code, global_names=global_names, local_names=local_names)
        self.run_frame(frame)

    # Frame manipulation
    def make_frame(self, code, callargs={}, global_names=None, local_names=None):
        if global_names is not None and local_names is not None:
            local_names = global_names
        elif self.frames:
            global_names = self.frame.global_names
            local_names = {}
        else:
            global_names = lobal_names = {
                '__builtins__': __builtins__,
                '__name__': '__main__',
                '__doc__': None,
                '__package__': None,
            }
        local_names.update(callargs)
        frame = Frame(code, global_names, local_names, self.frame)
        return frame

    def push_frame(self, frame):
        self.frames.append(frame)
        self.frame = frame

    def pop_frame(self):
        self.frames.pop()
        if self.frames:
            self.frame = self.frames[-1]
        else:
            self.frame = None

    # Data stack manipulation
    def top(self):
        return self.frame.stack[-1]

    def pop(self):
        return self.frame.stack.pop()

    def push(self, *vals):
        self.frame.stack.extend(vals)

    def popn(self, n):
        '''
        Pop a number of values from the value stack.
        A list of 'n' values is return, the deepest value first.
        '''
        if n:
            ret = self.frame.stack[-n:]
            self.frame.stack[-n:] = []
        else:
            return []


    def parse_byte_and_args(self):
        '''
        Takes a bytecode, checks if it has arguments and parses the arguments if so.
        It also updates the frame's attribute: last_instruction
        One byte long: no argument
        Three byte long: with argument
        '''
        f = self.frame
        opoffset = f.last_instruction
        byteCode = f.code_obj.co_code[opoffset]
        f.last_instruction += 1
        byte_name = dis.opname[byteCode]
        if byteCode >= dis.HAVE_ARGUMENT:
            # index into the bytecode
            arg = f.code_obj.co_code[f.last_instruction: f.last_instruction+2]
            f.last_instruction += 2 # advance the instruction pointer
            arg_val = arg[0] + (arg[1] * 256)
            if byteCode in dis.hasconst: # Look up a constant
                arg = f.code_obj.co_const[arg_val]
            elif byteCode in dis.hasname: # Look up a name
                arg = f.code_obj.co_names[arg_val]
            elif byteCode in dis.haslocal: # Look up a local name
                arg = f.code_obj.co_varnames[arg_val]
            elif byteCode in dis.hasjrel: # Calculate a relative jump
                arg = f.last_instruction + arg_val
            else:
                arg = arg_val
        else:
            argument = []

        return byte_name, argument


    def dispatch(self, byte_name, argument):
        '''
        It looks up the operations for a given instruction and executes them.
        Define a method for each bytename and then use getattr to look it up.

        Dispatch by bytename to the corresponding method.
        Exceptions are caught and set on the virtual machine.
        '''

        # When later unwinding the block stack,
        # we need to keep track of why we are doing it.
        why = None
        try:
            bytecode_fn = getattr(self, 'byte_%s' % byte_name, None)
            if bytecode_fn is None:
                if byte_name.startswith('UNARY_'):
                    self.unaryOperator(byte_name[6:])
                elif byte_name.startswith('BINARY_'):
                    self.binaryOperator(byte_name[7:])
                else:
                    raise VirtualMachineError(
                        'unsupported bytecode type: %s' % byte_name
                    )
            else:
                why = bytecode_fn(*argument)
        except:
            # deal with exceptions encountered while executing the op.
            self.last_exception = sys.exc_info()[:2] + (None, )
            why = 'exception'

        return why

    def run_frame(self, frame):
        '''Run a frame until it returns (somehow).
        Exceptions are raised, the return value is returned.
        '''
        self.push_frame(frame)
        while True:
            byte_name, arguments = self.parse_byte_and_args()
            why = self.dispatch(byte_name, arguments)
            # Deal with any block management we need to do
            while why and frame.block_stack:
                why = self.manage_block_stack(why)

            if why:
                break

        self.pop_frame()

        if why == 'exception':
            exc, val, tb = self.last_exception
            e = exc(val)
            e.__traceback__ = tb
            raise e

        return self.return_value



    # Block stack manipulation
    def push_block(self, b_type, handler=None):
        stack_height = len(self.frame.stack)
        self.frame.block_stack.append(Block(b_type, handler, stack_height))

    def pop_block(self):
        return self.frame.block_stack.pop()

    def unwind_block(self, block):
        '''Unwind the values on the data stack corresponding to a given block'''
        if block.type == 'except-handler':
            # The exception itself is on the stack as type, value, and traceback.
            offset = 3
        else:
            offset = 0

        while len(self.frame.stack) > block.level + offset:
            self.pop()

        if block.type == 'except_handler':
            traceback, value, exctype = self.popn(3)
            self.last_exception = exctype, value, traceback

    def manage_block_stack(self, why):
        frame = self.frame
        block = frame.block_stack[-1]
        if block.type == 'loop' and why == 'continue':
            self.jump(self.return_value)
            why = None
            return why

        self.pop_block()
        self.unwind_block(block)

        if block.type == 'loop' and why == 'break':
            why = None
            self.jump(block.handler)
            return why

        if (block.type in ['setup-exception', 'finally'] and why == 'exception'):
            self.push_block('except_handler')
            exctype, value, tb = self.last_exception
            self.push(tb, value, exctype)
            self.push(tb, value, exctype) # twice
            why = None
            self.jump(block.handler)
            return why

        elif block.type == 'finally':
            if why in ('return', 'continue'):
                self.push(self.return_value)

            self.push(why)

            why = None
            self.jump(block.handler)
            return why
        return why







class Frame(object):

    def __init__(self, code_obj, global_names, local_names, prev_frame):
        self.code_obj = code_obj
        self.global_names = global_names
        self.local_names = local_names
        self.prev_frame = prev_frame
        self.stack = []

        if prev_frame:
            self.builtin_names = prev_frame.builtin_names
        else:
            self.builtin_names = local_names['__builtins__']
            if hasattr(self.builtin_names, '__dict__'):
                self.builtin_names = self.builtin_names.__dict__
        
        self.last_instruction = 0
        self.block_stack = []


class Function(object):
    '''
    Create a realistic function object, defining the things the interpreter expect

    '''
    __slots__ = [
        'func_code', 'func_name', 'func_defaults', 'func_globals',
        'func_locals', 'func_dict', 'func_closure',
        '__name__', '__dict__', '__doc__',
        '_vm', '_func'
    ]

    def __init__(self, name, code, globs, defaults, closure, vm):
        '''Don't have to follow this closely'''
        self._vm = vm
        self.func_code = code
        self.func_name = self.__name__ = name or code.co_name
        self.func_defaults = tuple(defaults)
        self.func_globals = globs
        self.func_locals = self._vm.frame.f_locals
        self.__dict__ = {}
        self.func_closure = closure
        self.__doc__ = code.co_consts[0] if code.co_consts else None

        # Sometimes we need a real Python function. This is for that.
        kw = {
            'argdefs': self.func_defaults,
        }
        if closure:
            kw['closure'] = tuple(make_cell(0) for _ in closure)
        self._func = types.FunctionType(code, globs, **kw)

    def __call__(self, *args, **kwargs):
        '''When calling a Function, make a new frame and run it.'''
        callargs = inspect.getcallargs(self._func, *args, **kwargs)
        # Use callargs to provide a mapping of arguments: values to pass into the frame
        frame = self._vm.make_frame(
            self.func_code, callargs, self.func_globals, {}
        )

        return self._vm.run_frame(frame)

def make_cell(value):
    '''Create a real Python closure and grab a cell.'''
    fn = (lambda x: lambda: x)(value)
    return fn.__closure__[0]


# A block is used for certain kinds of flow control, specifically exception handling and looping.
# For example, in a loop , a special iterator object remains on the stack while the loop is running,
# but is popped off when it is finished


Block = collections.namedtuple('Block', 'type, handler, stack_height')





# -------------------------------- TEST CODE ----------------------------------

if __name__ == '__main__':

    what_to_execute_0 = { # 7 + 5
        'instructions':[('LOAD_VALUE', 0), # the first number
                        ('LOAD_VALUE', 1), # the second number
                        ('ADD_TWO_VALUES', None),
                        ('PRINT_ANSWER', None)],
        'numbers': [7, 5]
    }

    # 加3个数，Interpreter 类不用做任何修改

    what_to_execute_1 = { # 7 + 5 + 8
        'instructions':[('LOAD_VALUE', 0), 
                        ('LOAD_VALUE', 1), 
                        ('ADD_TWO_VALUES', None),
                        ('LOAD_VALUE', 2),
                        ('ADD_TWO_VALUES', None),
                        ('PRINT_ANSWER', None)],
        'numbers': [7, 5, 8]
    }


    # def s():
    #     a = 1
    #     b = 2
    #     print(a + b)

    '''complier for 's' '''

    what_to_execute_2 = { # 7 + 5 + 8
        'instructions':[('LOAD_VALUE', 0),
                        ('STORE_NAME', 0), 
                        ('LOAD_VALUE', 1),
                        ('STORE_NAME', 1), 
                        ('LOAD_NAME', 0),
                        ('LOAD_NAME', 1),
                        ('ADD_TWO_VALUES', None),
                        ('PRINT_ANSWER', None)],
        'numbers': [1, 2],
        'names': ['a', 'b']
    }

    interpreter = Interpreter()
    interpreter.execute(what_to_execute_2)


    # --- demo of a real python bytecode ---

    def cond():
        x = 3
        if x < 5:
            return 'yes'
        else:
            return 'no'

    print(cond.__code__.co_code)
    print(list(cond.__code__.co_code))

    # print(dis.dis(cond))
    print_result = '''
                    142           0 LOAD_CONST               1 (3)
                                  2 STORE_FAST               0 (x)

                    143           4 LOAD_FAST                0 (x)
                                  6 LOAD_CONST               2 (5)
                                  8 COMPARE_OP               0 (<)
                                 10 POP_JUMP_IF_FALSE       16

                    144          12 LOAD_CONST               3 ('yes')
                                 14 RETURN_VALUE

                    146     >>   16 LOAD_CONST               4 ('no')
                                 18 RETURN_VALUE
                                 20 LOAD_CONST               0 (None)
                                 22 RETURN_VALUE

                    '''

    def loop():
        x = 1
        while x < 5:
            x = x + 1
        return x

    # print(dis.dis(loop))
    print_result = '''    
                    173           0 LOAD_CONST               1 (1)
                                  2 STORE_FAST               0 (x)

                    174           4 SETUP_LOOP              20 (to 26)
                            >>    6 LOAD_FAST                0 (x)
                                  8 LOAD_CONST               2 (5)
                                 10 COMPARE_OP               0 (<)
                                 12 POP_JUMP_IF_FALSE       24

                    175          14 LOAD_FAST                0 (x)
                                 16 LOAD_CONST               1 (1)
                                 18 BINARY_ADD
                                 20 STORE_FAST               0 (x)
                                 22 JUMP_ABSOLUTE            6
                            >>   24 POP_BLOCK

                    176     >>   26 LOAD_FAST                0 (x)
                                 28 RETURN_VALUE

                    '''




    

