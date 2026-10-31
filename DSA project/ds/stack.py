
class _Node:
    def __init__(self, value, below):
        self.value, self.below = value, below


class Stack:
    def __init__(self):
        self.top = None
        self.size = 0

    def __len__(self):
        return self.size

    def push(self, value):
        self.top = _Node(value, self.top)
        self.size += 1

    def pop(self):
        if self.top is None:
            return None
        value = self.top.value
        self.top = self.top.below
        self.size -= 1
        return value

    def peek(self):
        return self.top.value if self.top else None

    def top_items(self, limit=None):
        out, node = [], self.top
        while node and (limit is None or len(out) < limit):
            out.append(node.value)
            node = node.below
        return out
