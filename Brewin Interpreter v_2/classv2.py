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
        self.return_type = method_def[1]
        self.method_name = method_def[2]
        self.formal_params = method_def[3]
        self.code = method_def[4]


class FieldDef:
    """
    Wrapper struct for the definition of a member field.
    """

    def __init__(self, field_def):
        self.field_type = field_def[1]
        self.field_name = field_def[2]
        self.default_field_value = field_def[3]


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
        if class_def[2] != 'inherits':
            self.__create_field_list(class_def[2:])
            self.__create_method_list(class_def[2:])
        else:
            self.__create_field_list(class_def[4:])
            self.__create_method_list(class_def[4:])
        self.__create_inherit_list(class_def[2:])

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
    
    def get_blood_line(self):
        return self.blood_line

    def __create_field_list(self, class_body):
        self.fields = []
        fields_defined_so_far = set()
        for member in class_body:
            if member[0] == InterpreterBase.FIELD_DEF:
                if member[2] in fields_defined_so_far:  # redefinition
                    self.interpreter.error(
                        ErrorType.NAME_ERROR,
                        "duplicate field " + member[2],
                        member[0].line_num,
                    )
                self.fields.append(FieldDef(member))
                fields_defined_so_far.add(member[2])

    def __create_method_list(self, class_body):
        self.methods = []
        methods_defined_so_far = set()
        for member in class_body:
            if member[0] == InterpreterBase.METHOD_DEF:
                if member[2] in methods_defined_so_far:  # redefinition
                    self.interpreter.error(
                        ErrorType.NAME_ERROR,
                        "duplicate method " + member[2],
                        member[0].line_num,
                    )
                self.methods.append(MethodDef(member))
                methods_defined_so_far.add(member[2])
                
    def __create_inherit_list(self, class_body):
        self.blood_line = [self.name]
        if class_body[0] != 'inherits':
            return
        parent = class_body[1]
        if parent not in self.interpreter.class_index:
            self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "no class named " + parent + " found.",
                        parent.line_num,
                    )
        parent_info = self.interpreter.class_index[parent]
        
        
        for f in parent_info.get_fields():
            if f.field_name in [x.field_name for x in self.fields]:
                self.interpreter.error(
                        ErrorType.NAME_ERROR,
                        "duplicate field " + f.field_name,
                        parent.line_num,
                    )
            self.fields.append(f)

        for m in parent_info.get_methods():
            add = True
            for x in self.methods:
                if m.method_name == x.method_name and len(m.formal_params)==len(x.formal_params):
                    add = False
                    break
            if add:
                self.methods.append(m)
            
        
        self.blood_line+=parent_info.get_blood_line()
        
