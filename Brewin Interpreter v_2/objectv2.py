"""
Module handling the operations of an object. This contains the meat
of the code to execute various instructions.
"""

from env_v2 import EnvironmentManager
from intbase import InterpreterBase, ErrorType
from type_valuev2 import create_value
from type_valuev2 import Type, Value
from type_variablev2 import  Variable
from type_variablev2 import create_variable
from type_methodv2 import convertType


class ObjectDef:
    STATUS_PROCEED = 0
    STATUS_RETURN = 1
    STATUS_NAME_ERROR = 2
    STATUS_TYPE_ERROR = 3

    def __init__(self, interpreter, class_def, trace_output):
        self.interpreter = interpreter  # objref to interpreter object. used to report errors, get input, produce output
        self.class_def = class_def  # take class body from 3rd+ list elements, e.g., ["class",classname", [classbody]]
        self.trace_output = trace_output
        self.__map_fields_to_values()
        self.__map_method_names_to_method_definitions()
        self.__initialize_blood_line()
        self.__initialize_parent()
        self.__create_map_of_operations_to_lambdas()  # sets up maps to facilitate binary and unary operations, e.g., (+ 5 6)

    def call_method(self, method_name, actual_params, line_num_of_caller):
        """
        actual_params is a list of Value objects (all parameters are passed by value).

        The caller passes in the line number so we can properly generate an error message.
        The error is then generated at the source (i.e., where the call is initiated).
        """
        if method_name not in self.methods:
            self.interpreter.error(
                ErrorType.NAME_ERROR,
                "unknown method " + method_name,
                line_num_of_caller,
            )
            
        method_infos = self.methods[method_name]
        method_info = None
        for i in method_infos:
            if len(actual_params) == len(i.formal_params):
                method_info = i
        if method_info is None:
            self.interpreter.error(
                ErrorType.TYPE_ERROR,
                "invalid number of parameters in call to " + method_name,
                line_num_of_caller,
            )
        env = (
            EnvironmentManager()
        )  # maintains lexical environment for function; just params for now
        for formal, actual in zip(method_info.formal_params, actual_params): #TODO(done): implement type checking
            created_formal = create_variable(formal[0], formal[1])
            if created_formal.type() != actual.type(): #TODO(done): need to deal with classes and null
                self.interpreter.error(
                ErrorType.NAME_ERROR,
                "invalid type assigned at " + method_name + " for parameter " + created_formal.name(),
                line_num_of_caller,
                )
            if created_formal.type()==Type.CLASS and actual.value() is not None:
                if created_formal.class_name() not in actual.value().get_blood_line():
                    self.interpreter.error(
                    ErrorType.NAME_ERROR,
                    "invalid type assigned at " + method_name + " for parameter " + created_formal.name(),
                    line_num_of_caller,
                    )
            env.init_set(created_formal.name(),[actual,created_formal.class_name()])
        # since each method has a single top-level statement, execute it.
        status, return_value = self.__execute_statement(env, method_info.code)
        # if the method explicitly used the (return expression) statement to return a value, then return that
        # value back to the caller
        if status == ObjectDef.STATUS_RETURN: #TODO(y): Deal with classes
            if method_info.return_type[0] != return_value.type(): #TODO(done): deal with classes
                if return_value.type()!= Type.NOTHING:
                    self.interpreter.error(
                    ErrorType.TYPE_ERROR,
                    "invalid return type at " + method_name,
                    line_num_of_caller,
                    )
                else:
                    r_type = method_info.return_type[0] 
                    if r_type == Type.INT:
                        return_value= create_value('0')
                    elif r_type == Type.BOOL:
                        return_value = create_value('false')
                    elif r_type == Type.STRING:
                        return_value = create_value('""')  
                    elif r_type == Type.CLASS:
                        return_value = create_value('null')                                        
            if method_info.return_type[0]==Type.CLASS and return_value.value() is not None:
                if method_info.return_type[1] not in return_value.value().get_blood_line():
                     self.interpreter.error(
                    ErrorType.TYPE_ERROR,
                    "invalid return type at " + method_name,
                    line_num_of_caller,
                    )   
                    
            return return_value
        # The method didn't explicitly return a value, so return a value of type nothing
        r_type = method_info.return_type 
        if r_type == Type.INT:
            return_value= create_value('0')
        elif r_type == Type.BOOL:
            return_value = create_value('false')
        elif r_type == Type.STRING:
            return_value = create_value('""')
        elif r_type == Type.CLASS:
            return_value = create_value('null')  
        return return_value

    def __execute_statement(self, env, code):
        """
        returns (status_code, return_value) where:
        - status_code indicates if the next statement includes a return
            - if so, the current method should terminate
            - otherwise, the next statement in the method should run normally
        - return_value is a Value containing the returned value from the function
        """
        if self.trace_output:
            print(f"{code[0].line_num}: {code}")
        tok = code[0]
        if tok == InterpreterBase.BEGIN_DEF:
            return self.__execute_begin(env, code)
        if tok == InterpreterBase.SET_DEF:
            return self.__execute_set(env, code)
        if tok == InterpreterBase.IF_DEF:
            return self.__execute_if(env, code)
        if tok == InterpreterBase.CALL_DEF:
            return self.__execute_call(env, code)
        if tok == InterpreterBase.WHILE_DEF:
            return self.__execute_while(env, code)
        if tok == InterpreterBase.RETURN_DEF:
            return self.__execute_return(env, code)
        if tok == InterpreterBase.INPUT_STRING_DEF:
            return self.__execute_input(env, code, True)
        if tok == InterpreterBase.INPUT_INT_DEF:
            return self.__execute_input(env, code, False)
        if tok == InterpreterBase.PRINT_DEF:
            return self.__execute_print(env, code)
        if tok == InterpreterBase.LET_DEF:
            return self.__execute_let(env,code)

        self.interpreter.error(
            ErrorType.SYNTAX_ERROR, "unknown statement " + tok, tok.line_num
        )

    #LET
    def __execute_let(self, env, code):
        loc_var_defined_so_far = set()
        shadows = {}
        for loc_var in code[1]:
            if loc_var[1] in loc_var_defined_so_far: #check if duplicate
                self.interpreter.error(
                    ErrorType.NAME_ERROR,
                    "duplicated local vairable "+loc_var[1],
                    code[0].line_num
                )
            #type_checking
            created_value = create_value(loc_var[2])
            created_loc_var = create_variable(loc_var[0],loc_var[1])
            if created_loc_var.type() != created_value.type(): #TODO(done): need to deal with classes
                self.interpreter.error(
                    ErrorType.TYPE_ERROR,
                    "invalid type assigned to "+created_loc_var.name(),
                    code[0].line_num
                    )
            if created_loc_var.type()==Type.CLASS and created_value.value() is not None:
                if created_loc_var.class_name() not in created_value.value().get_blood_line():
                    self.interpreter.error(
                    ErrorType.TYPE_ERROR,
                    "invalid type assigned to "+created_loc_var.name(),
                    code[0].line_num
                    )
            
            
            #dealing with shadowing
            origin_val = env.get_all(created_loc_var.name())
            if origin_val is not None:
                shadows[created_loc_var.name()] = origin_val
            
            #update loc_var
            loc_var_defined_so_far.add(created_loc_var.name())
            env.init_set(created_loc_var.name(),[created_value,created_loc_var.class_name()])
            
        
        for statement in code[2:]:
            status, return_value = self.__execute_statement(env, statement)
            if status == ObjectDef.STATUS_RETURN:
                
                # destructing local variables and recovering shadowed param
                for loc_var in loc_var_defined_so_far:
                    env.del_item(loc_var)
                for param in shadows:
                    env.init_set(param, shadows[param])
                
                return (
                    status,
                    return_value,
                )  # could be a valid return of a value or an error
        # if we run thru the entire block without a return, then just return proceed
        # we don't want the calling block to exit with a return
        
        # destructing local variables and recovering shadowed param
        for loc_var in loc_var_defined_so_far:
            env.del_item(loc_var)
        for param in shadows:
            env.init_set(param, shadows[param])
        return ObjectDef.STATUS_PROCEED, None



    # (begin (statement1) (statement2) ... (statementn))
    def __execute_begin(self, env, code):
        for statement in code[1:]:
            status, return_value = self.__execute_statement(env, statement)
            if status == ObjectDef.STATUS_RETURN:
                return (
                    status,
                    return_value,
                )  # could be a valid return of a value or an error
        # if we run thru the entire block without a return, then just return proceed
        # we don't want the calling block to exit with a return
        return ObjectDef.STATUS_PROCEED, None

    # (call object_ref/me methodname param1 param2 param3)
    # where params are expressions, and expresion could be a value, or a (+ ...)
    # statement version of a method call; there's also an expression version of a method call below
    def __execute_call(self, env, code):
        return ObjectDef.STATUS_PROCEED, self.__execute_call_aux(
            env, code, code[0].line_num
        )

    # (set varname expression), where expresion could be a value, or a (+ ...)
    def __execute_set(self, env, code):
        val = self.__evaluate_expression(env, code[2], code[0].line_num)
        self.__set_variable_aux(env, code[1], val, code[0].line_num)
        return ObjectDef.STATUS_PROCEED, None

    # (return expression) where expresion could be a value, or a (+ ...)
    def __execute_return(self, env, code):
        if len(code) == 1:
            # [return] with no return expression
            return ObjectDef.STATUS_RETURN, create_value(InterpreterBase.NOTHING_DEF)
        return ObjectDef.STATUS_RETURN, self.__evaluate_expression(
            env, code[1], code[0].line_num
        )

    # (print expression1 expression2 ...) where expresion could be a variable, value, or a (+ ...)
    def __execute_print(self, env, code):
        output = ""
        for expr in code[1:]:
            # TESTING NOTE: Will not test printing of object references
            term = self.__evaluate_expression(env, expr, code[0].line_num)
            val = term.value()
            typ = term.type()
            if typ == Type.BOOL:
                val = "true" if val else "false"
            # document - will never print out an object ref
            output += str(val)
        self.interpreter.output(output)
        return ObjectDef.STATUS_PROCEED, None

    # (inputs target_variable) or (inputi target_variable) sets target_variable to input string/int
    def __execute_input(self, env, code, get_string):
        inp = self.interpreter.get_input()
        if get_string:
            val = Value(Type.STRING, inp)
        else:
            val = Value(Type.INT, int(inp))

        self.__set_variable_aux(env, code[1], val, code[0].line_num)
        return ObjectDef.STATUS_PROCEED, None

    # helper method used to set either parameter variables or member fields; parameters currently shadow
    # member fields
    def __set_variable_aux(self, env, var_name, value, line_num):
        # parameter shadows fields
        if value.type() == Type.NOTHING:
            self.interpreter.error(
                ErrorType.TYPE_ERROR, "can't assign to nothing " + var_name, line_num
            )
        param_val = env.get(var_name)
        var_class_name = env.get_all(var_name)
        if param_val is not None:
            if param_val.type() != value.type(): #TODO(done): need to deal with classes and null
                self.interpreter.error(
                ErrorType.TYPE_ERROR,
                "invalid type assigned to "+var_name,
                line_num
                )
            if param_val.type()==Type.CLASS and value.value() is not None:
                if var_class_name[1] not in value.value().get_blood_line():
                    self.interpreter.error(
                    ErrorType.TYPE_ERROR,
                    "invalid type assigned to "+var_name,
                    line_num
                    )
            env.set(var_name, value) #TODO(done): implement type checking
            return

        
        if var_name not in self.fields:
            self.interpreter.error(
                ErrorType.NAME_ERROR, "unknown variable " + var_name, line_num
            )
        var_type = self.fields[var_name][0].type()
        var_class_name = self.fields[var_name][1]
        if var_type != value.type(): #TODO(done): need to deal with classes and null
            self.interpreter.error(
            ErrorType.TYPE_ERROR,
            "invalid type assigned to "+var_name,
            line_num
            )
        if var_type==Type.CLASS and value.value() is not None:
                if  var_class_name not in value.value().get_blood_line():
                    self.interpreter.error(
                    ErrorType.TYPE_ERROR,
                    "invalid type assigned to "+var_name,
                    line_num
                    )
        self.fields[var_name][0] = value #TODO(done): implement type checking

    # (if expression (statement) (statement) ) where expresion could be a boolean constant (e.g., true), member
    # variable without ()s, or a boolean expression in parens, like (> 5 a)
    def __execute_if(self, env, code):
        condition = self.__evaluate_expression(env, code[1], code[0].line_num)
        if condition.type() != Type.BOOL:
            self.interpreter.error(
                ErrorType.TYPE_ERROR,
                "non-boolean if condition " + ' '.join(x for x in code[1]),
                code[0].line_num,
            )
        if condition.value():
            status, return_value = self.__execute_statement(
                env, code[2]
            )  # if condition was true
            return status, return_value
        if len(code) == 4:
            status, return_value = self.__execute_statement(
                env, code[3]
            )  # if condition was false, do else
            return status, return_value
        return ObjectDef.STATUS_PROCEED, None

    # (while expression (statement) ) where expresion could be a boolean value, boolean member variable,
    # or a boolean expression in parens, like (> 5 a)
    def __execute_while(self, env, code):
        while True:
            condition = self.__evaluate_expression(env, code[1], code[0].line_num)
            if condition.type() != Type.BOOL:
                self.interpreter.error(
                    ErrorType.TYPE_ERROR,
                    "non-boolean while condition " + ' '.join(x for x in code[1]),
                    code[0].line_num,
                )
            if not condition.value():  # condition is false, exit loop immediately
                return ObjectDef.STATUS_PROCEED, None
            # condition is true, run body of while loop
            status, return_value = self.__execute_statement(env, code[2])
            if status == ObjectDef.STATUS_RETURN:
                return (
                    status,
                    return_value,
                )  # could be a valid return of a value or an error

    # given an expression, return a Value object with the expression's evaluated result
    # expressions could be: constants (true, 5, "blah"), variables (e.g., x), arithmetic/string/logical expressions
    # like (+ 5 6), (+ "abc" "def"), (> a 5), method calls (e.g., (call me foo)), or instantiations (e.g., new dog_class)
    def __evaluate_expression(self, env, expr, line_num_of_statement):
        if not isinstance(expr, list):
            # dealing with classes (for later)
            # locals shadow member variables
            val = env.get(expr)
            if val is not None:
                return val
            if expr in self.fields:
                return self.fields[expr][0]
            # need to check for variable name and get its value too
            value = create_value(expr) #if expr is straight up a value (Alan)
            if value is not None:
                return value
            self.interpreter.error(
                ErrorType.NAME_ERROR,
                "invalid field or parameter " + expr,
                line_num_of_statement,
            )

        operator = expr[0]
        if operator in self.binary_op_list:
            operand1 = self.__evaluate_expression(env, expr[1], line_num_of_statement)
            operand2 = self.__evaluate_expression(env, expr[2], line_num_of_statement)
            if operand1.type() == operand2.type() and operand1.type() == Type.INT:
                if operator not in self.binary_ops[Type.INT]:
                    self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "invalid operator applied to ints",
                        line_num_of_statement,
                    )
                return self.binary_ops[Type.INT][operator](operand1, operand2)
            if operand1.type() == operand2.type() and operand1.type() == Type.STRING:
                if operator not in self.binary_ops[Type.STRING]:
                    self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "invalid operator applied to strings",
                        line_num_of_statement,
                    )
                return self.binary_ops[Type.STRING][operator](operand1, operand2)
            if operand1.type() == operand2.type() and operand1.type() == Type.BOOL:
                if operator not in self.binary_ops[Type.BOOL]:
                    self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "invalid operator applied to bool",
                        line_num_of_statement,
                    )
                return self.binary_ops[Type.BOOL][operator](operand1, operand2)
            if operand1.type() == operand2.type() and operand1.type() == Type.CLASS: #TODO:class type check
                if operator not in self.binary_ops[Type.CLASS]:
                    self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "invalid operator applied to class",
                        line_num_of_statement,
                    )
                if operand1.value() is not None and operand2.value() is not None:
                    o1_blood_line = operand1.value().get_blood_line()
                    o2_blood_line = operand2.value().get_blood_line()
                    if o1_blood_line[0] not in o2_blood_line or o2_blood_line[0] not in o1_blood_line:
                        self.interpreter.error(
                             ErrorType.TYPE_ERROR,
                            "invalid operator applied to class",
                            line_num_of_statement,
                    )
                return self.binary_ops[Type.CLASS][operator](operand1, operand2)
            # error what about an obj reference and null
            self.interpreter.error(
                ErrorType.TYPE_ERROR,
                f"operator {operator} applied to two incompatible types",
                line_num_of_statement,
            )
        if operator in self.unary_op_list:
            operand = self.__evaluate_expression(env, expr[1], line_num_of_statement)
            if operand.type() == Type.BOOL:
                if operator not in self.unary_ops[Type.BOOL]:
                    self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "invalid unary operator applied to bool",
                        line_num_of_statement,
                    )
                return self.unary_ops[Type.BOOL][operator](operand)

        # handle call expression: (call objref methodname p1 p2 p3)
        if operator == InterpreterBase.CALL_DEF:
            return self.__execute_call_aux(env, expr, line_num_of_statement)
        # handle new expression: (new classname)
        if operator == InterpreterBase.NEW_DEF:
            return self.__execute_new_aux(env, expr, line_num_of_statement)

    # (new classname)
    def __execute_new_aux(self, _, code, line_num_of_statement):
        obj = self.interpreter.instantiate(code[1], line_num_of_statement)
        return Value(Type.CLASS, obj)

    # this method is a helper used by call statements and call expressions
    # (call object_ref/me methodname p1 p2 p3)
    def __execute_call_aux(self, env, code, line_num_of_statement):
        # determine which object we want to call the method on
        obj_name = code[1]
        if obj_name == InterpreterBase.ME_DEF:
            obj = self
        elif obj_name == InterpreterBase.SUPER_DEF: #by barista, this should not take precedence than else
            obj = self.super
        else:
            obj = self.__evaluate_expression(
                env, obj_name, line_num_of_statement
            ).value()
        # prepare the actual arguments for passing
        if obj is None:
            self.interpreter.error(
                ErrorType.FAULT_ERROR, "null dereference", line_num_of_statement
            )
        actual_args = []
        for expr in code[3:]:
            actual_args.append(
                self.__evaluate_expression(env, expr, line_num_of_statement)
            )
        return obj.call_method(code[2], actual_args, line_num_of_statement)

    def __map_method_names_to_method_definitions(self):
        self.methods = {}
        for method in self.class_def.get_methods():
            if type(method.return_type) is not Type and type(method.return_type) is not tuple:
                method.return_type = convertType(method.return_type)
            if method.method_name in self.methods:
                self.methods[method.method_name].append(method)
            else:
                self.methods[method.method_name] = [method]

    def __map_fields_to_values(self):
        self.fields = {}
        for field in self.class_def.get_fields():
            created_val = create_value(field.default_field_value)
            created_field = create_variable(field.field_type, field.field_name)
            if created_field.type() != created_val.type(): #TODO(nn): need to deal with classes and null
                self.interpreter.error(
                ErrorType.TYPE_ERROR,
                "invalid type assigned to "+created_field.name(),
                )
            self.fields[created_field.name()] = [created_val,created_field.class_name()]
            
    def __initialize_parent(self):
        bloodline = self.class_def.get_blood_line()
        if len(bloodline) > 1:
            self.super = self.interpreter.instantiate(bloodline[1], None)
        else:
            self.super = None
            
    def __initialize_blood_line(self):
        self.blood_line = self.class_def.get_blood_line()
        
    def get_blood_line(self):
        return self.blood_line
        
            
        

    def __create_map_of_operations_to_lambdas(self):
        self.binary_op_list = [
            "+",
            "-",
            "*",
            "/",
            "%",
            "==",
            "!=",
            "<",
            "<=",
            ">",
            ">=",
            "&",
            "|",
        ]
        self.unary_op_list = ["!"]
        self.binary_ops = {}
        self.binary_ops[Type.INT] = {
            "+": lambda a, b: Value(Type.INT, a.value() + b.value()),
            "-": lambda a, b: Value(Type.INT, a.value() - b.value()),
            "*": lambda a, b: Value(Type.INT, a.value() * b.value()),
            "/": lambda a, b: Value(
                Type.INT, a.value() // b.value()
            ),  # // for integer ops
            "%": lambda a, b: Value(Type.INT, a.value() % b.value()),
            "==": lambda a, b: Value(Type.BOOL, a.value() == b.value()),
            "!=": lambda a, b: Value(Type.BOOL, a.value() != b.value()),
            ">": lambda a, b: Value(Type.BOOL, a.value() > b.value()),
            "<": lambda a, b: Value(Type.BOOL, a.value() < b.value()),
            ">=": lambda a, b: Value(Type.BOOL, a.value() >= b.value()),
            "<=": lambda a, b: Value(Type.BOOL, a.value() <= b.value()),
        }
        self.binary_ops[Type.STRING] = {
            "+": lambda a, b: Value(Type.STRING, a.value() + b.value()),
            "==": lambda a, b: Value(Type.BOOL, a.value() == b.value()),
            "!=": lambda a, b: Value(Type.BOOL, a.value() != b.value()),
            ">": lambda a, b: Value(Type.BOOL, a.value() > b.value()),
            "<": lambda a, b: Value(Type.BOOL, a.value() < b.value()),
            ">=": lambda a, b: Value(Type.BOOL, a.value() >= b.value()),
            "<=": lambda a, b: Value(Type.BOOL, a.value() <= b.value()),
        }
        self.binary_ops[Type.BOOL] = {
            "&": lambda a, b: Value(Type.BOOL, a.value() and b.value()),
            "|": lambda a, b: Value(Type.BOOL, a.value() or b.value()),
            "==": lambda a, b: Value(Type.BOOL, a.value() == b.value()),
            "!=": lambda a, b: Value(Type.BOOL, a.value() != b.value()),
        }
        self.binary_ops[Type.CLASS] = {
            "==": lambda a, b: Value(Type.BOOL, a.value() == b.value()),
            "!=": lambda a, b: Value(Type.BOOL, a.value() != b.value()),
        }

        self.unary_ops = {}
        self.unary_ops[Type.BOOL] = {
            "!": lambda a: Value(Type.BOOL, not a.value()),
        }
