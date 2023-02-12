
def deep_union(a, b):
    if not isinstance(a, dict):
        TypeError("a is not dict") 
    if not isinstance(b, dict):
        TypeError("b is not dict") 

    if a == b:
        return a

    if len(a.keys()) < len(a.keys()):
        a, b = b, a
        
    for key in b.keys():
        if key in a.keys():
            a[key] = deep_union(a[key], b[key])
        else:
            a[key] = b[key]

    return a
