class _Node:
    def __init__(self, key, value):
        self.key, self.value = key, value
        self.left = self.right = None


class BST:
    def __init__(self):
        self.root = None
        self.size = 0

    def insert(self, key, value):
        node = _Node(key, value)
        self.size += 1
        if self.root is None:
            self.root = node
            return
        cur = self.root
        while True:
            if key < cur.key:
                if cur.left is None:
                    cur.left = node
                    return
                cur = cur.left
            else:
                if cur.right is None:
                    cur.right = node
                    return
                cur = cur.right

    def search(self, key):
        cur = self.root
        while cur:
            if key == cur.key:
                return cur.value
            cur = cur.left if key < cur.key else cur.right
        return None

    def delete(self, key):
        parent, node = None, self.root
        while node and node.key != key:
            parent = node
            node = node.left if key < node.key else node.right
        if node is None:
            return False
        if node.left and node.right:  
            sp, succ = node, node.right
            while succ.left:
                sp, succ = succ, succ.left
            node.key, node.value = succ.key, succ.value
            parent, node = sp, succ
        child = node.left or node.right
        if parent is None:
            self.root = child
        elif parent.left is node:
            parent.left = child
        else:
            parent.right = child
        self.size -= 1
        return True

    def range_query(self, low, high):
        result, stack, node = [], [], self.root
        while stack or node:
            if node:
                stack.append(node)
                node = node.left if node.key[0] >= low else None  
            else:
                node = stack.pop()
                if node.key[0] > high:
                    break  
                if node.key[0] >= low:
                    result.append(node.value)
                node = node.right
        return result

    def height(self):
        if not self.root:
            return 0
        best, stack = 0, [(self.root, 1)]
        while stack:
            node, depth = stack.pop()
            best = max(best, depth)
            if node.left:
                stack.append((node.left, depth + 1))
            if node.right:
                stack.append((node.right, depth + 1))
        return best
