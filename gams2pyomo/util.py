def get_path(obj, path):
    keys = path.split('.')
    for k in keys:
        try:
            obj = obj[k]
        except KeyError:
            return None
    return obj


def set_path(obj, path, value):
    keys = path.split('.')
    for k in keys[:-1]:
        if k not in obj.keys():
            obj[k] = {}
        obj = obj[k]
    obj[keys[-1]] = value


def scrub_meta(obj, bad=["_meta", "meta"]):
    if isinstance(obj, dict):
        for k in obj.keys():
            if k in bad:
                del obj[k]
            else:
                scrub_meta(obj[k], bad)
    elif isinstance(obj, list):
        for i in reversed(range(len(obj))):
            if obj[i] in bad:
                del obj[i]
            else:
                scrub_meta(obj[i], bad)

    else:
        # neither a dict nor a list, do nothing
        pass

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