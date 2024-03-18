
def deep_union(a, b):
    import sys

    if not isinstance(a, dict):
        return
    if not isinstance(b, dict):
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
