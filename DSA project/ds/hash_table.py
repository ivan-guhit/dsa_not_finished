
class HashTable:
    def __init__(self, capacity=16, max_load=0.75):
        self.capacity = capacity
        self.max_load = max_load
        self.size = 0
        self.buckets = [[] for _ in range(capacity)]

    def _hash(self, key):
        h = 5381
        for ch in str(key):
            h = (h * 33 + ord(ch)) & 0xFFFFFFFF
        return h % self.capacity

    def put(self, key, value):
        bucket = self.buckets[self._hash(key)]
        for pair in bucket:
            if pair[0] == key:
                pair[1] = value  
                return
        bucket.append([key, value])
        self.size += 1
        if self.size / self.capacity > self.max_load:
            self._resize()

    def get(self, key):
        for k, v in self.buckets[self._hash(key)]:
            if k == key:
                return v
        return None

    def contains(self, key):
        return self.get(key) is not None

    def delete(self, key):
        bucket = self.buckets[self._hash(key)]
        for i, pair in enumerate(bucket):
            if pair[0] == key:
                bucket.pop(i)
                self.size -= 1
                return True
        return False

    def values(self):
        return [pair[1] for bucket in self.buckets for pair in bucket]

    def _resize(self):
        old = self.buckets
        self.capacity *= 2
        self.buckets = [[] for _ in range(self.capacity)]
        self.size = 0
        for bucket in old:
            for k, v in bucket:
                self.put(k, v)

    def stats(self):
        lengths = [len(b) for b in self.buckets]
        return {
            "capacity": self.capacity,
            "size": self.size,
            "load_factor": round(self.size / self.capacity, 2),
            "longest_chain": max(lengths),
            "bucket_lengths": lengths,
        }
