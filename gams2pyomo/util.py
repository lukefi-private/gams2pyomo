def sequence_set(idx1, idx2):
    if isinstance(idx1, int):
        return list(range(idx1, idx2 + 1))
    prefix = ''
    for i, c in enumerate(idx1):
        try:
            int(idx1[i:])
            prefix = idx1[:i]
            break
        except ValueError:
            pass

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

def change_case(str):
    # change str to snake case

    return ''.join(['_'+i.lower() if i.isupper() else i for i in str]).lstrip('_')
