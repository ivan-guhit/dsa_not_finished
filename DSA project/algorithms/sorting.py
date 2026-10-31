

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


def quick_sort(items, key=lambda x: x, reverse=False):
    arr = [(key(x), x) for x in items]
    _quick_sort(arr, 0, len(arr) - 1)
    out = [x for _, x in arr]
    if reverse:
        out.reverse()
    return out


def _quick_sort(a, lo, hi):
    while lo < hi:
        x, y, z = a[lo][0], a[(lo + hi) // 2][0], a[hi][0]  
        if (x <= y <= z) or (z <= y <= x):
            pivot = y
        elif (y <= x <= z) or (z <= x <= y):
            pivot = x
        else:
            pivot = z
        lt, i, gt = lo, lo, hi  
        while i <= gt:
            k = a[i][0]
            if k < pivot:
                a[lt], a[i] = a[i], a[lt]
                lt += 1
                i += 1
            elif k > pivot:
                a[i], a[gt] = a[gt], a[i]
                gt -= 1
            else:
                i += 1
        if lt - lo < hi - gt:  
            _quick_sort(a, lo, lt - 1)
            lo = gt + 1
        else:
            _quick_sort(a, gt + 1, hi)
            hi = lt - 1
