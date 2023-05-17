# pylint: disable=too-few-public-methods

"""
Module with classes for class, field, and method definitions.

In P1, we don't allow overloading within a class;
two methods cannot have the same name with different parameters.
"""

from intbase import InterpreterBase, ErrorType


class MethodDef:
    """
    Wrapper struct for the definition of a member method.
    """

    def __init__(self, method_def):
        self.method_name = method_def[1]
        self.formal_params = method_def[2]
        self.code = method_def[3]


class FieldDef:
    """
    Wrapper struct for the definition of a member field.
    """

    def __init__(self, field_def):
        self.field_name = field_def[1]
        self.default_field_value = field_def[2]


class ClassDef:
    """
    Holds definition for a class:
        - list of fields (and default values)
        - list of methods

    class definition: [class classname [field1 field2 ... method1 method2 ...]]
    """

    def __init__(self, class_def, interpreter):
        self.interpreter = interpreter
        self.name = class_def[1]
        self.__create_field_list(class_def[2:])
        self.__create_method_list(class_def[2:])

    def get_fields(self):
        """
        Get a list of FieldDefs for *all* fields in the class.
        """
        return self.fields

    def get_methods(self):
        """
        Get a list of MethodDefs for *all* fields in the class.
        """
        return self.methods

    def __create_field_list(self, class_body):
        self.fields = []
        fields_defined_so_far = set()
        for member in class_body:
            if member[0] == InterpreterBase.FIELD_DEF:
                if member[1] in fields_defined_so_far:  # redefinition
                    self.interpreter.error(
                        ErrorType.NAME_ERROR,
                        "duplicate field " + member[1],
                        member[0].line_num,
                    )
                self.fields.append(FieldDef(member))
                fields_defined_so_far.add(member[1])

    def __create_method_list(self, class_body):
        self.methods = []
        methods_defined_so_far = set()
        for member in class_body:
            if member[0] == InterpreterBase.METHOD_DEF:
                if member[1] in methods_defined_so_far:  # redefinition
                    self.interpreter.error(
                        ErrorType.NAME_ERROR,
                        "duplicate method " + member[1],
                        member[0].line_num,
                    )
                self.methods.append(MethodDef(member))
                methods_defined_so_far.add(member[1])
