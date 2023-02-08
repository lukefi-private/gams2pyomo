import numpy as np

NUMBER = '0123456789'

def sequence_set(idx1, idx2):
    """
    Generate a set as a sequence from idx1 to idx2.
    """

    # when index is int, directly return a range
    if isinstance(idx1, int):
        return list(range(idx1, idx2 + 1))

    # get the string prefix to see if it is string + int or pure string
    prefix = ''
    for i, c in enumerate(idx1):
        prefix = idx1[:i + 1]
        left = idx1[i + 1:]
        if all([c in NUMBER for c in left]):
            break

    # pure string, e.g., a * i
    if prefix == idx1:
        char = idx1
        res = []
        while char != idx2:
            res.append(char)
            char = chr(ord(char) + 1)
        res.append(idx2)
        return res

    # string + int, e.g., a1 * a10
    try:
        n1 = int(idx1.split(prefix)[1])
        n2 = int(idx2.split(prefix)[1])
        _set = range(n1, n2 + 1)
        return [prefix + str(i) for i in _set]
    except ValueError:
        return list(range(int(idx1), int(idx2) + 1))

def change_case(string):
    """Change string format into snake case."""

    return ''.join(['_'+i.lower() if i.isupper() else i for i in string]).lstrip('_')

