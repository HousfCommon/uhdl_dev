
#from .Value import Value
from uhdl_core.Variable import Input,Output,Value
from functools import reduce
from uhdl_core.Root      import Root





def assign(opl:Value,opr:Value):
    tmp = opl
    tmp += opr

def smart_assign(op1:Value,op2:Value,outer=False):
    if isinstance(op1,Input):
        if hasattr(op2,'father') and op1.father is op2.father and outer: assign(op1,op2)
        else:                                                            assign(op2,op1)
    elif isinstance(op2,Input):
        if hasattr(op1,'father') and op1.father is op2.father and outer: assign(op2,op1)
        else:                                                            assign(op1,op2)
    else:
        raise Exception()

def LCA(*node_list):
    tree_list = [x.ancestors() for x in node_list]
    common_path = list(reduce(lambda x,y:set(x)&set(y),tree_list))
    return None if not common_path else common_path[0]

def linkable(op1,op2):
    if isinstance(op1,Input) and not isinstance(op2,Input):
        return True
    elif isinstance(op2,Input) and not isinstance(op1,Input):
        return True
    else:
        return False

