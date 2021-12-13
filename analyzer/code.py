#!/usr/bin/env python3
# coding: utf-8

from parsing.Parse import parse_file
from parsing.Typechecker import typecheck
from parsing.Typechecker import Context
from parsing.Ast import Term, Var
import copy

class Node:
    def __init__(self):
        self.out = [] # data flow out
        self.ine = [] # data flow in

class SE:
    def __init__(self, glob):
        self.variables = []
        self.glob = glob
        self.partialOrderPairs = []
        self.sources = [] 
        self.symbolicValue = []
        self.graph = {} # a data flow graph
        self.sortedVariables = [] # sort the variables along with the data flow.
        self.variable2RValue = {} # map a variable name to its possible R values
        self.variable2Expr = {}
        self.variable2Flag = {}
        self.tmp = Var('tmp', 'A')
        
    def performSymbolicExecution(self):
        '''
        let's represent the values as in the form of parameters/arguments and constants.
        there will be unterpreted functions that belong the SMT solvers,
        we do not interprete them
        however, we will also resolve its arguments. 
        '''
        return
    
    def sortOperands(self, command):
        '''
        (= t_mescape_107 (Replace t_mescape_106 __cOnStStR__x1a __cOnStStR__x5c_x78_x31_x61))        
        '''
        
        if command.op == '=':
            # flow from first to second
            operand0 = command.subterms[0]
            operand1 = command.subterms[1]
            first = []
            second = []
            # operand0.find_all(operand1, variables0)
            self.find_all_var(operand0, first)
            self.find_all_var(operand1, second)
            
            if operand0.is_var:

                if operand1.is_var: 
                    # case: a == b
                    if operand0 in self.sources: # let's consider the source.
                        if str(operand1) not in self.variable2Expr.keys():
                            self.variable2Expr[str(operand1)] = []
                        self.variable2Expr[str(operand1)].append(operand0)
                        self.partialOrderPairs.append((first, second))
                        return
                if str(operand0) not in self.variable2Expr.keys():
                    self.variable2Expr[str(operand0)] = []
                self.variable2Expr[str(operand0)].append(operand1)
                self.partialOrderPairs.append((second, first))

            else:
                if operand1.is_var:
                    if str(operand1) not in self.variable2Expr.keys():
                        self.variable2Expr[str(operand1)] = []
                    self.variable2Expr[str(operand1)].append(operand0)
                    
                self.partialOrderPairs.append((first, second))
        else:
            print('sortOperands', command.op)
            
    def resolveGraph(self):
        doneVariables = [str(i) for i in self.sources]

        found = 0
        while True:
            for var in self.graph.keys():
                if var not in doneVariables:
                    if set(self.graph[var].ine).issubset(set(doneVariables)):
                        found = 1
                        doneVariables.append(var)
                        if var in self.variable2Expr.keys():
                            if var not in self.variable2RValue.keys():
                                self.variable2RValue[var] = []
                            for e in self.variable2Expr[var]:
                                print(456, e, var)
                                ecopy = copy.deepcopy(e)
                                tmp = self.substitute(ecopy)
                                try:
                                    print(123, tmp)
                                except:
                                    pass
                                #if str(tmp) not in [str(i) for i in self.variable2RValue[var] if i != None]:
                                if tmp is not None and tmp not in self.variable2RValue[var]:
                                    self.variable2RValue[var].extend(tmp)
                                #print(ecopy, var)
                        else:
                            print('....')
                        '''
                        can update variable values here?
                        '''
                        
            if found == 0:
                if set(self.graph.keys()).issubset(set(doneVariables)):
                    '''
                    finished.
                    '''
                    break
                else:
                    for var in self.graph.keys():
                        if var not in doneVariables:
                            doneVariables.append(var)
                            if var in self.variable2Expr.keys():
                                if var not in self.variable2RValue.keys():
                                    self.variable2RValue[var] = []
                            else:
                                self.variable2RValue[var] = Var(var, 'A')
                            break
            found = 0
        self.sortedVariables = doneVariables
    
        
    def createGraph(self):
        '''
        Let's create a data flow graph
        '''
        for (a, b) in self.partialOrderPairs: # func->var, a->b, data flow direction.
            for v0 in a:
                for v1 in b:
                    if str(v0) not in self.graph.keys():
                        self.graph[str(v0)] = Node()
                    if str(v1) not in self.graph.keys():
                        self.graph[str(v1)] = Node()
                    if str(v1) not in self.graph[str(v0)].out:
                        self.graph[str(v0)].out.append(str(v1))
                    if str(v0) not in self.graph[str(v1)].ine:
                        self.graph[str(v1)].ine.append(str(v0))
                    # print('== %s %s ==' % (v0, v1))
                    if str(v1) in self.graph[str(v0)].out and str(v1) in self.graph[str(v0)].ine:
                        print('dependnecy conflicts! %s %s ', (v0, v1))
    
    def find_all_equal(self, term, occs):
        '''
        Find all equal/assignments
        '''
        if term.subterms:
            for sub in term.subterms:
                self.find_all_equal(sub, occs)
        if term.op == '=':
            occs.append(term)
    
    def find_all_var(self, term, occs):
        """
        Find all (sub)terms in the type of Var
        """
        if term.is_var:
            if term not in occs:
                occs.append(term)
  
        if term.subterms:
            for sub in term.subterms:
                self.find_all_var(sub, occs)
                    

    def substitute(self, expr):
        '''
        suppose an expr has been deepcopied, let's then normalize it
        '''
        occs = []
        result = [expr]
        self.find_all_var(expr, occs)
        hasUnresolved = False
        for v in occs:
            if str(v) in self.variable2RValue.keys() and len(self.variable2RValue[str(v)]) > 0:
                count = len(self.variable2RValue[str(v)])
                results = [result]

                for i in range(count - 1):
                    results.append(copy.deepcopy(result))

                result = []
                for (i, val) in enumerate(self.variable2RValue[str(v)]):
                    for e in results[i]:
                        e.substitute(v, val)
                        result.append(e)
            else:
                hasUnresolved = True
                for e in result:
                    e.substitute(v, self.tmp)

        if hasUnresolved == False:
            self.symbolicValue.extend(result)

        return result

    def start(self, script):
        '''
        TL;DR: “lvalue” either means “expression which can be placed on the left-hand side of the assignment operator”, 
        or means “expression which has a memory address”. 
        “rvalue” is defined as “all other expressions”.
        refer to https://jameshfisher.com/2017/01/21/c-lvalue-rvalue/
  
        some scripts has partial order dependency. 
        let's sort the variables and resolve their symbolic values
        '''

        equalOperations = []
        
        for ass in script.assert_cmd:
            self.find_all_equal(ass.term, equalOperations)
            self.find_all_var(ass.term, self.variables)

        count = 0
        for var in self.variables:
            if '_POST_' in str(var):
                self.sources.append(var)
                self.variable2Expr[str(var)] = [var]
                arg = Var('$A' + str(count), 'A')
                count += 1
                self.variable2RValue[str(var)] = [arg]
        
        for e in equalOperations:
            self.sortOperands(e)
        
        self.createGraph()
        self.resolveGraph()
        print(len(self.symbolicValue))
        '''
        how to remove duplicate ones?
        '''
        '''
        for v in self.symbolicValue:
            print(v)
        '''

def SEmain(seed):
    sources = [] # given a list of arguments we try to reconstruct the data flow
    # we distinguish equal and comparsion operators.
    script, glob = parse_file(seed, silent=False)
    ctxt = Context(glob, {})

    typecheck(script, glob)

    Analyzer = SE(glob)
    Analyzer.start(script)
    return Analyzer
    
if __name__ == "__main__":
    seed = "mysql.smt"
    SEmain(seed)
