from intbase import *
from bparser import BParser     # imports BParser class from bparser.py

#TODO: switch all to constants

class Interpreter(InterpreterBase):
    def __init__(self,console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase’s constructor
        self.classes = {}
        
    
    def run(self, program):
        # parse the program into a more easily processed form
        result, parsed_program = BParser.parse(program)
        if result == False:
            return 0 # error
        self.__discover_all_classes_and_track_them(parsed_program)
        class_def = self.__find_definition_for_class(InterpreterBase.MAIN_CLASS_DEF)
        obj = class_def.instantiate_object() 
        obj.run_method(InterpreterBase.MAIN_FUNC_DEF)
        
    def __discover_all_classes_and_track_them(self, parsed_program):
        for c in parsed_program:
            if c[1] in self.classes.keys():
                super().error(ErrorType.TYPE_ERROR) #TODO: LINE NUM
            self.classes[c[1]] = ClassDefinition(c,super())#TODO: return a ClassDef type
        
        #enable all classes to be public to one another
        for c in self.classes.values():
            c.gain_class_view(self.classes)
    
    def __find_definition_for_class(self,name):
        return self.classes[name]
    
    def interpret_statement(self, statement, line_num):
 	    print(f"{line_num}: {statement}")
	    # your code to interpret the passed-in statement
        #if cant_find_variable(v):
            #super().error(ErrorType.NAME_ERROR,f"Unknown variable {v}", line_number)


class ClassDefinition:
  # constructor for a ClassDefinition
    def __init__(self,recipe,intbase):
        self.intbase = intbase
        self.my_methods = self.__extract_methods(recipe) #returns a list
        self.my_fields = self.__extract_fields(recipe) #retunrs a dictionary
        self.all_classes = {}


# uses the definition of a class to create and return an instance of it
    def instantiate_object(self): 
        obj = ObjectDefinition(self.all_classes,self.intbase)
        for method in self.my_methods:
            obj.add_method(method)
        for field in self.my_fields:
            obj.add_field(field.name(), field.initial_value()) #have a class for this
        return obj  
    
    
    def __extract_methods(self,recipe):
        result = []
        for component in recipe[2:]:
            if component[0]==InterpreterBase.METHOD_DEF:
                m = MethodDefinition(component)
                for item in result:
                    if m.name() == item.name():
                        self.intbase.error(ErrorType.NAME_ERROR) #TODO: LINE NUM (I decide to raise an error here)
                result.append(m)
        if result==[]:
            ... #TODO:Dealing with no method in a class
        return result
        
    def __extract_fields(self,recipe):
        result = []
        for component in recipe[2:]: #the first two items in recipe MUST be 'class', 'main'
            if component[0]==InterpreterBase.FIELD_DEF: #make sure its field, not method
                f = FieldDefinition(component,self.intbase)
                for item in result:
                    if f.name() ==item.name(): #check for same name overlapping
                        self.intbase.error(ErrorType.NAME_ERROR) #TODO: LINE NUM
                result.append(f)
        return result
    
    def gain_class_view(self,view):
        self.all_classes = view 

class ObjectDefinition:
    def __init__(self,all_classes,intbase):
        self.methods = []
        self.fields = {}
        self.intbase = intbase
        self.all_classes=all_classes
        #TODO: Track objects initiated (deal with this with new)
    
    
    def add_method(self,method):
        self.methods.append(method)
    
    def add_field(self, name, val):
        self.fields[name] = val
    
    
    def run_method(self,method_name): #This is specifically foor calling main()
        method = self.__find_method(method_name)
        statement = method.get_top_level_statement()
        result = self.__run_statement(statement)
        return result
    
    
    def __find_method(self, method_name):
        #returns a method
        for m in self.methods:
            if m.name() == method_name:
                return m
        self.intbase.error(ErrorType.NAME_ERROR)
        
        

    #Expression
    #transforms an int, bool, null, variables to its value
    def transform_value(self,item):
        if item in self.fields.keys(): #is a variable
            return self.transform_value(self.fields[item])
        elif item==InterpreterBase.TRUE_DEF: #is true
            return True
        elif item==InterpreterBase.FALSE_DEF: #is true
            return False
        elif item==InterpreterBase.NULL_DEF: #is null
            return None
        elif not (type(item) is ObjectDefinition) and item[0]=='\"' and item[-1]=='\"': #is a string
            return item[1:-1]             
        elif not (type(item) is ObjectDefinition):#is int
            return int(item)
        else:
            return item
            
    
    
    #returns True if is an expression (specifically ones with parantheses)
    def __is_expression(self,item):
        return type(item)==list
    
    def __eval_expression(self,items):
        expression = [items[0]]
        if expression[0] ==InterpreterBase.CALL_DEF:
            return self.__execute_call_statement(items)
        elif expression[0] ==InterpreterBase.NEW_DEF:
            if items[1] not in self.all_classes.keys():
                self.intbase.error(ErrorType.TYPE_ERROR)
            class_def = self.all_classes[items[1]]
            return class_def.instantiate_object()
        else:
            for i in items [1:]:
                if self.__is_expression(i):
                    expression.append(self.__eval_expression(i))
                else:
                    expression.append(self.transform_value(i))
        
            e=ExpressionDefinition(self.intbase)
            return e.evaluate(expression)

    # runs/interprets the passed-in statement until completion and 
    # gets the result, if any
    #TODO: missing set statement
    def __run_statement(self, statement):
        if statement[0]==InterpreterBase.PRINT_DEF: #no return
            result = self.__execute_print_statement(statement)
        elif statement[0]==InterpreterBase.INPUT_INT_DEF or statement[0]==InterpreterBase.INPUT_STRING_DEF: #no return
            result = self.__execute_input_statement(statement)
        elif statement[0]==InterpreterBase.CALL_DEF: #has return, results from next__run_statement
            result = self.__execute_call_statement(statement)
        elif statement[0]==InterpreterBase.WHILE_DEF: #
            result = self.__execute_while_statement(statement)
        elif statement[0]==InterpreterBase.IF_DEF: #no return
            result = self.__execute_if_statement(statement)
        elif statement[0] ==InterpreterBase.SET_DEF:
            result = self.__execute_set_statement(statement)
        elif statement[0]==InterpreterBase.RETURN_DEF:
            result = self.__execute_return_statement(statement)
        elif statement[0]==InterpreterBase.BEGIN_DEF: #DONE
            result = self.__execute_all_sub_statements_of_begin_statement(statement) 
        return result #this ultimately returns whatever return returns

    #PRINT    
    def __execute_print_statement(self,statement):
        result = ""
        for i in statement[1:]: #concatenating all the items of the statement
            if self.__is_expression(i):
                i=self.__eval_expression(i)
            else:
                i = self.transform_value(i)  
                
            if type(i) is bool:
                if i:
                    result+=InterpreterBase.TRUE_DEF
                else:
                    result+=InterpreterBase.FALSE_DEF
            else:
                result+=str(i)
        
        self.intbase.output(result)
                
    #INPUTI/INPUTS
    def __execute_input_statement(self,statement):
        input = self.intbase.get_input()
        var = statement[1]
        if statement[0]==InterpreterBase.INPUT_INT_DEF:
            self.fields[var] = input
        else:
            self.fields[var]='\"'+input+'\"'
            

    # CALL   
    def __execute_call_statement(self, statement):
        obj = statement[1]
        method_name = statement[2]
        args = []
        if len(statement) > 3:        
            args = statement[3:] 
            #deal with args
            for i in range(len(args)):
                if self.__is_expression(args[i]):
                    args[i] = self.__eval_expression(args[i])
                else:
                    args[i] = self.transform_value(args[i])
        
        if obj == InterpreterBase.ME_DEF:
            method = self.__find_method(method_name)
            
            if len(args) != len(method.param()): #check right number of args
                self.intbase.error(ErrorType.TYPE_ERROR)
            #deal with params---adding them to fields and deleting them later
            #also consider shadowing
            record = {}
            for i in range(len(args)):
                if method.param()[i] in self.fields.keys():
                    record[method.param()[i]] = self.fields[method.param()[i]]
                self.fields[method.param()[i]] = str(args[i])          
            
            statement = method.get_top_level_statement()
            result = self.__run_statement(statement)
            #delete args in fields list
            for i in range(len(args)):
                del self.fields[method.param()[i]]
            #recover field list (from shadowing)
            self.fields = self.fields|record
            return result
        else:
            obj = self.transform_value(obj)
            
            if obj == None:
                self.intbase.error(ErrorType.FAULT_ERROR)
            method = obj.__find_method(method_name)
            
            
            # Same thing as me, just changing self to obj
            if len(args) != len(method.param()): #check right number of args
                obj.intbase.error(ErrorType.TYPE_ERROR)
            #deal with params---adding them to fields and deleting them later
            #also consider shadowing
            record = {}
            for i in range(len(args)):
                if method.param()[i] in obj.fields.keys():
                    record[method.param()[i]] = obj.fields[method.param()[i]]
                obj.fields[method.param()[i]] = str(args[i])          
            
            statement = method.get_top_level_statement()
            result = obj.__run_statement(statement)
            #delete args in fields list
            for i in range(len(args)):
                del obj.fields[method.param()[i]]
            #recover field list (from shadowing)
            obj.fields = obj.fields|record
            return result
            

    #WHILE
    def __execute_while_statement(self,statement):
        if self.__is_expression(statement[1]):
            determine = self.__eval_expression(statement[1])
        else:
            determine = self.transform_value(statement[1])
        
        if type(determine) is not bool:
            self.intbase.error(ErrorType.TYPE_ERROR)
        
        while(determine):
            result = self.__run_statement(statement[2])
            if result != None:
                if result =="":
                    return
                return result
            if self.__is_expression(statement[1]):
                determine = self.__eval_expression(statement[1])
            else:
                determine = self.transform_value(statement[1])
        
        

    #IF
    def __execute_if_statement(self,statement):
        if self.__is_expression(statement[1]):
            determine = self.__eval_expression(statement[1])
        else:
            determine = self.transform_value(statement[1])
        
        if type(determine) is not bool:
            self.intbase.error(ErrorType.TYPE_ERROR)
        
        if determine:
            result = self.__run_statement(statement[2])
        elif not determine and len(statement)>3:
            result =  self.__run_statement(statement[3])
        
        if result != None:
                if result =="":
                    return
                return result


    #SET
    def __execute_set_statement(self,statement):
        if statement[1] not in self.fields.keys():
            self.intbase.error(ErrorType.NAME_ERROR)
        
        if self.__is_expression(statement[2]):
            new_val = self.__eval_expression(statement[2])
        else:
            new_val = self.transform_value(statement[2])
            
        if type(new_val) is bool:
                if new_val:
                    self.fields[statement[1]]=InterpreterBase.TRUE_DEF
                else:
                    self.fields[statement[1]]=InterpreterBase.FALSE_DEF
        elif type(new_val) is ObjectDefinition:
            self.fields[statement[1]]=new_val
        elif type(new_val) is str:
            self.fields[statement[1]]='\"'+new_val+'\"'
        else:
            self.fields[statement[1]]=str(new_val)
        
    
    
    
    
    #RETURN
    def __execute_return_statement(self,statement):
        # if we have a value to return
        if len(statement) >1:
            if self.__is_expression(statement[1]):
                return self.__eval_expression(statement[1])
            else:
                return self.transform_value(statement[1])
        return ""

        

    #BEGIN
    def __execute_all_sub_statements_of_begin_statement(self,statement):
        for i in statement[1:]:
            result = self.__run_statement(i)
            if result != None:
                if result =="":
                    return
                return result
            
        
        
        
class FieldDefinition:
    
    def __init__(self,description,intbase):
        field_name =description[1]
        legal_initials = [chr(x) for x in range(ord('a'), ord('z') + 1)]+[chr(x) for x in range(ord('A'), ord('Z') + 1)]+['_']
        legal_rest = legal_initials+[str(x) for x in range(0,10)]
        self.intbase = intbase
        
        if not(field_name[0] in legal_initials and all(item in legal_rest for item in field_name)):
            self.intbase.error(ErrorType.NAME_ERROR) #TODO: LINE NUM (I decide to raise an error here)
        self.__name = field_name
        self.__initial_value = description[2]
        
    def name(self):
        return self.__name
    
    def initial_value(self):
        return self.__initial_value
        


class MethodDefinition:
    def __init__(self,description):
        self.__name = description[1]
        self.__param = description[2]
        self.__tp_statement = description[3]
    
    def name(self):
        return self.__name
    
    def param(self):
        return self.__param    
    
    def get_top_level_statement(self):
        return self.__tp_statement
    
    
    
class ExpressionDefinition:
    def __init__(self,intbase):
        self.intbase = intbase
    
    def evaluate(self,lst):
        operation = lst[0]
        fst_arg = lst[1]
        if len(lst)>2:
            snd_arg=lst[2]
            has_object = False
            for i in lst[1:]:
                if type(i) is ObjectDefinition:
                    has_object=True
            if (type(fst_arg) != type(snd_arg)) and (not has_object or None not in lst[1:]):
                self.intbase.error(ErrorType.TYPE_ERROR) #TODO: linenum
            if (has_object and None not in lst[1:]):
                self.intbase.error(ErrorType.TYPE_ERROR) #TODO: linenum

        if operation == '+':
            if (type(fst_arg) is int) or (type(fst_arg) is str):
                return fst_arg+snd_arg    
        elif operation =='-':
            if type(fst_arg) is int:
                return fst_arg-snd_arg
        elif operation=='*':
            if type(fst_arg) is int:
                return fst_arg*snd_arg
        elif operation=='/':
            if type(fst_arg) is int:
                return int(fst_arg/snd_arg)
        elif operation=='%':
            if type(fst_arg) is int:
                return fst_arg%snd_arg
        elif operation == '<':
            if (type(fst_arg) is int) or (type(fst_arg) is str):
                return fst_arg<snd_arg
        elif operation == '<=':
            if (type(fst_arg) is int) or (type(fst_arg) is str):
                return fst_arg<=snd_arg
        elif operation == '>':
            if (type(fst_arg) is int) or (type(fst_arg) is str):
                return fst_arg>snd_arg
        elif operation == '>=':
            if (type(fst_arg) is int) or (type(fst_arg) is str):
                return fst_arg>=snd_arg
        elif operation == '==':
            if (type(fst_arg) is int) or (type(fst_arg) is str) or (type(fst_arg) is bool) or (fst_arg==None) or (snd_arg==None):
                return fst_arg==snd_arg
        elif operation == '!=':
            if (type(fst_arg) is int) or (type(fst_arg) is str) or (type(fst_arg) is bool) or (fst_arg==None) or (snd_arg==None):
                return fst_arg!=snd_arg
        elif operation == '&':
            if (type(fst_arg) is bool):
                return fst_arg and snd_arg
        elif operation =='|':
            if (type(fst_arg) is bool):
                return fst_arg or snd_arg
        elif operation =='!':
            if(type(fst_arg) is bool):
                return not fst_arg   
        self.intbase.error(ErrorType.TYPE_ERROR) #TODO: linenum

    
def test():
    program_source = ['(class main',
                    '(field a "Josh Zhang")',
                    '(field b 3)',
                    '(field c null)',
                    ' (method main ()',
                    '   (begin',
                    '       (if (== 1 2)',
                    '           (print "hello " a "!" )',
                    '           (print (/ 3 5) " equal to 8 is " (== (- 5 3) 8))',
                    '       )',
                    '       (print (== (new main) null))',
                    '       (print (call me mult (+ 1 1) b))',
                    '       (print "hope you are still there, " a "!")',
                    '       (while (> b 6)',
                    '           (begin',
                    '               (print b)',
                    '               (set b (- b 1))))',
                    '       (print "c is null is " (== c null))',
                    '       (set c (new main))',
                    '       (print "c is null is " (== c null))',
                    '       (set b (call c mult 3 4))',
                    '       (print b)',
                    '   ) # end of begin',
                    ' ) # end of method',
                    ' (method mult (a b)',
                    '   (return (* a b))',
                    ' ) # end of mult',
                    ') # end of class']
    
    ps2 =   ['(class main',
            '(method fact (n)',
            '   (if (== n 1)',
            '       (return 1)',
            '       (return (* n (call me fact (- n 1))))',
            '   )',
            ')', #end of method fact
            '(method main () (print (call me fact 5)))',
            ')'] #end of class
    
    ps3 =   ['(class main',
            '(field x "abc")',
            '(method main ()',
            '   (begin',
            '       (set x "def")',
            '       (print x)',
            '       (set x 20)',
            '       (print x)',
            '       (set x true)',
            '(print x)',
            ')))' ]
    
    program_source1 = ['(class main',
                    '(field a "Josh Zhang")',
                    '(field b 3)',
                    '(field c null)',
                    ' (method main ()',
                    '   (begin',
                    '   (set c (new ))'
                    '   (print c)'
                    '   ) # end of begin',
                    ' ) # end of method',
                    ' (method mult (a b)',
                    '   (return (* a b))',
                    ' ) # end of mult',
                    '(method add (a b)',
                    '   (return (+ a b))',
                    ')'
                    ') # end of class']
    
    program_source2 = ['(class main',
                    '(field a "Josh Zhang")',
                    '(field b 3)',
                    '(field c null)',
                    ' (method main ()',
                    '   (begin',
                    '   (set c (call me mult b (call me add 1 3)))'
                    '   (print c)'
                    '   ) # end of begin',
                    ' ) # end of method',
                    ' (method mult (a b)',
                    '   (return (* a b))',
                    ' ) # end of mult',
                    '(method add (a b)',
                    '   (return (+ a b))',
                    ')'
                    ') # end of class']
    
    i = Interpreter()
    i.run(program_source)
    
test()