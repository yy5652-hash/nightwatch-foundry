"""Own bounded nested input generator; client settings never configure service."""
import sys
from semantic_oracle import Number,encode,same

DEPTHS=[32,999,1100,1101]
SHAPES=["objects","arrays","alternating"]

def configure_client():
    # This is the separate evidence interpreter only. No source process shares
    # it, and no service limit/stack/network setting is changed.
    sys.setrecursionlimit(20000)

def leaf(variant="original"):
    value=dict(n=Number("0.100000000000000005"),zero=Number("-0.0"),order=[Number("1.0"),True,"1"],text='brackets:[{}] quote:" slash:\\ é汉')
    if variant=="alias":
        value.update(n=Number("100000000000000005e-18"),zero=Number("0e9999"),order=[Number("1e0"),True,"1"])
        value=dict(reversed(list(value.items())))
    elif variant=="number-difference":value["n"]=Number("0.1")
    elif variant=="type-difference":value["order"][0]=True
    return value

def object_level(shape,index):return shape=="objects" or shape=="alternating" and index%2==0

def tree(shape,depth,variant="original"):
    value=leaf(variant)
    for index in reversed(range(depth)):
        value={"next":value} if object_level(shape,index) else [value]
    return value

def raw(shape,depth,variant="original"):
    # Build wrappers independently of the object-tree encoder. Only the small
    # ordinary leaf uses the verifier's existing exact JSON token encoder.
    opens=[];closes=[]
    for index in range(depth):
        opens.append('{"next":' if object_level(shape,index) else '[')
        closes.append('}' if object_level(shape,index) else ']')
    return ''.join(opens)+encode(leaf(variant))+''.join(reversed(closes))

def inspect_generated(value,shape,depth,variant="original"):
    current=value
    for index in range(depth):
        if object_level(shape,index):
            if not isinstance(current,dict) or set(current)!={"next"}:return False
            current=current["next"]
        else:
            if not isinstance(current,list) or len(current)!=1:return False
            current=current[0]
    return same(current,leaf(variant))

def max_container_depth(value):
    maximum=0;stack=[(value,0)]
    while stack:
        node,level=stack.pop()
        if isinstance(node,(dict,list)):
            level+=1;maximum=max(maximum,level)
            stack.extend((child,level) for child in (node.values() if isinstance(node,dict) else node))
    return maximum
