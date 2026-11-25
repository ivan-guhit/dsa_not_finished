

def merge_sort(items, key=lambda x: x, reverse=False):
    result = _merge_sort([(key(x), x) for x in items])
    out = [x for _, x in result]
    if reverse:
        out.reverse()
    return out


def _merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left, right = _merge_sort(arr[:mid]), _merge_sort(arr[mid:])
    merged, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i][0] <= right[j][0]:  
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged

