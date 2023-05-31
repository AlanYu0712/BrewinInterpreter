# Project 2 additional testcases

Project 2 has had a slew of clarifications and conditions that the autograder has overlooked. 
The canonical solutions are guaranteed to pass all of these.

Making these testcases run have the potential to help you with project 3 if you are working off of your own project 2 implementation. 
They are currently run as part of the command `python3 tester.py 2`. Please go in and edit the `tester.py` file if you'd like to exclude them.

In the folders named **tests/more_tests** and **fails/more_fails**, you will find additional testcases that deal with the
following clarifications/issues: 

### more_tests/test_super_me
Clarification: super and me behave correctly
The super keyword is similar to the explicit base:: call in C++, so it is always relative to the class in which the method uses the super keyword, to refer to the parent class.
The me keyword is similar to the self keyword in C++, so it should depend on the actual object being pointed to (irrespective of polymorphism). 

### more_tests/test_1b_return_me , more_tests/test_cmpwr552
Fix: `return me` in the context of object reference returns was lacking in testing (Campuswire post #552). (1b testcase comes from a question about when we would want to return me, and it can be to save a line of object mutation in main.)

### more_fails/test_base_super
Undefined behaviour: super keyword called by a method in a class with no parent ancestor class
This should return a TYPE_ERROR, as barista correctly does but since the spec did not require it, you will not be penalised for not checking for this in project 2.

### more_fails/test_cmpr445
Fix: having the situation of returning null for a method of non-object-reference type return a TYPE_ERROR.

### more_fails/test_cmpr450
Fix: having type incompatibility of two unrelated object references hold (returning a TYPE_ERROR) even when the reference is null. 