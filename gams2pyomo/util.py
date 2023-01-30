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

def find_alias(idx, container):

    # index is defined
    if isinstance(idx, int) or idx.upper() in container.set:
        return idx

    # index is alias to defined index
    for aliases in container.symbols['alias']:
        if idx in aliases:
            # if so, find the defined index
            for a in aliases:
                if a.upper() in container.set:
                    return a

    # a specific index in the set, return itself
    return idx

def change_case(string):
    """Change string format into snake case."""

    return ''.join(['_'+i.lower() if i.isupper() else i for i in string]).lstrip('_')


def gams_arange(start, stop, step=1):
    """
    Generate a list from the for loop condition in GAMS.
    """

    res = list(np.arange(start, stop, step))

    if res[-1] + step == stop:
        res.append(stop)

    return res
