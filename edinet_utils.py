
def deep_union(a, b):
    import sys

    if not isinstance(a, dict):
        #print(TypeError('Error: {0} is not dict'.format(a)))
        return
    if not isinstance(b, dict):
        #print(TypeError('Error: {0} is not dict'.format(b)))
        return

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
