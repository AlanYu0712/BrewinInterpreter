from enum import Enum
from intbase import InterpreterBase
from type_valuev2 import Type

def convertType(type):
    """
    Convert Method's return type.
    """
    if type == InterpreterBase.INT_DEF:
        return (Type.INT, None)
    elif type == InterpreterBase.BOOL_DEF:
        return (Type.BOOL, None)
    elif type == InterpreterBase.STRING_DEF:
        return (Type.STRING, None)
    elif type == InterpreterBase.VOID_DEF:
        return (Type.NOTHING, None)
    else: #TODO: need to deal with classes
        return (Type.CLASS, type)
    return None