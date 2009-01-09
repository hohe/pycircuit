# Copyright (c) 2008 Pycircuit Development Team
# See LICENSE for details.

""" Test circuit module
"""

from pycircuit.circuit.circuit import *
from pycircuit.circuit.symbolicanalysis import SymbolicAC
import sympy
import numpy as npy
from nose.tools import *

def generate_testcircuit():
    subc = SubCircuit()
    plus, minus = subc.add_nodes('plus', 'minus')
    subc['R1'] = R(plus, minus)

    subc['R3'] = R(plus, plus)

    class MySubC(SubCircuit):
        terminals = ['p', 'm']

        def __init__(self, *args, **kvargs):
            super(MySubC, self).__init__(*args, **kvargs)
            
            internal = self.add_node('internal')
            
            self['R1'] = R(self.nodenames['p'], internal)
            self['R2'] = R(internal, self.nodenames['m'])
            self['V1'] = VS(internal, gnd)
            self['R3'] = R(internal, gnd)

    subc['I1'] = MySubC(plus, minus)

    return subc

def test_subcircuit_nodes():
    """Test node consistency of hierarchical circuit"""
    
    subc = generate_testcircuit()

    ## Check nodes of subc
    assert_equal(set(subc.nodes), 
                 set([Node('plus'), Node('minus'), Node('I1.internal'), 
                      gnd]))

    ## Check local names of subc
    assert_equal(subc.nodenames,
                 {'plus': Node('plus'), 'minus': Node('minus'),
                  'I1.internal': Node('I1.internal'),
                  'gnd': gnd})

    ## Check branches of subc
    assert_equal(subc.branches,
                 [Branch(Node('I1.internal'), gnd)])

    ## Check local names of I1
    assert_equal(subc['I1'].nodenames,
                 {'p': Node('plus'), 'm': Node('minus'),
                  'internal': Node('internal'),
                  'gnd': gnd})

    ## Check branches of I1
    assert_equal(subc['I1'].branches,
                 [Branch(Node('internal'), gnd)])

    ## Check nodes of I1
    assert_equal(set(subc['I1'].nodes), 
                 set([Node('plus'), Node('minus'), Node('internal'), 
                      gnd]))

    ## Check that first nodes of I1 are terminal nodes 
    assert_equal(subc['I1'].nodes[0:2], [Node('plus'), Node('minus')])

    ## delete I1
    del subc['I1']
    
    ## Check nodes of subc
    assert_equal(set(subc.nodes), 
                 set([Node('plus'), Node('minus')]))

    ## Check local names of subc
    assert_equal(subc.nodenames,
                 {'plus': Node('plus'), 'minus': Node('minus')})
    

    ## Check nodes of R3
    assert_equal(subc['R3'].nodes,
                 [Node('plus')])

def test_add_nodes_implicitly():
    subc = SubCircuit()

    ## Test to add nodes implicitly using node objects
    subc['R1'] = R(Node('a'), Node('b'))
    
    ## Check nodes of subc
    assert_equal(set(subc.nodes), 
                 set([Node('a'), Node('b')]))

    ## Check local names of subc
    assert_equal(subc.nodenames,
                 {'a': Node('a'), 'b': Node('b') })

    ## Test to add nodes implicitly using strings
    subc['R2'] = R('a', 'c')
    subc['R3'] = R('b', 1)
    
    ## Check nodes of subc
    assert_equal(set(subc.nodes), 
                 set([Node('a'), Node('b'), Node('c'), Node('1')]))

    ## Check local names of subc
    assert_equal(subc.nodenames,
                 {'a': Node('a'), 'b': Node('b'), 'c': Node('c'), 
                  '1': Node('1')})
    
def create_current_divider(R1,R3,C2):
    cir = SubCircuit()

    n1,n2 = cir.add_nodes('n1', 'n2')
    
    class MySubC(SubCircuit):
        terminals = ['plus', 'minus']

        def __init__(self, *args, **kvargs):
            super(MySubC, self).__init__(*args, **kvargs)

            self['R3'] = R(self.nodenames['plus'], self.nodenames['minus'], r=R3)
            self['I2'] = IS(self.nodenames['plus'], self.nodenames['minus'], iac=1)


    cir['IS'] = IS(gnd,n1, iac=2)
    cir['R1'] = R(n1, n2, r=R1)
    cir['I1'] = MySubC(n2, gnd)
    cir['C2'] = C(n2, gnd, c=C2)
 
    return cir

def test_current_probing():
    """Test current probing with a current divider circuit"""
    
    s = sympy.Symbol('s')

    R1, R3, C2 = sympy.symbols('R1', 'R3', 'C2')

    cir = create_current_divider(R1,R3,C2)
    
    cir = cir.save_current('I1.plus')

    assert cir.get_terminal_branch('I1.plus') != None
    
    res = SymbolicAC(cir).solve(s, complexfreq=True)

    assert_equal(sympy.simplify(res.i('I1.plus')), (2 + C2*R3*s)/(1 + C2*R3*s))

    assert_equal(sympy.simplify(res.i('C2.plus')), s*R3*C2 / (1 + s*R3*C2))

def test_current_probing_wo_branch():
    """Test current probing with a current divider circuit without current probe"""

    s = sympy.Symbol('s')

    R1, C2, R3 = sympy.symbols('R1', 'C2', 'R3')

    cir = create_current_divider(R1,R3,C2)

    res = SymbolicAC(cir).solve(s, complexfreq=True)
    
    assert_equal(sympy.simplify(res.i('I1.plus')), (2 + C2*R3*s)/(1 + C2*R3*s))

    assert_equal(sympy.simplify(res.i('C2.plus')), s*R3*C2 / (1 + s*R3*C2))
            
def test_adddel_subcircuit_element():
    """add subcircuit element that contains a branch then delete it"""
    cir = SubCircuit()

    n1, = cir.add_nodes('n1')
    
    cir['R1'] = R(n1, gnd, r=1e3)
    
    cir['V'] = VS(n1, gnd)
    
    del cir['V']
    
    assert_equal(cir.elements.values(), [cir['R1']])
    assert_equal(cir.nodes, [n1,gnd])
    assert_equal(cir.branches, [])
