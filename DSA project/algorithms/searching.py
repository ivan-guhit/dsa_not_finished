

def linear_search(items, query, fields):
    q = query.lower()
    matches, steps = [], 0
    for item in items:
        steps += 1
        for f in fields:
            if q in str(item[f]).lower():  
                matches.append(item)
                break
    return matches, steps


def binary_search_prefix(sorted_items, prefix, key):

    prefix = prefix.lower()
    lo, hi, steps = 0, len(sorted_items), 0
    while lo < hi:  
        steps += 1
        mid = (lo + hi) // 2
        if key(sorted_items[mid]) < prefix:
            lo = mid + 1
        else:
            hi = mid
    matches = []
    while lo < len(sorted_items) and key(sorted_items[lo]).startswith(prefix):
        matches.append(sorted_items[lo])
        lo += 1
        steps += 1
    return matches, steps
