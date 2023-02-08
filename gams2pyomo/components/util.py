import numpy as np

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


def gams_arange(start, stop, step=1):
    """
    Generate a list from the for loop condition in GAMS.
    """

    res = list(np.arange(start, stop, step))

    if res[-1] + step == stop:
        res.append(stop)

    return res