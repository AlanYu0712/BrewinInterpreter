"""
The module that brings it all together! We intentionally keep this as small as possible,
delegating functionality to various modules.
"""

from classv2 import ClassDef
from intbase import InterpreterBase, ErrorType
from bparser import BParser
from objectv2 import ObjectDef


class Interpreter(InterpreterBase):
    """
    Main interpreter class that subclasses InterpreterBase.
    """

    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.trace_output = trace_output
        self.main_object = None
        self.class_index = {}

    def run(self, program):
        """
        Run a program (an array of strings, where each item is a line of source code).
        Delegates parsing to the provided BParser class in bparser.py.
        """
        status, parsed_program = BParser.parse(program)
        if not status:
            super().error(
                ErrorType.SYNTAX_ERROR, f"Parse error on program: {parsed_program}"
            )
        self.__map_class_names_to_class_defs(parsed_program)

        # instantiate main class
        invalid_line_num_of_caller = None
        self.main_object = self.instantiate(
            InterpreterBase.MAIN_CLASS_DEF, invalid_line_num_of_caller
        )

        # call main function in main class; return value is ignored from main
        self.main_object.call_method(
            InterpreterBase.MAIN_FUNC_DEF, [], invalid_line_num_of_caller
        )

        # program terminates!

    def instantiate(self, class_name, line_num_of_statement):
        """
        Instantiate a new class. The line number is necessary to properly generate an error
        if a `new` is called with a class name that does not exist.
        This reports the error where `new` is called.
        """
        if class_name not in self.class_index:
            super().error(
                ErrorType.TYPE_ERROR,
                f"No class named {class_name} found",
                line_num_of_statement,
            )
        class_def = self.class_index[class_name]
        obj = ObjectDef(
            self, class_def, self.trace_output
        )  # Create an object based on this class definition
        return obj

    def __map_class_names_to_class_defs(self, program):
        self.class_index = {}
        for item in program:
            if item[0] == InterpreterBase.CLASS_DEF:
                if item[1] in self.class_index:
                    super().error(
                        ErrorType.TYPE_ERROR,
                        f"Duplicate class name {item[1]}",
                        item[0].line_num,
                    )
                self.class_index[item[1]] = ClassDef(item, self)


def test():
    program_source = [
                    '(class parent',
                    '(field string k "Alan")',
                    '(method int foo ((int param))',
                    ' (return (+ param 50000))',
                    ') #end of foo method',
                    '(method int f ((int param))',
                    '  (return (- 0 param))',
                    ')'
                    ') #end of class parent',

                    '(class test',
                    '(method void foo ()',
                    '   (print "im happy")',
                    ')',
                    ')'
        
                    '(class main inherits parent',
                    '(field string a "Josh Zhang")',
                    '(field int b 3)',
                    '(field bool c true)',
                    '(field main t null)',
                    '(field main t1 null)'
                    '(field parent p null)',
                    '(method void main ()',
                    '   (begin',
                    '       (print (== t null))',
                    '       (print b)',
                    '       (let ((bool b false))',
                    '           (print b))',
                    '       (print b)',
                    '       (set t (new main))',
                    '       (set t1 (new main))',
                    '       (print (== t t1))',
                    '       #(print k)',
                    '       (set b (call me foo b 100))',
                    '       (print b)',
                    '       (print (call me foo b))',
                    '       (print "new test")',
                    '       (set p (new parent))',
                    '       (call me poly t)'
                    '       (print (call me foo b 100))'
                    '   ) #end of begin',
                    ') #end of main method',
                    '(method int foo ((int param) (int param2))',
                    ' (return)',
                    ') #end of foo method',
                    
                    '(method void poly ((parent param))',
                    '   (print "Yeah Poly works!"))',
                    
                    ') #end of class'
                    ]
    i = Interpreter()
    i.run(program_source)

test()