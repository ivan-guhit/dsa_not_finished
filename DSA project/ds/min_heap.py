
class MinHeap:
    def __init__(self, items=None):
        self.data = list(items) if items else []
        for i in range(len(self.data) // 2 - 1, -1, -1):  
            self._sift_down(i)

    def __len__(self):
        return len(self.data)

    def peek(self):
        return self.data[0] if self.data else None

    def push(self, item):
        self.data.append(item)
        self._sift_up(len(self.data) - 1)

    def pop(self):
        if not self.data:
            return None
        top = self.data[0]
        last = self.data.pop()
        if self.data:
            self.data[0] = last
            self._sift_down(0)
        return top

    def smallest_k(self, k):
        clone = MinHeap()
        clone.data = self.data[:]
        out = []
        for _ in range(min(k, len(clone))):
            out.append(clone.pop())
        return out

    def _sift_up(self, i):
        while i > 0:
            parent = (i - 1) // 2
            if self.data[i] < self.data[parent]:
                self.data[i], self.data[parent] = self.data[parent], self.data[i]
                i = parent
            else:
                break

    def _sift_down(self, i):
        n = len(self.data)
        while True:
            left, right, smallest = 2 * i + 1, 2 * i + 2, i
            if left < n and self.data[left] < self.data[smallest]:
                smallest = left
            if right < n and self.data[right] < self.data[smallest]:
                smallest = right
            if smallest == i:
                break
            self.data[i], self.data[smallest] = self.data[smallest], self.data[i]
            i = smallest
