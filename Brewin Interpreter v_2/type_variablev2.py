"""
Module that contains the Value definition and associated type constructs.
"""

from enum import Enum
from intbase import InterpreterBase
from type_valuev2 import Type



# Represents a value, which has a type and its value
class Variable:
    """A representation for a value that contains a type tag."""

    def __init__(self, var_type, var_name, class_name):
        self.__type = var_type
        self.__name = var_name
        self.__class_name= class_name

    def type(self):
        return self.__type

    def name(self):
        return self.__name
    
    def class_name(self):
        return self.__class_name

    #NOTICE WE DO NOT HAVE SETTERS BECAUSE IT WOULDNT MAKE SENSE


# pylint: disable=too-many-return-statements
# also threw away create variable as it wouldn't make sense

#convert type declaration to Type class
def create_variable(type,name):
    """
    Create a Variable object.
    """
    if type == InterpreterBase.INT_DEF:
        return Variable(Type.INT, name, None)
    elif type == InterpreterBase.BOOL_DEF:
        return Variable(Type.BOOL, name, None)
    elif type == InterpreterBase.STRING_DEF:
        return Variable(Type.STRING, name, None)
    else: #TODO: need to deal with classes
        return Variable(Type.CLASS, name, type)
    return None

