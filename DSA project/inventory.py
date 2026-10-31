import threading
import time
from datetime import date, datetime

import database
from algorithms.searching import binary_search_prefix, linear_search
from algorithms.sorting import merge_sort, quick_sort
from ds.bst import BST
from ds.hash_table import HashTable
from ds.min_heap import MinHeap
from ds.stack import Stack


class StoreError(Exception):
    status = 400


class NotFoundError(StoreError):
    status = 404


class DuplicateError(StoreError):
    status = 409


SORT_KEYS = {
    "name": lambda p: p["name"].lower(),
    "price": lambda p: p["price"],
    "quantity": lambda p: p["quantity"],
    "expiry": lambda p: p["expiry"] or "9999-12-31",  
}


def decorate(p):

    out = dict(p)
    if p["expiry"]:
        days = (date.fromisoformat(p["expiry"]) - date.today()).days
        out["days_left"] = days
        out["status"] = "expired" if days < 0 else "soon" if days <= 7 else "ok"
    else:
        out["days_left"], out["status"] = None, "none"
    return out


class InventoryStore:
    def __init__(self):
        self.lock = threading.RLock()
        self.table, self.heap, self.bst = HashTable(), MinHeap(), BST()
        self.sales = Stack()
        self._by_name = None  


    def load(self):
        rows = database.fetch_all()
        with self.lock:
            self.table, self.bst = HashTable(), BST()
            for r in rows:
                self.table.put(r["sku"], r)
                self.bst.insert((r["price"], r["sku"]), r["sku"])
            self._refresh()
            self.sales = Stack()
            for sale in database.fetch_sales():  
                self.sales.push(sale)

    def _refresh(self):
        self.heap = MinHeap([(p["expiry"], p["sku"]) for p in self.table.values() if p["expiry"]])
        self._by_name = None


    def get(self, sku):
        with self.lock:
            p = self.table.get(sku)
            if p is None:
                raise NotFoundError(f"No product with SKU {sku}.")
            return decorate(p)

    def add(self, data):
        with self.lock:
            if self.table.contains(data["sku"]):
                raise DuplicateError(f"SKU {data['sku']} already exists.")
            database.insert(data)
            self.table.put(data["sku"], data)
            self.bst.insert((data["price"], data["sku"]), data["sku"])
            self._refresh()
            return decorate(data)

    def update(self, sku, fields):
        with self.lock:
            old = self.table.get(sku)
            if old is None:
                raise NotFoundError(f"No product with SKU {sku}.")
            new = {**old, **fields, "sku": sku}
            database.update(new)
            self.bst.delete((old["price"], sku))
            self.bst.insert((new["price"], sku), sku)
            self.table.put(sku, new)
            self._refresh()
            return decorate(new)

    def remove(self, sku):
        with self.lock:
            old = self.table.get(sku)
            if old is None:
                raise NotFoundError(f"No product with SKU {sku}.")
            database.delete(sku)
            self.table.delete(sku)
            self.bst.delete((old["price"], sku))
            self._refresh()


    def sell(self, sku, qty):
        with self.lock:
            p = self.table.get(sku)
            if p is None:
                raise NotFoundError(f"No product with SKU {sku}.")
            if qty > p["quantity"]:
                raise StoreError(f"Only {p['quantity']} in stock; cannot sell {qty}.")
            new_qty = p["quantity"] - qty
            sale = {
                "sku": sku, "name": p["name"], "quantity": qty, "unit_price": p["price"],
                "total": round(p["price"] * qty, 2),
                "sold_at": datetime.now().isoformat(timespec="seconds"),
            }
            sale["id"] = database.record_sale(sku, new_qty, sale) 
            product = {**p, "quantity": new_qty}
            self.table.put(sku, product)  
            self._by_name = None
            self.sales.push(sale)
            return {"product": decorate(product), "sale": sale}

    def undo_last_sale(self):
        with self.lock:
            sale = self.sales.peek()
            if sale is None:
                raise StoreError("There are no sales to undo.")
            p = self.table.get(sale["sku"])
            new_qty = p["quantity"] + sale["quantity"] if p else None
            database.void_sale(sale["id"], sale["sku"], new_qty)
            self.sales.pop()
            if p:
                self.table.put(p["sku"], {**p, "quantity": new_qty})
                self._by_name = None
            return {"sale": sale, "restored": p is not None}

    def recent_sales(self, limit):
        with self.lock:
            return self.sales.top_items(limit)

    def sales_report(self):

        with self.lock:
            sales = self.sales.top_items()
            by_product, by_day = HashTable(), HashTable()
            units, revenue = 0, 0.0
            for s in sales:
                units += s["quantity"]
                revenue += s["total"]
                row = by_product.get(s["sku"])
                if row is None:
                    row = {"sku": s["sku"], "name": s["name"], "units": 0, "revenue": 0.0}
                    by_product.put(s["sku"], row)
                row["units"] += s["quantity"]
                row["revenue"] = round(row["revenue"] + s["total"], 2)
                day = s["sold_at"][:10]
                drow = by_day.get(day)
                if drow is None:
                    drow = {"day": day, "sales": 0, "revenue": 0.0}
                    by_day.put(day, drow)
                drow["sales"] += 1
                drow["revenue"] = round(drow["revenue"] + s["total"], 2)
            best = merge_sort(by_product.values(), key=lambda r: r["revenue"], reverse=True)
            days = merge_sort(by_day.values(), key=lambda r: r["day"], reverse=True)
            return {"count": len(sales), "units": units, "revenue": round(revenue, 2),
                    "best_sellers": best[:5], "by_day": days[:7]}

    def sorted_list(self, sort_by, order, algo):
        with self.lock:
            items = self.table.values()
            sorter = merge_sort if algo == "merge" else quick_sort
            start = time.perf_counter()
            result = sorter(items, SORT_KEYS[sort_by], reverse=(order == "desc"))
            ms = round((time.perf_counter() - start) * 1000, 3)
            return {"items": [decorate(p) for p in result], "algorithm": f"{algo} sort", "ms": ms}

    def search(self, q, mode):
        with self.lock:
            if mode == "linear":
                found, steps = linear_search(self.table.values(), q, ("name", "category", "sku"))
                label = "linear search (name / category / SKU contains)"
            else:
                if self._by_name is None:
                    self._by_name = merge_sort(self.table.values(), SORT_KEYS["name"])
                found, steps = binary_search_prefix(self._by_name, q, SORT_KEYS["name"])
                label = "binary search (name starts with)"
            return {"items": [decorate(p) for p in found], "algorithm": label, "steps": steps}


    def expiring(self, limit):
        with self.lock:
            pairs = self.heap.smallest_k(limit)
            return [decorate(self.table.get(sku)) for _, sku in pairs]


    def price_range(self, low, high):
        if low > high:
            raise StoreError("Minimum price cannot be higher than maximum price.")
        with self.lock:
            skus = self.bst.range_query(low, high)
            return [decorate(self.table.get(s)) for s in skus]


    def structures(self):
        with self.lock:
            h = self.table.stats()
            return {
                "hash_table": {k: h[k] for k in ("capacity", "size", "load_factor", "longest_chain")},
                "bucket_lengths": h["bucket_lengths"],
                "heap": {"size": len(self.heap), "top": self.heap.data[:8]},
                "stack": {"size": len(self.sales), "top": self.sales.peek()},
                "bst": {"size": self.bst.size, "height": self.bst.height(),
                        "root": list(self.bst.root.key) if self.bst.root else None},
            }


store = InventoryStore()
